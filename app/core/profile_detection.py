"""
Profile detection for sketches.

Detects closed profiles (outer boundaries and holes) from sketch entities.
This enables proper boolean operations (extrude with holes).
"""

from typing import Optional
from app.core.ir import Sketch, SketchEntity, Profile
import math


def calculate_entity_area(entity: SketchEntity) -> float:
    """Calculate the area enclosed by an entity (for circles and rectangles)."""
    if entity.type == "circle" and entity.center and entity.radius:
        return math.pi * entity.radius * entity.radius
    elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
        c1 = entity.corner1
        c2 = entity.corner2
        width = abs(c2[0] - c1[0])
        height = abs(c2[1] - c1[1])
        return width * height
    return 0.0


def find_closed_loops(entities: list[SketchEntity]) -> list[list[str]]:
    """
    Find closed loops from line entities by following connected endpoints.
    
    Returns a list of loops, where each loop is a list of entity IDs in order.
    """
    if not entities:
        return []
    
    # Build adjacency map: point -> list of entities connected at that point
    point_to_entities: dict[tuple[float, float], list[tuple[str, bool]]] = {}
    # bool indicates if point is start (True) or end (False) of the entity
    
    for entity in entities:
        if entity.type == "line" and entity.start and entity.end:
            start = (round(entity.start[0], 6), round(entity.start[1], 6))
            end = (round(entity.end[0], 6), round(entity.end[1], 6))
            
            if start not in point_to_entities:
                point_to_entities[start] = []
            if end not in point_to_entities:
                point_to_entities[end] = []
            
            point_to_entities[start].append((entity.id, True))
            point_to_entities[end].append((entity.id, False))
    
    # Find closed loops by following connected lines
    loops: list[list[str]] = []
    used_entities = set()
    
    for start_entity in entities:
        if start_entity.type != "line" or start_entity.id in used_entities:
            continue
        if not start_entity.start or not start_entity.end:
            continue
        
        # Try to find a loop starting from this entity
        loop = _find_loop_from_entity(start_entity, entities, point_to_entities, used_entities)
        if loop and len(loop) >= 3:  # At least 3 entities for a closed loop
            loops.append(loop)
            used_entities.update(loop)
    
    return loops


def _find_loop_from_entity(
    start_entity: SketchEntity,
    all_entities: list[SketchEntity],
    point_to_entities: dict[tuple[float, float], list[tuple[str, bool]]],
    used_entities: set[str]
) -> Optional[list[str]]:
    """Find a closed loop starting from a given entity."""
    if not start_entity.start or not start_entity.end:
        return None
    
    entity_map = {e.id: e for e in all_entities}
    loop = [start_entity.id]
    current_point = (round(start_entity.end[0], 6), round(start_entity.end[1], 6))
    start_point = (round(start_entity.start[0], 6), round(start_entity.start[1], 6))
    max_iterations = len(all_entities)  # Prevent infinite loops
    
    for _ in range(max_iterations):
        # Check if we've closed the loop
        if current_point == start_point and len(loop) >= 3:
            return loop
        
        # Find next entity connected at current point
        connected = point_to_entities.get(current_point, [])
        next_entity_id = None
        
        for entity_id, is_start in connected:
            if entity_id not in loop and entity_id not in used_entities:
                next_entity_id = entity_id
                break
        
        if not next_entity_id:
            return None  # Dead end
        
        next_entity = entity_map.get(next_entity_id)
        if not next_entity or not next_entity.start or not next_entity.end:
            return None
        
        loop.append(next_entity_id)
        
        # Move to the other end of this entity
        next_start = (round(next_entity.start[0], 6), round(next_entity.start[1], 6))
        next_end = (round(next_entity.end[0], 6), round(next_entity.end[1], 6))
        
        if current_point == next_start:
            current_point = next_end
        elif current_point == next_end:
            current_point = next_start
        else:
            return None  # Not connected
    
    return None  # Loop too long or not closed


def detect_profiles(sketch: Sketch) -> list[Profile]:
    """
    Detect closed profiles (outer boundaries and holes) from sketch entities.
    
    Algorithm:
    1. Find all closed loops from line entities
    2. Treat circles and rectangles as individual closed profiles
    3. Calculate area for each profile
    4. Largest profile is the outer boundary, smaller ones inside are holes
    
    Args:
        sketch: The sketch to analyze
        
    Returns:
        List of detected profiles, with outer boundary first, then holes
    """
    profiles: list[Profile] = []
    
    # Find closed loops from lines
    line_entities = [e for e in sketch.entities if e.type == "line"]
    loops = find_closed_loops(line_entities)
    
    for i, loop in enumerate(loops):
        # Calculate approximate area (bounding box area for now)
        # In a full implementation, we'd calculate actual polygon area
        loop_entities = [e for e in sketch.entities if e.id in loop]
        if not loop_entities:
            continue
        
        # Calculate bounding box area as approximation
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for entity in loop_entities:
            if entity.start:
                min_x = min(min_x, entity.start[0])
                max_x = max(max_x, entity.start[0])
                min_y = min(min_y, entity.start[1])
                max_y = max(max_y, entity.start[1])
            if entity.end:
                min_x = min(min_x, entity.end[0])
                max_x = max(max_x, entity.end[0])
                min_y = min(min_y, entity.end[1])
                max_y = max(max_y, entity.end[1])
        
        area = (max_x - min_x) * (max_y - min_y) if max_x > min_x and max_y > min_y else 0.0
        
        profiles.append(Profile(
            id=f"profile_{i}",
            type="outer",  # Will be determined later
            entity_ids=loop,
            area=area,
            is_outer=True  # Will be determined later
        ))
    
    # Add circles and rectangles as individual profiles
    for entity in sketch.entities:
        if entity.type == "circle" or entity.type == "rectangle":
            area = calculate_entity_area(entity)
            profiles.append(Profile(
                id=f"profile_{entity.id}",
                type="outer",
                entity_ids=[entity.id],
                area=area,
                is_outer=True
            ))
    
    if not profiles:
        return []
    
    # Sort by area (largest first)
    profiles.sort(key=lambda p: p.area or 0.0, reverse=True)
    
    # Determine outer vs holes
    # Largest is outer, others are holes if they're inside it
    # For MVP, we'll use a simple heuristic: largest is outer, rest are holes
    # In a full implementation, we'd check if smaller profiles are actually inside larger ones
    result: list[Profile] = []
    
    if profiles:
        # First profile (largest) is outer
        outer = profiles[0]
        outer.type = "outer"
        outer.is_outer = True
        result.append(outer)
        
        # Rest are holes (if they're smaller)
        for profile in profiles[1:]:
            # Simple heuristic: if area is significantly smaller, treat as hole
            # In full implementation, would check geometric containment
            if profile.area and outer.area and profile.area < outer.area * 0.9:
                profile.type = "hole"
                profile.is_outer = False
                result.append(profile)
            else:
                # Could be multiple outer boundaries (separate regions)
                profile.type = "outer"
                profile.is_outer = True
                result.append(profile)
    
    return result

