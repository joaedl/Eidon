"""
DSL Generator: converts Part IR back to DSL text.

This module provides the reverse operation of dsl_parser - it takes a Part IR
and generates the corresponding DSL code.
"""

from app.core.ir import Part, Param, Feature, Chain, Sketch, SketchEntity, SketchConstraint, SketchDimension


def ir_to_dsl(part: Part) -> str:
    """
    Convert a Part IR object to DSL text.
    
    Args:
        part: The Part IR to convert
        
    Returns:
        str: The DSL code representation
    """
    lines = [f"part {part.name} {{"]
    
    # Add parameters
    for param_name, param in sorted(part.params.items()):
        # Format value nicely (remove .0 for integers)
        value_str = str(int(param.value)) if isinstance(param.value, float) and param.value.is_integer() else str(param.value)
        line = f"  param {param_name} = {value_str} {param.unit}"
        if param.tolerance_class:
            line += f" tolerance {param.tolerance_class}"
        lines.append(line)
    
    # Add features
    for feature in part.features:
        if feature.type == "sketch" and feature.sketch:
            # Generate sketch feature
            sketch = feature.sketch
            lines.append(f"  feature {feature.name} = sketch(on_plane=\"{sketch.plane}\") {{")
            
            # Add entities
            for entity in sketch.entities:
                if entity.type == "line":
                    lines.append(f"    line {entity.id} from ({entity.start[0]}, {entity.start[1]}) to ({entity.end[0]}, {entity.end[1]})")
                elif entity.type == "circle":
                    # Find unit from dimensions or default to mm
                    unit = "mm"
                    for dim in sketch.dimensions:
                        if entity.id in dim.entity_ids:
                            unit = dim.unit
                            break
                    lines.append(f"    circle {entity.id} center ({entity.center[0]}, {entity.center[1]}) radius {entity.radius} {unit}")
                elif entity.type == "rectangle":
                    lines.append(f"    rectangle {entity.id} from ({entity.corner1[0]}, {entity.corner1[1]}) to ({entity.corner2[0]}, {entity.corner2[1]})")
            
            # Add constraints
            for constraint in sketch.constraints:
                entity_ids_str = ", ".join(constraint.entity_ids)
                lines.append(f"    {constraint.type}({entity_ids_str})")
            
            # Add dimensions (MVP: only length and diameter)
            for dim in sketch.dimensions:
                if dim.type == "length":
                    lines.append(f"    dim_length({dim.entity_ids[0]}, {dim.value} {dim.unit})")
                elif dim.type == "diameter":
                    lines.append(f"    dim_diameter({dim.entity_ids[0]}, {dim.value} {dim.unit})")
                # MVP: distance and radius dimensions not supported
            
            lines.append("  }")
        else:
            # Regular feature
            # Build feature arguments string
            args = []
            for key, value in feature.params.items():
                if key == "plane":  # Skip plane for sketch features (handled above)
                    continue
                if isinstance(value, (int, float)):
                    # Direct numeric value - format nicely (remove .0 for integers)
                    if isinstance(value, float) and value.is_integer():
                        args.append(f"{key} = {int(value)}")
                    else:
                        args.append(f"{key} = {value}")
                elif isinstance(value, str):
                    # Could be a parameter reference or string literal
                    # If it's a parameter name, use it as-is
                    if value in part.params:
                        args.append(f"{key} = {value}")
                    else:
                        # String literal (like operation="cut" for extrude)
                        args.append(f'{key} = "{value}"')
                else:
                    args.append(f"{key} = {value}")
            
            args_str = ", ".join(args)
            lines.append(f"  feature {feature.name} = {feature.type}({args_str})")
    
    # Add chains
    for chain in part.chains:
        terms_str = ", ".join(chain.terms)
        lines.append(f"  chain {chain.name} {{")
        lines.append(f"    terms = [{terms_str}]")
        
        if chain.target_value is not None:
            lines.append(f"    target_value = {chain.target_value}")
        if chain.target_tolerance is not None:
            lines.append(f"    target_tolerance = {chain.target_tolerance}")
        
        lines.append("  }")
    
    # Add constraints (if any)
    if part.constraints:
        for constraint in part.constraints:
            entities_str = ", ".join(constraint.entities)
            params_str = ", ".join([f"{k} = {v}" for k, v in constraint.params.items()])
            if params_str:
                lines.append(f"  constraint {constraint.name} = {constraint.type}(entities = [{entities_str}], {params_str})")
            else:
                lines.append(f"  constraint {constraint.name} = {constraint.type}(entities = [{entities_str}])")
    
    lines.append("}")
    
    return "\n".join(lines)

