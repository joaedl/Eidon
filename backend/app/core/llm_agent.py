"""
LLM Agent module for natural language interaction with CAD models.

This module integrates with OpenAI API to allow users to:
- Create new parts from natural language descriptions
- Edit existing parts via natural language commands
- Get explanations about parts and validation issues

The agent is constrained to only use well-defined operations, ensuring
that all modifications are safe and traceable.
"""

import os
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
# Look for .env in the project root (Eidos/)
# __file__ is backend/app/core/llm_agent.py
# So we go up 3 levels to backend/, then up 1 more to project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback: try loading from current directory or environment variables
    load_dotenv()
from app.core.ir import Part, Feature, Param, Chain
from app.core.operations import (
    Operation,
    SetParameterOperation,
    UpdateParameterToleranceOperation,
    AddFeatureOperation,
    UpdateFeatureOperation,
    apply_operations,
)
from app.core.builder import build_cad_model
from app.core.analysis import validate_part


class AgentMode(str, Enum):
    """Mode of operation for the LLM agent."""
    CREATE = "create"
    EDIT = "edit"
    EXPLAIN = "explain"


@dataclass
class AgentScope:
    """Scope for agent operations - limits what can be modified."""
    selected_feature_ids: list[str] = field(default_factory=list)
    selected_param_names: list[str] = field(default_factory=list)
    selected_chain_names: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from agent execution."""
    part: Optional[Part]  # New or updated part, or None in explain mode
    operations: list[Operation]  # Empty if mode is create or explain-only
    message: str  # Natural language summary from LLM


def get_openai_client() -> OpenAI:
    """Get OpenAI client, using API key from .env file or environment variable."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in a .env file in the project root "
            "or as an environment variable. See .env.example for reference."
        )
    return OpenAI(api_key=api_key)


def summarize_part(part: Part) -> str:
    """
    Create a compact text summary of a part for LLM context.
    
    Returns a human-readable summary suitable for including in prompts.
    """
    lines = [f"Part: {part.name}"]
    lines.append("\nParameters:")
    for param_name, param in part.params.items():
        tol_str = f" tolerance {param.tolerance_class}" if param.tolerance_class else ""
        lines.append(f"  {param_name} = {param.value} {param.unit}{tol_str}")
    
    lines.append("\nFeatures:")
    for feature in part.features:
        params_str = ", ".join([f"{k}={v}" for k, v in feature.params.items()])
        lines.append(f"  {feature.name} ({feature.type}): {params_str}")
    
    lines.append("\nChains:")
    for chain in part.chains:
        terms_str = ", ".join(chain.terms)
        target_str = ""
        if chain.target_value is not None:
            target_str = f" target={chain.target_value}"
        if chain.target_tolerance is not None:
            target_str += f" ±{chain.target_tolerance}"
        lines.append(f"  {chain.name}: [{terms_str}]{target_str}")
    
    return "\n".join(lines)


def build_system_prompt(mode: AgentMode, scope: AgentScope, part: Optional[Part]) -> str:
    """
    Build the system prompt for the LLM based on mode and context.
    """
    prompt_parts = [
        "You are an AI assistant for a parametric CAD system. Your role is to help users",
        "create and modify 3D parts using natural language commands.",
        "",
        "The CAD system uses a semantic representation with:",
        "- Parameters: named values with units (e.g., 'dia = 20 mm') and optional tolerance classes",
        "- Features: geometric elements (cylinder, hole, chamfer, joint_interface, link_body, pocket, fillet)",
        "- Chains: dimensional chains for tolerance analysis",
        "",
    ]
    
    if mode == AgentMode.CREATE:
        prompt_parts.extend([
            "MODE: CREATE NEW PART",
            "You must create a complete new part from scratch based on the user's description.",
            "Use the create_new_part tool to generate a full Part specification.",
            "",
            "Guidelines:",
            "- Include all necessary parameters with appropriate units (typically 'mm')",
            "- Create features that make sense for the described part",
            "- Use meaningful parameter and feature names",
            "- Consider adding tolerance classes where appropriate (e.g., 'g6', 'H7')",
        ])
    elif mode == AgentMode.EDIT:
        prompt_parts.extend([
            "MODE: EDIT EXISTING PART",
            "You must modify the existing part based on the user's request.",
            "Use the propose_operations tool to specify what changes to make.",
            "",
            "Available operations:",
            "- set_parameter: Change a parameter's value",
            "- update_parameter_tolerance: Change a parameter's tolerance class",
            "- add_feature: Add a new geometric feature",
            "- update_feature: Update parameters of an existing feature",
            "",
        ])
        
        if scope.selected_feature_ids or scope.selected_param_names:
            prompt_parts.append("SCOPE RESTRICTION:")
            if scope.selected_feature_ids:
                prompt_parts.append(f"  - Only modify features: {', '.join(scope.selected_feature_ids)}")
            if scope.selected_param_names:
                prompt_parts.append(f"  - Only modify parameters: {', '.join(scope.selected_param_names)}")
            prompt_parts.append("  - Do NOT modify anything outside this scope unless absolutely necessary.")
            prompt_parts.append("")
        else:
            prompt_parts.append("SCOPE: Full part (you can modify any parameter or feature)")
            prompt_parts.append("")
    else:  # EXPLAIN
        prompt_parts.extend([
            "MODE: EXPLAIN",
            "You must provide explanations about the part without modifying it.",
            "Use the explain_model tool to return your explanation.",
            "",
            "You can explain:",
            "- The structure and purpose of the part",
            "- Parameter relationships and dependencies",
            "- Validation issues and their causes",
            "- Tolerance analysis results",
        ])
    
    prompt_parts.extend([
        "",
        "IMPORTANT RULES:",
        "- Always use the specified tools - do not generate arbitrary code",
        "- Ensure all parameter references in features are valid",
        "- Maintain consistency (e.g., if changing a parameter, update features that use it)",
        "- Provide clear, helpful messages explaining what you did",
    ])
    
    return "\n".join(prompt_parts)


def get_part_schema_json() -> dict:
    """
    Get JSON schema for Part IR (for OpenAI function calling).
    """
    # Simplified schema based on Part model
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "params": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string", "default": "mm"},
                        "tolerance_class": {"type": "string", "nullable": True}
                    },
                    "required": ["name", "value"]
                }
            },
            "features": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["cylinder", "hole", "chamfer", "joint_interface", "link_body", "pocket", "fillet"]
                        },
                        "name": {"type": "string"},
                        "params": {
                            "type": "object",
                            "additionalProperties": {"oneOf": [{"type": "string"}, {"type": "number"}]}
                        },
                        "critical": {"type": "boolean", "default": False}
                    },
                    "required": ["type", "name"]
                }
            },
            "chains": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "terms": {"type": "array", "items": {"type": "string"}},
                        "target_value": {"type": "number", "nullable": True},
                        "target_tolerance": {"type": "number", "nullable": True}
                    },
                    "required": ["name", "terms"]
                }
            },
            "constraints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["coincident", "parallel", "perpendicular", "distance", "angle", "reference"]
                        },
                        "entities": {"type": "array", "items": {"type": "string"}},
                        "params": {"type": "object"}
                    },
                    "required": ["name", "type"]
                }
            }
        },
        "required": ["name"]
    }


def get_operations_schema_json() -> dict:
    """
    Get JSON schema for operations list (for OpenAI function calling).
    """
    return {
        "type": "object",
        "properties": {
            "operations": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "set_parameter"},
                                "name": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["type", "name", "value"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "update_parameter_tolerance"},
                                "name": {"type": "string"},
                                "tolerance_class": {"type": "string", "nullable": True}
                            },
                            "required": ["type", "name"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "add_feature"},
                                "feature": get_part_schema_json()["properties"]["features"]["items"]
                            },
                            "required": ["type", "feature"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {"const": "update_feature"},
                                "feature_name": {"type": "string"},
                                "params": {
                                    "type": "object",
                                    "additionalProperties": {"oneOf": [{"type": "string"}, {"type": "number"}]}
                                }
                            },
                            "required": ["type", "feature_name"]
                        }
                    ]
                }
            }
        },
        "required": ["operations"]
    }


def run_agent(
    mode: AgentMode,
    scope: AgentScope,
    part: Optional[Part],
    user_prompt: str,
) -> AgentResult:
    """
    Run the LLM agent to process a user's natural language command.
    
    Args:
        mode: CREATE, EDIT, or EXPLAIN
        scope: What parts of the model can be modified
        part: Current part (None for CREATE mode)
        user_prompt: User's natural language command
        
    Returns:
        AgentResult with updated part, operations, and message
    """
    client = get_openai_client()
    
    # Build system prompt
    system_prompt = build_system_prompt(mode, scope, part)
    
    # Build user context
    user_messages = []
    
    if part:
        user_messages.append({
            "role": "user",
            "content": f"Current part:\n{summarize_part(part)}\n\nUser request: {user_prompt}"
        })
    else:
        user_messages.append({
            "role": "user",
            "content": f"User request: {user_prompt}"
        })
    
    # Define tools based on mode
    tools = []
    tool_choice = {}
    
    if mode == AgentMode.CREATE:
        tools.append({
            "type": "function",
            "function": {
                "name": "create_new_part",
                "description": "Create a new part from scratch based on the user's description",
                "parameters": get_part_schema_json()
            }
        })
        tool_choice = {"type": "function", "function": {"name": "create_new_part"}}
    
    elif mode == AgentMode.EDIT:
        tools.append({
            "type": "function",
            "function": {
                "name": "propose_operations",
                "description": "Propose a list of operations to modify the existing part",
                "parameters": get_operations_schema_json()
            }
        })
        tool_choice = {"type": "function", "function": {"name": "propose_operations"}}
    
    else:  # EXPLAIN
        tools.append({
            "type": "function",
            "function": {
                "name": "explain_model",
                "description": "Provide an explanation about the part",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "explanation": {
                            "type": "string",
                            "description": "Your explanation in natural language"
                        }
                    },
                    "required": ["explanation"]
                }
            }
        })
        tool_choice = {"type": "function", "function": {"name": "explain_model"}}
    
    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using a cost-effective model, can be upgraded
            messages=[
                {"role": "system", "content": system_prompt},
                *user_messages
            ],
            tools=tools,
            tool_choice=tool_choice,
            temperature=0.3,  # Lower temperature for more deterministic results
        )
        
        message = response.choices[0].message
        
        # Process tool calls
        if not message.tool_calls:
            return AgentResult(
                part=None,
                operations=[],
                message="Error: LLM did not return a tool call. Please try rephrasing your request."
            )
        
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        if mode == AgentMode.CREATE:
            if function_name != "create_new_part":
                return AgentResult(
                    part=None,
                    operations=[],
                    message=f"Error: Expected create_new_part, got {function_name}"
                )
            
            # Validate and create Part
            try:
                new_part = Part.model_validate(arguments)
                
                # Validate that it can be built
                try:
                    build_cad_model(new_part)
                    issues = validate_part(new_part)
                    issue_summary = f" ({len(issues)} validation issues)" if issues else ""
                except Exception as e:
                    return AgentResult(
                        part=None,
                        operations=[],
                        message=f"Error: Generated part cannot be built: {str(e)}"
                    )
                
                return AgentResult(
                    part=new_part,
                    operations=[],
                    message=f"Created new part '{new_part.name}' with {len(new_part.params)} parameters and {len(new_part.features)} features{issue_summary}."
                )
            except Exception as e:
                return AgentResult(
                    part=None,
                    operations=[],
                    message=f"Error: Invalid part structure from LLM: {str(e)}"
                )
        
        elif mode == AgentMode.EDIT:
            if function_name != "propose_operations":
                return AgentResult(
                    part=None,
                    operations=[],
                    message=f"Error: Expected propose_operations, got {function_name}"
                )
            
            # Parse operations
            operations_json = arguments.get("operations", [])
            operations: list[Operation] = []
            
            for op_json in operations_json:
                op_type = op_json.get("type")
                try:
                    if op_type == "set_parameter":
                        operations.append(SetParameterOperation.model_validate(op_json))
                    elif op_type == "update_parameter_tolerance":
                        operations.append(UpdateParameterToleranceOperation.model_validate(op_json))
                    elif op_type == "add_feature":
                        operations.append(AddFeatureOperation.model_validate(op_json))
                    elif op_type == "update_feature":
                        operations.append(UpdateFeatureOperation.model_validate(op_json))
                    else:
                        return AgentResult(
                            part=None,
                            operations=[],
                            message=f"Error: Unknown operation type: {op_type}"
                        )
                except Exception as e:
                    return AgentResult(
                        part=None,
                        operations=[],
                        message=f"Error: Invalid operation structure: {str(e)}"
                    )
            
            # Apply operations
            try:
                updated_part = apply_operations(part, operations)
                
                # Validate
                try:
                    build_cad_model(updated_part)
                    issues = validate_part(updated_part)
                    issue_summary = f" ({len(issues)} validation issues)" if issues else ""
                except Exception as e:
                    return AgentResult(
                        part=None,
                        operations=[],
                        message=f"Error: Modified part cannot be built: {str(e)}"
                    )
                
                # Generate summary message
                op_summary = []
                for op in operations:
                    if isinstance(op, SetParameterOperation):
                        op_summary.append(f"set {op.name} to {op.value}")
                    elif isinstance(op, UpdateParameterToleranceOperation):
                        op_summary.append(f"updated tolerance for {op.name}")
                    elif isinstance(op, AddFeatureOperation):
                        op_summary.append(f"added feature {op.feature.name}")
                    elif isinstance(op, UpdateFeatureOperation):
                        op_summary.append(f"updated feature {op.feature_name}")
                
                message = f"Applied {len(operations)} operation(s): {', '.join(op_summary)}{issue_summary}."
                
                return AgentResult(
                    part=updated_part,
                    operations=operations,
                    message=message
                )
            except Exception as e:
                return AgentResult(
                    part=None,
                    operations=[],
                    message=f"Error: Failed to apply operations: {str(e)}"
                )
        
        else:  # EXPLAIN
            if function_name != "explain_model":
                return AgentResult(
                    part=None,
                    operations=[],
                    message=f"Error: Expected explain_model, got {function_name}"
                )
            
            explanation = arguments.get("explanation", "No explanation provided.")
            return AgentResult(
                part=None,
                operations=[],
                message=explanation
            )
    
    except Exception as e:
        return AgentResult(
            part=None,
            operations=[],
            message=f"Error: LLM API call failed: {str(e)}"
        )

