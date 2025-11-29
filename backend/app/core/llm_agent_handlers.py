"""
LLM Agent Handlers for different intents.

This module contains handler functions for each agent intent:
- Chat about the model
- Edit DSL code
- Edit parameters
- Generate Python scripts
"""

import json
from typing import Optional
from dataclasses import dataclass
from openai import OpenAI
from app.core.ir import Part, ValidationIssue, Sketch, SketchEntity, SketchConstraint, SketchDimension
from app.core.dsl_store import get_current_dsl, update_dsl, set_part
from app.core.edits import TextEdit, apply_text_edits_to_dsl
from app.core.analysis import validate_part, validate_sketch
from app.core.builder import build_cad_model, generate_mesh
from app.core.agent_intent import AgentIntent


@dataclass
class HandlerResult:
    """Result from a handler function."""
    part: Optional[Part] = None
    dsl: Optional[str] = None
    message: str = ""
    success: bool = True
    validation_issues: Optional[list[ValidationIssue]] = None
    script_code: Optional[str] = None  # For GENERATE_SCRIPT intent
    sketch: Optional[Sketch] = None  # For EDIT_SKETCH intent


def get_openai_client() -> OpenAI:
    """Get OpenAI client."""
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    return OpenAI(api_key=api_key)


def handle_chat_model(prompt: str, part: Part, part_summary: dict) -> HandlerResult:
    """
    Handle pure chat/explanation requests about the model.
    
    No code changes are made, only explanations are returned.
    
    Args:
        prompt: User's question/prompt
        part: Current Part IR
        part_summary: Compact summary of the part
        
    Returns:
        HandlerResult with message only (no part/dsl changes)
    """
    client = get_openai_client()
    
    system_prompt = """You are a CAD design assistant. Your role is to explain, answer questions, 
and provide insights about parametric CAD models.

IMPORTANT: Do NOT propose code changes unless the user explicitly asks for them.
Focus on explaining what the model does, why things are the way they are, and answering questions.

You see:
- A semantic tree of parameters, features, and chains
- Current parameter values and tolerances
- Validation issues (if any)
- Dimensional chain analysis results

Provide clear, helpful explanations without modifying anything."""

    # Build context message
    context_parts = [
        "Current part summary:",
        f"- Name: {part.name}",
        f"- Parameters: {len(part.params)}",
        f"- Features: {len(part.features)}",
        f"- Chains: {len(part.chains)}",
    ]
    
    if part.params:
        context_parts.append("\nParameters:")
        for name, param in part.params.items():
            tol_str = f" (tolerance: {param.tolerance_class})" if param.tolerance_class else ""
            context_parts.append(f"  {name} = {param.value} {param.unit}{tol_str}")
    
    if part.features:
        context_parts.append("\nFeatures:")
        for feature in part.features:
            params_str = ", ".join([f"{k}={v}" for k, v in feature.params.items()])
            context_parts.append(f"  {feature.name} ({feature.type}): {params_str}")
    
    # Get validation issues
    issues = validate_part(part)
    if issues:
        context_parts.append("\nValidation Issues:")
        for issue in issues:
            context_parts.append(f"  [{issue.severity.upper()}] {issue.message}")
    
    context_message = "\n".join(context_parts)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_message}\n\nUser question: {prompt}"}
            ],
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        
        return HandlerResult(
            part=None,  # No changes
            dsl=None,
            message=message,
            success=True
        )
    except Exception as e:
        return HandlerResult(
            message=f"Error during chat: {str(e)}",
            success=False
        )


def handle_edit_dsl(prompt: str, current_dsl: str, part: Part, max_attempts: int = 3) -> HandlerResult:
    """
    Handle DSL editing requests using text edits (Cursor-style).
    
    Args:
        prompt: User's edit request
        current_dsl: Current DSL text
        part: Current Part IR (for context)
        max_attempts: Maximum number of fix attempts if parsing fails
        
    Returns:
        HandlerResult with updated part, dsl, and message
    """
    client = get_openai_client()
    
    system_prompt = """You are a code editor assistant for a CAD DSL (Domain Specific Language).

Your task is to make minimal, precise text edits to the DSL code based on user requests.

You MUST respond with a call to apply_text_edits containing the exact text changes needed.

Rules:
- Make minimal changes - only edit what needs to change
- Preserve formatting and structure
- Ensure edits are syntactically correct
- If the user asks to change a value, find the exact location and replace it
- If adding features, add them in the correct location within the part definition

The DSL syntax:
- Parameters: `param name = value unit [tolerance class]`
- Features: `feature name = type(param1 = value1, param2 = value2)`
- Chains: `chain name { terms = [param1, param2] }`

Respond ONLY with a tool call to apply_text_edits."""

    # Show relevant context (first 2000 chars of DSL)
    dsl_preview = current_dsl[:2000]
    if len(current_dsl) > 2000:
        dsl_preview += "\n... (truncated)"
    
    user_message = f"""Current DSL code:

```
{dsl_preview}
```

User request: {prompt}

Make the necessary text edits to fulfill this request."""

    tools = [{
        "type": "function",
        "function": {
            "name": "apply_text_edits",
            "description": "Apply text edits to the DSL code",
            "parameters": {
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "integer", "description": "Start character offset"},
                                "end": {"type": "integer", "description": "End character offset (exclusive)"},
                                "replacement": {"type": "string", "description": "Text to insert"}
                            },
                            "required": ["start", "end", "replacement"]
                        }
                    }
                },
                "required": ["edits"]
            }
        }
    }]
    
    attempt = 0
    last_error = None
    last_dsl = current_dsl
    
    while attempt < max_attempts:
        try:
            # Call LLM for edits
            if attempt == 0:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            else:
                # Retry with error context
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": f"I attempted edits but got an error: {last_error}"},
                    {"role": "user", "content": f"Original DSL:\n```\n{current_dsl}\n```\n\nFailed DSL:\n```\n{last_dsl}\n```\n\nError: {last_error}\n\nPlease fix the error with corrected edits."}
                ]
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "apply_text_edits"}},
                temperature=0.3
            )
            
            message = response.choices[0].message
            
            if not message.tool_calls:
                return HandlerResult(
                    message="Error: LLM did not return text edits",
                    success=False
                )
            
            # Parse edits
            tool_call = message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            edits_json = arguments.get("edits", [])
            
            edits = [TextEdit(**edit) for edit in edits_json]
            
            # Apply edits
            new_dsl = apply_text_edits_to_dsl(current_dsl, edits)
            last_dsl = new_dsl
            
            # Try to update DSL (this validates and parses)
            try:
                updated_part, errors = update_dsl("current", new_dsl)
                
                # Get validation issues
                validation_issues = validate_part(updated_part)
                
                # Generate summary message
                change_summary = f"Applied {len(edits)} edit(s) to DSL"
                if errors:
                    change_summary += f" (with {len(errors)} error(s))"
                
                return HandlerResult(
                    part=updated_part,
                    dsl=new_dsl,
                    message=change_summary,
                    success=len(errors) == 0,
                    validation_issues=validation_issues
                )
                
            except ValueError as e:
                # Parsing/validation failed, try again
                last_error = str(e)
                attempt += 1
                if attempt >= max_attempts:
                    return HandlerResult(
                        message=f"Failed to apply edits after {max_attempts} attempts. Last error: {last_error}",
                        success=False
                    )
                continue
                
        except Exception as e:
            return HandlerResult(
                message=f"Error during DSL editing: {str(e)}",
                success=False
            )
    
    return HandlerResult(
        message=f"Failed after {max_attempts} attempts",
        success=False
    )


def handle_edit_params(prompt: str, part: Part) -> HandlerResult:
    """
    Handle parameter editing requests via operations.
    
    This is similar to the existing edit flow but focused on parameters.
    
    Args:
        prompt: User's edit request
        part: Current Part IR
        
    Returns:
        HandlerResult with updated part
    """
    # For now, delegate to the existing edit flow
    # In the future, this could be optimized for parameter-only changes
    from app.core.llm_agent import run_agent, AgentMode, AgentScope
    
    result = run_agent(
        mode=AgentMode.EDIT,
        scope=AgentScope(),
        part=part,
        user_prompt=prompt
    )
    
    if result.part:
        # Generate DSL from updated part
        from app.core.dsl_generator import ir_to_dsl
        dsl = ir_to_dsl(result.part)
        set_part(result.part, dsl)
        
        validation_issues = validate_part(result.part)
        
        return HandlerResult(
            part=result.part,
            dsl=dsl,
            message=result.message,
            success=True,
            validation_issues=validation_issues
        )
    else:
        return HandlerResult(
            message=result.message,
            success=False
        )


def handle_generate_script(prompt: str, part: Part) -> HandlerResult:
    """
    Handle script generation requests.
    
    For MVP, returns a suggested Python code snippet.
    
    Args:
        prompt: User's request for script generation
        part: Current Part IR (for context)
        
    Returns:
        HandlerResult with script_code
    """
    client = get_openai_client()
    
    system_prompt = """You are a Python code generator for CAD DSL pattern helpers.

Generate Python functions that create DSL code snippets for reusable patterns.

Function signature should be:
```python
def pattern_name_dsl(name: str, **params) -> str:
    \"\"\"
    Generate DSL code for a pattern.
    
    Args:
        name: Name for the part/feature
        **params: Pattern-specific parameters
        
    Returns:
        DSL code string
    \"\"\"
    # Implementation
```

The function should return a DSL code string that can be inserted into a part definition.

Example:
```python
def hole_grid_dsl(name: str, rows: int, cols: int, pitch: float, dia: float) -> str:
    lines = []
    for i in range(rows):
        for j in range(cols):
            x = j * pitch
            y = i * pitch
            lines.append(f'  feature {name}_hole_{i}_{j} = hole(dia = {dia}, x = {x}, y = {y})')
    return '\\n'.join(lines)
```

Generate clean, well-documented Python code."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User request: {prompt}\n\nGenerate a Python helper function for this pattern."}
            ],
            temperature=0.5
        )
        
        script_code = response.choices[0].message.content
        
        return HandlerResult(
            message="Generated Python helper function. Review and add to generators/pattern_generators.py",
            success=True,
            script_code=script_code
        )
    except Exception as e:
        return HandlerResult(
            message=f"Error generating script: {str(e)}",
            success=False
        )


def handle_edit_sketch(prompt: str, sketch: Sketch, selected_entity_ids: list[str] = None) -> HandlerResult:
    """
    Handle sketch editing requests using LLM to generate sketch operations.
    
    Args:
        prompt: User's edit request
        sketch: Current Sketch IR
        selected_entity_ids: IDs of selected entities (if any)
        
    Returns:
        HandlerResult with updated sketch
    """
    client = get_openai_client()
    
    system_prompt = """You are a sketch editing assistant for a 2D CAD sketch system.

Your task is to modify sketches by adding entities, constraints, and dimensions based on user requests.

You MUST respond with tool calls to modify the sketch. Available tools:
- add_line: Add a line entity
- add_circle: Add a circle entity
- add_rectangle: Add a rectangle entity
- add_constraint: Add a geometric constraint
- add_dimension: Add a dimension

Rules:
- Use meaningful entity IDs (e.g., L1, L2 for lines, C1 for circles)
- When adding constraints, reference existing entity IDs
- When adding dimensions, specify the dimension value and unit (typically mm)
- Preserve existing entities unless explicitly asked to modify/remove them

Respond ONLY with tool calls."""

    # Build sketch summary
    sketch_summary = f"""Current sketch '{sketch.name}' on plane '{sketch.plane}':
Entities: {len(sketch.entities)}
Constraints: {len(sketch.constraints)}
Dimensions: {len(sketch.dimensions)}

Entities:
"""
    for entity in sketch.entities:
        if entity.type == "line":
            sketch_summary += f"  {entity.id}: line from {entity.start} to {entity.end}\n"
        elif entity.type == "circle":
            sketch_summary += f"  {entity.id}: circle center {entity.center} radius {entity.radius}\n"
        elif entity.type == "rectangle":
            sketch_summary += f"  {entity.id}: rectangle from {entity.corner1} to {entity.corner2}\n"
    
    if sketch.constraints:
        sketch_summary += "\nConstraints:\n"
        for constraint in sketch.constraints:
            sketch_summary += f"  {constraint.id}: {constraint.type}({', '.join(constraint.entity_ids)})\n"
    
    if sketch.dimensions:
        sketch_summary += "\nDimensions:\n"
        for dim in sketch.dimensions:
            sketch_summary += f"  {dim.id}: {dim.type}({', '.join(dim.entity_ids)}) = {dim.value} {dim.unit}\n"
    
    if selected_entity_ids:
        sketch_summary += f"\nSelected entities: {', '.join(selected_entity_ids)}\n"
    
    user_message = f"""{sketch_summary}

User request: {prompt}

Modify the sketch according to the user's request."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "add_line",
                "description": "Add a line entity to the sketch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entity ID (e.g., L1, L2)"},
                        "start_x": {"type": "number", "description": "Start X coordinate"},
                        "start_y": {"type": "number", "description": "Start Y coordinate"},
                        "end_x": {"type": "number", "description": "End X coordinate"},
                        "end_y": {"type": "number", "description": "End Y coordinate"}
                    },
                    "required": ["id", "start_x", "start_y", "end_x", "end_y"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_circle",
                "description": "Add a circle entity to the sketch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entity ID (e.g., C1)"},
                        "center_x": {"type": "number", "description": "Center X coordinate"},
                        "center_y": {"type": "number", "description": "Center Y coordinate"},
                        "radius": {"type": "number", "description": "Radius"}
                    },
                    "required": ["id", "center_x", "center_y", "radius"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_rectangle",
                "description": "Add a rectangle entity to the sketch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Entity ID (e.g., R1)"},
                        "corner1_x": {"type": "number", "description": "First corner X"},
                        "corner1_y": {"type": "number", "description": "First corner Y"},
                        "corner2_x": {"type": "number", "description": "Second corner X"},
                        "corner2_y": {"type": "number", "description": "Second corner Y"}
                    },
                    "required": ["id", "corner1_x", "corner1_y", "corner2_x", "corner2_y"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_constraint",
                "description": "Add a geometric constraint",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["horizontal", "vertical", "equal_length", "perpendicular", "tangent", "concentric", "symmetric"],
                            "description": "Constraint type"
                        },
                        "entity_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Entity IDs involved in the constraint"
                        }
                    },
                    "required": ["type", "entity_ids"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_dimension",
                "description": "Add a dimension",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["length", "diameter"],  # MVP: Only length and diameter
                            "description": "Dimension type"
                        },
                        "entity_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Entity IDs (1 for length/diameter/radius, 2 for distance)"
                        },
                        "value": {"type": "number", "description": "Dimension value"},
                        "unit": {"type": "string", "description": "Unit (default: mm)", "default": "mm"}
                    },
                    "required": ["type", "entity_ids", "value"]
                }
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            tools=tools,
            temperature=0.3
        )
        
        message = response.choices[0].message
        
        if not message.tool_calls:
            return HandlerResult(
                message="Error: LLM did not return tool calls for sketch editing",
                success=False
            )
        
        # Apply operations to sketch
        updated_sketch = sketch.model_copy(deep=True)
        operations_summary = []
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name == "add_line":
                entity = SketchEntity(
                    id=arguments["id"],
                    type="line",
                    start=(arguments["start_x"], arguments["start_y"]),
                    end=(arguments["end_x"], arguments["end_y"])
                )
                updated_sketch.entities.append(entity)
                operations_summary.append(f"added line {arguments['id']}")
            
            elif function_name == "add_circle":
                entity = SketchEntity(
                    id=arguments["id"],
                    type="circle",
                    center=(arguments["center_x"], arguments["center_y"]),
                    radius=arguments["radius"]
                )
                updated_sketch.entities.append(entity)
                operations_summary.append(f"added circle {arguments['id']}")
            
            elif function_name == "add_rectangle":
                entity = SketchEntity(
                    id=arguments["id"],
                    type="rectangle",
                    corner1=(arguments["corner1_x"], arguments["corner1_y"]),
                    corner2=(arguments["corner2_x"], arguments["corner2_y"])
                )
                updated_sketch.entities.append(entity)
                operations_summary.append(f"added rectangle {arguments['id']}")
            
            elif function_name == "add_constraint":
                constraint_id = f"c_{len(updated_sketch.constraints) + 1}"
                constraint = SketchConstraint(
                    id=constraint_id,
                    type=arguments["type"],
                    entity_ids=arguments["entity_ids"]
                )
                updated_sketch.constraints.append(constraint)
                operations_summary.append(f"added {arguments['type']} constraint")
            
            elif function_name == "add_dimension":
                dim_id = f"d_{arguments['type']}_{len(updated_sketch.dimensions) + 1}"
                dimension = SketchDimension(
                    id=dim_id,
                    type=arguments["type"],
                    entity_ids=arguments["entity_ids"],
                    value=arguments["value"],
                    unit=arguments.get("unit", "mm")
                )
                updated_sketch.dimensions.append(dimension)
                operations_summary.append(f"added {arguments['type']} dimension = {arguments['value']} {arguments.get('unit', 'mm')}")
        
        # Validate updated sketch
        validation_issues = validate_sketch(updated_sketch)
        
        # Update the part's sketch (find the feature and update it)
        # For now, we'll return the sketch and let the caller handle part updates
        message_text = f"Applied sketch operations: {', '.join(operations_summary)}"
        if validation_issues:
            message_text += f" ({len(validation_issues)} validation issues)"
        
        return HandlerResult(
            part=None,  # Part update handled by caller
            dsl=None,
            message=message_text,
            success=True,
            validation_issues=validation_issues,
            sketch=updated_sketch
        )
        
    except Exception as e:
        return HandlerResult(
            message=f"Error during sketch editing: {str(e)}",
            success=False
        )

