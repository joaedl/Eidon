"""
Technical Drawing module: generates simple SVG drawings from Part IR.

MVP: Generates a front view (XY plane projection) with auto-dimensions
from DSL dimension entries.
"""

from typing import Optional
from app.core.ir import Part, Sketch, SketchEntity, SketchDimension


def generate_front_view_svg(part: Part, width: int = 800, height: int = 600) -> str:
    """
    Generate a simple SVG front view of a part.
    
    MVP: Projects the part onto the XY plane and draws dimensions from sketch dimensions.
    For now, focuses on sketch-based features (extrude from sketch).
    
    Args:
        part: The Part IR to draw
        width: SVG canvas width in pixels
        height: SVG canvas height in pixels
        
    Returns:
        SVG string
    """
    # Calculate bounding box from all sketches
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    # Collect all sketches (from sketch features or part.sketches)
    all_sketches: list[Sketch] = []
    for feature in part.features:
        if feature.type == "sketch" and feature.sketch:
            all_sketches.append(feature.sketch)
    all_sketches.extend(part.sketches)
    
    if not all_sketches:
        # No sketches - return empty SVG
        return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#999">No sketches to display</text>
</svg>'''
    
    # Find bounding box from all sketch entities
    for sketch in all_sketches:
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                min_x = min(min_x, entity.start[0], entity.end[0])
                max_x = max(max_x, entity.start[0], entity.end[0])
                min_y = min(min_y, entity.start[1], entity.end[1])
                max_y = max(max_y, entity.start[1], entity.end[1])
            elif entity.type == "circle" and entity.center and entity.radius:
                min_x = min(min_x, entity.center[0] - entity.radius)
                max_x = max(max_x, entity.center[0] + entity.radius)
                min_y = min(min_y, entity.center[1] - entity.radius)
                max_y = max(max_y, entity.center[1] + entity.radius)
            elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
                min_x = min(min_x, entity.corner1[0], entity.corner2[0])
                max_x = max(max_x, entity.corner1[0], entity.corner2[0])
                min_y = min(min_y, entity.corner1[1], entity.corner2[1])
                max_y = max(max_y, entity.corner1[1], entity.corner2[1])
    
    if min_x == float('inf'):
        # No valid entities
        return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#999">No geometry to display</text>
</svg>'''
    
    # Add padding
    padding = 50
    range_x = max_x - min_x
    range_y = max_y - min_y
    
    if range_x == 0:
        range_x = 100
    if range_y == 0:
        range_y = 100
    
    # Calculate scale to fit
    scale_x = (width - 2 * padding) / range_x
    scale_y = (height - 2 * padding) / range_y
    scale = min(scale_x, scale_y)
    
    # Calculate offset to center
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    offset_x = width / 2 - center_x * scale
    offset_y = height / 2 + center_y * scale  # Flip Y axis
    
    def world_to_svg(x: float, y: float) -> tuple[float, float]:
        """Convert world coordinates to SVG coordinates."""
        svg_x = x * scale + offset_x
        svg_y = -y * scale + offset_y  # Flip Y
        return (svg_x, svg_y)
    
    # Build SVG
    svg_lines = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '  <defs>',
        '    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
        '      <polygon points="0 0, 10 3, 0 6" fill="#333" />',
        '    </marker>',
        '  </defs>',
        '  <g id="geometry">'
    ]
    
    # Draw entities
    for sketch in all_sketches:
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                x1, y1 = world_to_svg(entity.start[0], entity.start[1])
                x2, y2 = world_to_svg(entity.end[0], entity.end[1])
                svg_lines.append(f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000" stroke-width="2" />')
            elif entity.type == "circle" and entity.center and entity.radius:
                cx, cy = world_to_svg(entity.center[0], entity.center[1])
                r = entity.radius * scale
                svg_lines.append(f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" stroke="#000" stroke-width="2" fill="none" />')
            elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
                x1, y1 = world_to_svg(entity.corner1[0], entity.corner1[1])
                x2, y2 = world_to_svg(entity.corner2[0], entity.corner2[1])
                # Ensure x1 < x2 and y1 < y2 for rectangle
                rect_x = min(x1, x2)
                rect_y = min(y1, y2)
                rect_width = abs(x2 - x1)
                rect_height = abs(y2 - y1)
                svg_lines.append(f'    <rect x="{rect_x:.2f}" y="{rect_y:.2f}" width="{rect_width:.2f}" height="{rect_height:.2f}" stroke="#000" stroke-width="2" fill="none" />')
    
    svg_lines.append('  </g>')
    svg_lines.append('  <g id="dimensions">')
    
    # Draw dimensions
    for sketch in all_sketches:
        for dimension in sketch.dimensions:
            if dimension.type == "length":
                # Find the entity
                entity_id = dimension.entity_ids[0]
                entity = next((e for e in sketch.entities if e.id == entity_id), None)
                if entity and entity.type == "line" and entity.start and entity.end:
                    x1, y1 = world_to_svg(entity.start[0], entity.start[1])
                    x2, y2 = world_to_svg(entity.end[0], entity.end[1])
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    
                    # Draw dimension line perpendicular to entity
                    dx = x2 - x1
                    dy = y2 - y1
                    length = (dx**2 + dy**2)**0.5
                    if length > 0:
                        perp_x = -dy / length * 30
                        perp_y = dx / length * 30
                        dim_x = mid_x + perp_x
                        dim_y = mid_y + perp_y
                        
                        svg_lines.append(f'    <line x1="{mid_x:.2f}" y1="{mid_y:.2f}" x2="{dim_x:.2f}" y2="{dim_y:.2f}" stroke="#0066cc" stroke-width="1" />')
                        svg_lines.append(f'    <text x="{dim_x + 5:.2f}" y="{dim_y + 5:.2f}" fill="#0066cc" font-size="12">{dimension.value} {dimension.unit}</text>')
            elif dimension.type == "diameter":
                # Find the entity
                entity_id = dimension.entity_ids[0]
                entity = next((e for e in sketch.entities if e.id == entity_id), None)
                if entity and entity.type == "circle" and entity.center and entity.radius:
                    cx, cy = world_to_svg(entity.center[0], entity.center[1])
                    r = entity.radius * scale
                    
                    # Draw diameter dimension
                    svg_lines.append(f'    <line x1="{cx - r - 20:.2f}" y1="{cy:.2f}" x2="{cx + r + 20:.2f}" y2="{cy:.2f}" stroke="#0066cc" stroke-width="1" marker-end="url(#arrowhead)" marker-start="url(#arrowhead)" />')
                    svg_lines.append(f'    <text x="{cx:.2f}" y="{cy - 10:.2f}" text-anchor="middle" fill="#0066cc" font-size="12">⌀{dimension.value} {dimension.unit}</text>')
    
    svg_lines.append('  </g>')
    svg_lines.append('</svg>')
    
    return '\n'.join(svg_lines)

