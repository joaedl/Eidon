"""
Pattern generators for common CAD patterns.

These functions generate DSL code snippets that can be inserted into
part definitions. They follow a consistent interface:

def pattern_name_dsl(name: str, **params) -> str:
    \"\"\"
    Generate DSL code for a pattern.
    
    Args:
        name: Base name for the pattern (used for features/params)
        **params: Pattern-specific parameters
        
    Returns:
        DSL code string (can be multiple lines)
    \"\"\"
    ...
"""


def gear_dsl(name: str, module: float, teeth: int, width: float) -> str:
    """
    Generate DSL code for a simple gear.
    
    Args:
        name: Name prefix for the gear
        module: Gear module (pitch diameter / number of teeth)
        teeth: Number of teeth
        width: Gear width/thickness
        
    Returns:
        DSL code string
    """
    # Placeholder implementation
    # In a full implementation, this would generate proper gear geometry
    pitch_dia = module * teeth
    return f"""  param {name}_module = {module} mm
  param {name}_teeth = {teeth}
  param {name}_width = {width} mm
  param {name}_pitch_dia = {pitch_dia} mm
  feature {name}_body = cylinder(dia = {name}_pitch_dia, length = {name}_width)"""


def hole_grid_dsl(name: str, rows: int, cols: int, pitch: float, dia: float) -> str:
    """
    Generate DSL code for a 2D hole grid pattern.
    
    Args:
        name: Name prefix for the holes
        rows: Number of rows
        cols: Number of columns
        pitch: Spacing between holes (center-to-center)
        dia: Hole diameter
        
    Returns:
        DSL code string
    """
    lines = []
    lines.append(f"  param {name}_pitch = {pitch} mm")
    lines.append(f"  param {name}_hole_dia = {dia} mm")
    
    for i in range(rows):
        for j in range(cols):
            x = j * pitch
            y = i * pitch
            hole_name = f"{name}_hole_{i}_{j}"
            lines.append(f"  feature {hole_name} = hole(dia = {name}_hole_dia, x = {x}, y = {y})")
    
    return "\n".join(lines)


def bolt_circle_dsl(name: str, dia: float, num_holes: int, hole_dia: float, thickness: float) -> str:
    """
    Generate DSL code for a bolt circle pattern.
    
    Args:
        name: Name prefix
        dia: Bolt circle diameter
        num_holes: Number of holes
        hole_dia: Hole diameter
        thickness: Material thickness
        
    Returns:
        DSL code string
    """
    return f"""  param {name}_bc_dia = {dia} mm
  param {name}_num_holes = {num_holes}
  param {name}_hole_dia = {hole_dia} mm
  param {name}_thickness = {thickness} mm
  feature {name}_interface = joint_interface(
    dia = {name}_bc_dia,
    hole_dia = {name}_hole_dia,
    holes = {name}_num_holes,
    thickness = {name}_thickness
  )"""

