"""
Geometry builder: converts IR (Part) to CadQuery models and meshes.

This module takes a Part IR object and builds the corresponding 3D geometry
using CadQuery, then exports it as mesh data for the frontend.
"""

import cadquery as cq
from typing import Any
from app.core.ir import Part, Feature, Param, Sketch
from app.core.profile_detection import detect_profiles


class MeshData:
    """Simple mesh data structure for frontend consumption."""
    
    def __init__(self, vertices: list[list[float]], faces: list[list[int]], feature_id: str | None = None):
        self.vertices = vertices  # List of [x, y, z] coordinates
        self.faces = faces  # List of face indices (triangles: [i, j, k])
        self.feature_id = feature_id  # Associated feature name for selection
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        result = {
            "vertices": self.vertices,
            "faces": self.faces
        }
        if self.feature_id:
            result["featureId"] = self.feature_id
        return result


class MultiMeshData:
    """Container for multiple meshes (one per feature)."""
    
    def __init__(self, meshes: list[MeshData], face_to_feature: list[str | None] | None = None):
        self.meshes = meshes
        self.face_to_feature = face_to_feature  # Optional: direct face-to-feature mapping
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict with combined mesh and feature mapping."""
        if self.face_to_feature and self.meshes:
            # Use provided face_to_feature mapping with first mesh
            mesh = self.meshes[0]
            return {
                "vertices": mesh.vertices,
                "faces": mesh.faces,
                "faceToFeature": self.face_to_feature
            }
        
        # Combine all meshes into one, but track which faces belong to which feature
        all_vertices: list[list[float]] = []
        all_faces: list[list[int]] = []
        face_to_feature: list[str | None] = []  # Maps face index to feature_id
        
        vertex_offset = 0
        for mesh in self.meshes:
            # Add vertices
            all_vertices.extend(mesh.vertices)
            
            # Add faces with offset indices
            for face in mesh.faces:
                all_faces.append([v + vertex_offset for v in face])
                face_to_feature.append(mesh.feature_id)
            
            vertex_offset += len(mesh.vertices)
        
        return {
            "vertices": all_vertices,
            "faces": all_faces,
            "faceToFeature": face_to_feature  # Maps each face to its feature_id
        }


def _build_profile_workplane_on_face(
    sketch: Sketch, 
    distance: float, 
    face_wp: cq.Workplane,
    direction: tuple[float, float, float]
) -> cq.Workplane | None:
    """
    Build a workplane with extruded profile on a specific face.
    
    Args:
        sketch: The sketch with profiles
        distance: Extrusion distance
        face_wp: Workplane on the face to extrude from
        direction: Extrusion direction vector (x, y, z)
        
    Returns:
        Extruded workplane, or None if construction fails
    """
    # For MVP, we'll build the profile in 2D first, then position it on the face
    # In full implementation, would transform sketch entities to face coordinates
    
    # Build profile using existing method (assumes XY plane)
    profile_wp = _build_profile_workplane(sketch, distance)
    
    if not profile_wp:
        return None
    
    # For MVP: if face is not XY plane, we need to transform
    # For now, assume sketches on faces are still in XY plane coordinates
    # In full implementation, would:
    # 1. Get face normal and transform sketch entities
    # 2. Build profile on face directly
    # 3. Extrude along face normal (or specified direction)
    
    # Apply direction to extrusion
    # CadQuery extrude uses workplane normal by default
    # For custom direction, we'd need to use OCP directly or transform
    # For MVP, assume direction is handled by workplane orientation
    
    return profile_wp


def _build_profile_workplane(sketch: Sketch, distance: float) -> cq.Workplane | None:
    """
    Build a CadQuery workplane from sketch profiles (outer boundary + holes).
    
    Args:
        sketch: The sketch with detected profiles
        distance: Extrusion distance
        
    Returns:
        CadQuery workplane with extruded solid, or None if no valid geometry
    """
    if not sketch.profiles:
        # Fallback to bounding box method if no profiles detected
        return _build_bounding_box_workplane(sketch, distance)
    
    # Find outer profile (should be first/largest)
    outer_profile = None
    hole_profiles = []
    
    for profile in sketch.profiles:
        if profile.is_outer and profile.type == "outer":
            if outer_profile is None:
                outer_profile = profile
            else:
                # Multiple outer profiles - treat as separate regions
                # For MVP, use first one
                pass
        elif profile.type == "hole":
            hole_profiles.append(profile)
    
    if not outer_profile:
        # No outer profile found, fallback
        return _build_bounding_box_workplane(sketch, distance)
    
    try:
        # Build outer profile wire
        outer_wire = _build_wire_from_profile(outer_profile, sketch)
        if not outer_wire:
            return _build_bounding_box_workplane(sketch, distance)
        
        # Build hole wires
        hole_wires = []
        for hole_profile in hole_profiles:
            hole_wire = _build_wire_from_profile(hole_profile, sketch)
            if hole_wire:
                hole_wires.append(hole_wire)
        
        # Create face with holes using OCP directly
        try:
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
            from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
            from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
            from OCP.gp import gp_Vec
            from OCP.TopoDS import TopoDS_Wire
            
            # Method 1: Try creating face with holes
            face_builder = BRepBuilderAPI_MakeFace(outer_wire.wrapped)
            
            # Add holes
            for hole_wire in hole_wires:
                if hasattr(hole_wire, 'wrapped'):
                    hole_wire_occ = hole_wire.wrapped
                    # Get wire from shape if needed
                    from OCP.TopExp import TopExp_Explorer
                    from OCP.TopAbs import TopAbs_WIRE
                    if not isinstance(hole_wire_occ, TopoDS_Wire):
                        exp = TopExp_Explorer(hole_wire_occ, TopAbs_WIRE)
                        if exp.More():
                            hole_wire_occ = exp.Current()
                    face_builder.Add(hole_wire_occ)
            
            # For now, always use 3D cut method to ensure holes are properly subtracted
            # The face method creates faces with boundaries but doesn't guarantee hole subtraction
            raise ValueError("Using 3D cut method for reliable hole subtraction")
        except Exception as face_error:
            # Fallback method: Extrude outer solid, then cut hole solids using CadQuery
            try:
                # Build outer workplane and extrude
                outer_wp = _build_2d_profile_from_entities(outer_profile, sketch)
                if not outer_wp:
                    raise ValueError("Failed to build outer profile")
                
                result_wp = outer_wp.extrude(distance)
                
                # Cut each hole in 3D
                for hole_profile in hole_profiles:
                    hole_wp = _build_2d_profile_from_entities(hole_profile, sketch)
                    if hole_wp:
                        # Extrude hole and cut from result
                        hole_solid_wp = hole_wp.extrude(distance)
                        result_wp = result_wp.cut(hole_solid_wp)
                
                return result_wp
            except Exception as cut_error:
                # Final fallback: bounding box
                print(f"Warning: Both face and 3D cut methods failed: {face_error}, {cut_error}")
                return _build_bounding_box_workplane(sketch, distance)
        except Exception as ocp_error:
            # Fallback: use workplane method (simpler but may not support holes)
            print(f"Warning: OCP face creation failed, using workplane fallback: {ocp_error}")
            outer_wp = _build_2d_profile_from_entities(outer_profile, sketch)
            if outer_wp:
                # For MVP, just extrude outer without holes if OCP fails
                return outer_wp.extrude(distance)
            return _build_bounding_box_workplane(sketch, distance)
    except Exception as e:
        # Fallback to bounding box if wire construction fails
        print(f"Warning: Profile construction failed, using bounding box: {e}")
        return _build_bounding_box_workplane(sketch, distance)


def _build_2d_profile_from_entities(profile, sketch: Sketch) -> cq.Workplane | None:
    """
    Build a 2D CadQuery workplane from profile entities.
    """
    entity_map = {e.id: e for e in sketch.entities}
    profile_entities = [entity_map.get(eid) for eid in profile.entity_ids if eid in entity_map]
    profile_entities = [e for e in profile_entities if e is not None]
    
    if not profile_entities:
        return None
    
    try:
        wp = cq.Workplane("XY")
        
        # Handle single entity profiles
        if len(profile_entities) == 1:
            entity = profile_entities[0]
            
            if entity.type == "rectangle" and entity.corner1 and entity.corner2:
                c1 = entity.corner1
                c2 = entity.corner2
                width = abs(c2[0] - c1[0])
                height = abs(c2[1] - c1[1])
                return wp.rect(width, height)
            
            elif entity.type == "circle" and entity.center and entity.radius:
                return wp.circle(entity.radius)
        
        # For line loops, use bounding box as fallback
        # In full implementation, would build proper wire from connected lines
        return _build_bounding_box_workplane_2d(profile_entities)
    except Exception as e:
        print(f"Warning: 2D profile construction failed: {e}")
        return _build_bounding_box_workplane_2d(profile_entities)


def _get_profile_center(profile, sketch: Sketch) -> tuple[float, float] | None:
    """Get the center point of a profile for positioning holes."""
    entity_map = {e.id: e for e in sketch.entities}
    profile_entities = [entity_map.get(eid) for eid in profile.entity_ids if eid in entity_map]
    profile_entities = [e for e in profile_entities if e is not None]
    
    if not profile_entities:
        return None
    
    # For circles, use center directly
    if len(profile_entities) == 1:
        entity = profile_entities[0]
        if entity.type == "circle" and entity.center:
            return entity.center
    
    # For other shapes, calculate centroid
    points = []
    for entity in profile_entities:
        if entity.type == "line":
            if entity.start:
                points.append(entity.start)
            if entity.end:
                points.append(entity.end)
        elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
            # Center of rectangle
            cx = (entity.corner1[0] + entity.corner2[0]) / 2
            cy = (entity.corner1[1] + entity.corner2[1]) / 2
            return (cx, cy)
        elif entity.type == "circle" and entity.center:
            return entity.center
    
    if points:
        # Calculate centroid
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        return (cx, cy)
    
    return None


def _build_bounding_box_workplane_2d(entities: list) -> cq.Workplane | None:
    """Build a 2D workplane from bounding box of entities."""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for entity in entities:
        if entity.type == "line" and entity.start and entity.end:
            min_x = min(min_x, entity.start[0], entity.end[0])
            max_x = max(max_x, entity.start[0], entity.end[0])
            min_y = min(min_y, entity.start[1], entity.end[1])
            max_y = max(max_y, entity.start[1], entity.end[1])
        elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
            min_x = min(min_x, entity.corner1[0], entity.corner2[0])
            max_x = max(max_x, entity.corner1[0], entity.corner2[0])
            min_y = min(min_y, entity.corner1[1], entity.corner2[1])
            max_y = max(max_y, entity.corner1[1], entity.corner2[1])
        elif entity.type == "circle" and entity.center and entity.radius:
            min_x = min(min_x, entity.center[0] - entity.radius)
            max_x = max(max_x, entity.center[0] + entity.radius)
            min_y = min(min_y, entity.center[1] - entity.radius)
            max_y = max(max_y, entity.center[1] + entity.radius)
    
    if max_x > min_x and max_y > min_y:
        width = max_x - min_x
        height = max_y - min_y
        return cq.Workplane("XY").rect(width, height)
    
    return None


def _build_wire_from_profile(profile, sketch: Sketch) -> cq.Wire | None:
    """
    Build a CadQuery wire from a profile's entities.
    
    Args:
        profile: The profile to build
        sketch: The sketch containing the entities
        
    Returns:
        CadQuery wire, or None if construction fails
    """
    entity_map = {e.id: e for e in sketch.entities}
    profile_entities = [entity_map.get(eid) for eid in profile.entity_ids if eid in entity_map]
    profile_entities = [e for e in profile_entities if e is not None]
    
    if not profile_entities:
        return None
    
    try:
        # For MVP: handle simple cases (rectangles, circles, closed line loops)
        if len(profile_entities) == 1:
            entity = profile_entities[0]
            
            if entity.type == "rectangle" and entity.corner1 and entity.corner2:
                c1 = entity.corner1
                c2 = entity.corner2
                width = abs(c2[0] - c1[0])
                height = abs(c2[1] - c1[1])
                center_x = (c1[0] + c2[0]) / 2
                center_y = (c1[1] + c2[1]) / 2
                
                # Create rectangle wire at correct position
                return cq.Workplane("XY").center(center_x, center_y).rect(width, height).val()
            
            elif entity.type == "circle" and entity.center and entity.radius:
                # Create circle wire at correct position
                center = entity.center
                return cq.Workplane("XY").center(center[0], center[1]).circle(entity.radius).val()
        
        # For line loops: build wire from connected lines
        elif all(e.type == "line" for e in profile_entities):
            # Build wire from line segments
            points = []
            for entity in profile_entities:
                if entity.start:
                    points.append((entity.start[0], entity.start[1]))
                if entity.end and entity.end not in [p[:2] for p in points]:
                    points.append((entity.end[0], entity.end[1]))
            
            if len(points) >= 3:
                # Create closed wire from points
                # Note: This assumes points are in order - in full implementation,
                # we'd properly order them based on entity connectivity
                try:
                    wire = cq.Wire.makePolygon([cq.Vector(p[0], p[1], 0) for p in points])
                    return wire
                except:
                    # Fallback: create bounding box
                    pass
        
        # Fallback: create bounding box
        return _build_bounding_box_wire(profile_entities)
    except Exception as e:
        print(f"Warning: Wire construction failed: {e}")
        return _build_bounding_box_wire(profile_entities)


def _build_bounding_box_wire(entities: list) -> cq.Wire | None:
    """Build a wire from bounding box of entities (fallback method)."""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for entity in entities:
        if entity.type == "line" and entity.start and entity.end:
            min_x = min(min_x, entity.start[0], entity.end[0])
            max_x = max(max_x, entity.start[0], entity.end[0])
            min_y = min(min_y, entity.start[1], entity.end[1])
            max_y = max(max_y, entity.start[1], entity.end[1])
        elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
            min_x = min(min_x, entity.corner1[0], entity.corner2[0])
            max_x = max(max_x, entity.corner1[0], entity.corner2[0])
            min_y = min(min_y, entity.corner1[1], entity.corner2[1])
            max_y = max(max_y, entity.corner1[1], entity.corner2[1])
        elif entity.type == "circle" and entity.center and entity.radius:
            min_x = min(min_x, entity.center[0] - entity.radius)
            max_x = max(max_x, entity.center[0] + entity.radius)
            min_y = min(min_y, entity.center[1] - entity.radius)
            max_y = max(max_y, entity.center[1] + entity.radius)
    
    if max_x > min_x and max_y > min_y:
        width = max_x - min_x
        height = max_y - min_y
        return cq.Workplane("XY").rect(width, height).val()
    
    return None


def _build_bounding_box_workplane(sketch: Sketch, distance: float) -> cq.Workplane | None:
    """Fallback: build workplane from bounding box (old method)."""
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    has_geometry = False
    
    for entity in sketch.entities:
        if getattr(entity, 'isConstruction', False):
            continue
            
        if entity.type == "line":
            if entity.start and entity.end:
                has_geometry = True
                min_x = min(min_x, entity.start[0], entity.end[0])
                max_x = max(max_x, entity.start[0], entity.end[0])
                min_y = min(min_y, entity.start[1], entity.end[1])
                max_y = max(max_y, entity.start[1], entity.end[1])
        elif entity.type == "rectangle":
            if entity.corner1 and entity.corner2:
                has_geometry = True
                min_x = min(min_x, entity.corner1[0], entity.corner2[0])
                max_x = max(max_x, entity.corner1[0], entity.corner2[0])
                min_y = min(min_y, entity.corner1[1], entity.corner2[1])
                max_y = max(max_y, entity.corner1[1], entity.corner2[1])
        elif entity.type == "circle":
            if entity.center and entity.radius:
                has_geometry = True
                min_x = min(min_x, entity.center[0] - entity.radius)
                max_x = max(max_x, entity.center[0] + entity.radius)
                min_y = min(min_y, entity.center[1] - entity.radius)
                max_y = max(max_y, entity.center[1] + entity.radius)
    
    if has_geometry and min_x != float('inf'):
        width = max_x - min_x
        height = max_y - min_y
        if width <= 0:
            width = 1.0
        if height <= 0:
            height = 1.0
        return cq.Workplane("XY").rect(width, height).extrude(distance)
    
    return None


def resolve_param_value(part: Part, param_ref: str | float) -> float:
    """
    Resolve a parameter reference to its numeric value.
    
    Args:
        part: The part containing parameters
        param_ref: Either a parameter name (str) or a direct value (float)
        
    Returns:
        float: The resolved numeric value
    """
    if isinstance(param_ref, (int, float)):
        return float(param_ref)
    
    if isinstance(param_ref, str):
        # Check if it's a parameter name
        if param_ref in part.params:
            return part.params[param_ref].value
        
        # Check if it's a value with unit like "1 mm"
        parts = param_ref.split()
        if len(parts) == 2:
            try:
                return float(parts[0])
            except ValueError:
                pass
        
        # If it's just a parameter name, try to get it
        if param_ref in part.params:
            return part.params[param_ref].value
    
    raise ValueError(f"Cannot resolve parameter reference: {param_ref}")


def _parse_normal_spec(normal_spec: str) -> tuple[float, float, float] | None:
    """Parse normal specification like '+X', '-Y', or '[1,0,0]'."""
    # Direction strings
    direction_map = {
        "+X": (1, 0, 0), "-X": (-1, 0, 0),
        "+Y": (0, 1, 0), "-Y": (0, -1, 0),
        "+Z": (0, 0, 1), "-Z": (0, 0, -1),
        "X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1),
    }
    
    if normal_spec in direction_map:
        return direction_map[normal_spec]
    
    # Try parsing as vector "[x,y,z]"
    if normal_spec.startswith("[") and normal_spec.endswith("]"):
        try:
            coords = [float(x.strip()) for x in normal_spec[1:-1].split(",")]
            if len(coords) == 3:
                return tuple(coords)
        except:
            pass
    
    return None


def _parse_point_spec(point_spec: str) -> tuple[float, float, float] | None:
    """Parse point specification like '[5,5,10]'."""
    if point_spec.startswith("[") and point_spec.endswith("]"):
        try:
            coords = [float(x.strip()) for x in point_spec[1:-1].split(",")]
            if len(coords) == 3:
                return tuple(coords)
        except:
            pass
    return None


def _get_face_normal(face: cq.Face) -> tuple[float, float, float]:
    """Get the normal vector of a face."""
    try:
        # Get face center and normal
        center = face.Center()
        normal = face.normalAt(center)
        return (normal.x, normal.y, normal.z)
    except:
        return (0, 0, 1)  # Default


def _get_face_center(face: cq.Face) -> tuple[float, float, float]:
    """Get the center point of a face."""
    try:
        center = face.Center()
        return (center.x, center.y, center.z)
    except:
        return (0, 0, 0)


def _get_face_area(face: cq.Face) -> float:
    """Get the area of a face."""
    try:
        return face.Area()
    except:
        return 0.0


def _find_face_by_normal(faces: list[cq.Face], target_normal: tuple[float, float, float]) -> cq.Workplane:
    """Find face with normal closest to target normal."""
    best_face = None
    best_dot = -1.0
    
    for face in faces:
        normal = _get_face_normal(face)
        # Dot product (cosine of angle)
        dot = abs(normal[0] * target_normal[0] + normal[1] * target_normal[1] + normal[2] * target_normal[2])
        if dot > best_dot:
            best_dot = dot
            best_face = face
    
    return cq.Workplane(best_face if best_face else faces[0])


def _find_face_by_center(faces: list[cq.Face], target_center: tuple[float, float, float]) -> cq.Workplane:
    """Find face containing or closest to target center point."""
    best_face = None
    best_dist = float('inf')
    
    for face in faces:
        center = _get_face_center(face)
        dist = ((center[0] - target_center[0])**2 + 
                (center[1] - target_center[1])**2 + 
                (center[2] - target_center[2])**2)
        if dist < best_dist:
            best_dist = dist
            best_face = face
    
    return cq.Workplane(best_face if best_face else faces[0])


def _find_largest_face(faces: list[cq.Face]) -> cq.Workplane:
    """Find face with largest area."""
    best_face = None
    best_area = -1.0
    
    for face in faces:
        area = _get_face_area(face)
        if area > best_area:
            best_area = area
            best_face = face
    
    return cq.Workplane(best_face if best_face else faces[0])


def _find_smallest_face(faces: list[cq.Face]) -> cq.Workplane:
    """Find face with smallest area."""
    best_face = None
    best_area = float('inf')
    
    for face in faces:
        area = _get_face_area(face)
        if area < best_area:
            best_area = area
            best_face = face
    
    return cq.Workplane(best_face if best_face else faces[0])


def _find_face_by_position(faces: list[cq.Face], position: str) -> cq.Workplane:
    """Find face by semantic position (top, bottom, front, back, right, left)."""
    if not faces:
        return cq.Workplane("XY")
    
    # Get bounding box of all faces
    all_centers = [_get_face_center(f) for f in faces]
    if not all_centers:
        return cq.Workplane(faces[0])
    
    min_x = min(c[0] for c in all_centers)
    max_x = max(c[0] for c in all_centers)
    min_y = min(c[1] for c in all_centers)
    max_y = max(c[1] for c in all_centers)
    min_z = min(c[2] for c in all_centers)
    max_z = max(c[2] for c in all_centers)
    
    best_face = None
    best_score = float('inf') if position in ["top", "front", "right"] else float('-inf')
    
    for face in faces:
        center = _get_face_center(face)
        score = None
        
        if position == "top":
            score = center[2]  # Highest Z
        elif position == "bottom":
            score = -center[2]  # Lowest Z (negate for max)
        elif position == "front":
            score = center[1]  # Highest Y
        elif position == "back":
            score = -center[1]  # Lowest Y
        elif position == "right":
            score = center[0]  # Highest X
        elif position == "left":
            score = -center[0]  # Lowest X
        
        if score is not None:
            if position in ["top", "front", "right"]:
                if score > best_score:
                    best_score = score
                    best_face = face
            else:
                if score < best_score:
                    best_score = score
                    best_face = face
    
    return cq.Workplane(best_face if best_face else faces[0])


def _resolve_plane_to_workplane(plane_ref: str, part: Part, current_wp: cq.Workplane | None = None, feature_history: dict[str, cq.Workplane] = {}) -> cq.Workplane:
    """
    Resolve a plane reference to a CadQuery workplane.
    
    Args:
        plane_ref: Plane reference string (e.g., "front_plane", "face:feature_name")
        part: The part being built
        current_wp: Current workplane (for face references)
        feature_history: Dictionary of feature_name -> workplane for face references
        
    Returns:
        CadQuery workplane on the specified plane
    """
    # Standard planes
    if plane_ref == "front_plane" or plane_ref == "XY":
        return cq.Workplane("XY")
    elif plane_ref == "right_plane" or plane_ref == "YZ":
        return cq.Workplane("YZ")
    elif plane_ref == "top_plane" or plane_ref == "XZ":
        return cq.Workplane("XZ")
    
    # Face references: "face:feature_name" with various selection methods
    if plane_ref.startswith("face:"):
        parts = plane_ref.split(":")
        if len(parts) >= 2:
            feature_name = parts[1]
            
            # Get the workplane from the feature history
            if feature_name in feature_history:
                feature_wp = feature_history[feature_name]
                faces = feature_wp.faces().vals()
                
                if not faces:
                    # Fallback to the feature workplane itself
                    return feature_wp
                
                # If no selector specified, use default (first face)
                if len(parts) == 2:
                    return cq.Workplane(faces[0])
                
                # Parse selector
                selector = parts[2] if len(parts) >= 3 else None
                
                # Index selector: "face:feature_name:index:0"
                if selector == "index" and len(parts) >= 4:
                    try:
                        face_index = int(parts[3])
                        if 0 <= face_index < len(faces):
                            return cq.Workplane(faces[face_index])
                    except (ValueError, IndexError):
                        pass
                
                # Normal direction selector: "face:feature_name:normal:+X" or "face:feature_name:normal:[1,0,0]"
                elif selector == "normal" and len(parts) >= 4:
                    normal_spec = parts[3]
                    target_normal = _parse_normal_spec(normal_spec)
                    if target_normal:
                        return _find_face_by_normal(faces, target_normal)
                
                # Center point selector: "face:feature_name:center:[5,5,10]"
                elif selector == "center" and len(parts) >= 4:
                    try:
                        # Parse center point from string like "[5,5,10]"
                        center_str = parts[3]
                        center = _parse_point_spec(center_str)
                        if center:
                            return _find_face_by_center(faces, center)
                    except:
                        pass
                
                # Semantic selectors
                elif selector == "largest":
                    return _find_largest_face(faces)
                elif selector == "smallest":
                    return _find_smallest_face(faces)
                elif selector == "top":
                    return _find_face_by_position(faces, "top")
                elif selector == "bottom":
                    return _find_face_by_position(faces, "bottom")
                elif selector == "front":
                    return _find_face_by_position(faces, "front")
                elif selector == "back":
                    return _find_face_by_position(faces, "back")
                elif selector == "right":
                    return _find_face_by_position(faces, "right")
                elif selector == "left":
                    return _find_face_by_position(faces, "left")
                
                # Legacy: "face:feature_name:0" (index without "index:" prefix)
                elif selector.isdigit():
                    try:
                        face_index = int(selector)
                        if 0 <= face_index < len(faces):
                            return cq.Workplane(faces[face_index])
                    except (ValueError, IndexError):
                        pass
                
                # Default: use first face
                return cq.Workplane(faces[0])
    
    # Default fallback
    return cq.Workplane("XY")


def _resolve_extrude_distance(
    distance_param: str | float,
    part: Part,
    sketch_wp: cq.Workplane,
    current_wp: cq.Workplane,
    operation: str,
    direction: tuple[float, float, float]
) -> float:
    """
    Resolve extrude distance, handling "through_all" and "to_next" modes.
    
    Args:
        distance_param: Distance parameter (can be number, "through_all", "to_next", or param name)
        part: The part being built
        sketch_wp: Workplane of the sketch being extruded
        current_wp: Current workplane (for "to_next" calculation)
        operation: "join" or "cut"
        direction: Extrusion direction vector
        
    Returns:
        Resolved distance as float
    """
    if isinstance(distance_param, (int, float)):
        return float(distance_param)
    
    if isinstance(distance_param, str):
        # Special modes
        if distance_param == "through_all":
            # For cuts, extrude far enough to go through the entire body
            if operation == "cut" and current_wp.objects:
                # Get bounding box of current body
                solid = current_wp.val()
                bbox = solid.BoundingBox()
                # Calculate distance needed in the extrusion direction
                # For MVP, use the maximum dimension along the direction
                # In full implementation, would raycast along direction to find exit point
                max_dim = max(
                    abs(bbox.xmax - bbox.xmin) * abs(direction[0]) if abs(direction[0]) > 0.1 else abs(bbox.xmax - bbox.xmin),
                    abs(bbox.ymax - bbox.ymin) * abs(direction[1]) if abs(direction[1]) > 0.1 else abs(bbox.ymax - bbox.ymin),
                    abs(bbox.zmax - bbox.zmin) * abs(direction[2]) if abs(direction[2]) > 0.1 else abs(bbox.zmax - bbox.zmin)
                )
                # Add a safety margin
                return max_dim * 1.5 if max_dim > 0 else 100.0
            else:
                # For joins, use a reasonable default
                return 10.0
        
        elif distance_param == "to_next":
            # Extrude until hitting the next surface
            if operation == "cut" and current_wp.objects:
                # For MVP, use a large distance (in full implementation, would raycast)
                solid = current_wp.val()
                bbox = solid.BoundingBox()
                max_dim = max(
                    abs(bbox.xmax - bbox.xmin),
                    abs(bbox.ymax - bbox.ymin),
                    abs(bbox.zmax - bbox.zmin)
                )
                return max_dim  # Should hit the opposite face
            else:
                return 10.0
        
        # Try to resolve as parameter reference
        return resolve_param_value(part, distance_param)
    
    return 10.0  # Default fallback


def _get_extrude_direction(
    direction_param: str | list[float] | None,
    sketch_wp: cq.Workplane,
    operation: str
) -> tuple[float, float, float]:
    """
    Get extrude direction vector.
    
    Args:
        direction_param: Direction parameter ("normal", "reverse", [x, y, z], or None)
        sketch_wp: Workplane of the sketch
        operation: "join" or "cut" (affects default direction for cuts)
        
    Returns:
        Direction vector as (x, y, z)
    """
    if direction_param is None:
        # Default: use workplane normal
        # For MVP, assume Z direction (0, 0, 1) for XY plane
        if operation == "cut":
            # For cuts, default to negative normal (into the body)
            return (0, 0, -1)
        else:
            return (0, 0, 1)
    
    if isinstance(direction_param, str):
        if direction_param == "normal":
            # Use workplane normal (positive)
            return (0, 0, 1)
        elif direction_param == "reverse":
            # Reverse of normal
            return (0, 0, -1)
    
    if isinstance(direction_param, list) and len(direction_param) == 3:
        # Explicit direction vector
        return tuple(direction_param)
    
    # Default
    return (0, 0, 1) if operation == "join" else (0, 0, -1)


def build_cad_model(part: Part) -> cq.Workplane:
    """
    Build a CadQuery model from a Part IR.
    
    Args:
        part: The part IR to build
        
    Returns:
        cq.Workplane: The resulting CadQuery workplane with the solid
    """
    wp = cq.Workplane("XY")
    feature_history: dict[str, cq.Workplane] = {}  # Track workplanes by feature name
    
    # Process features in order
    # MVP: Only sketch and extrude features are supported
    for feature in part.features:
        if feature.type not in ["sketch", "extrude"]:
            raise ValueError(f"Feature type '{feature.type}' not supported in MVP. Only 'sketch' and 'extrude' are available.")
        
        if feature.type == "sketch":
            # Sketches don't build geometry directly - they're 2D profiles
            # Geometry is built when they're used in extrude features
            # For now, just skip (no-op)
            pass
        
        elif feature.type == "extrude":
            # Extrude a sketch into 3D
            sketch_ref = feature.params.get("sketch") or feature.params.get("sketch_name")
            distance_param = feature.params.get("distance") or feature.params.get("distance_param")
            operation = feature.params.get("operation", "join")  # "join" or "cut"
            direction_param = feature.params.get("direction")  # Optional: "normal", "reverse", [x, y, z]
            
            if not sketch_ref:
                raise ValueError(f"Extrude feature '{feature.name}' missing sketch reference")
            if not distance_param:
                raise ValueError(f"Extrude feature '{feature.name}' missing distance parameter")
            
            # Find the sketch (could be in part.sketches or embedded in a sketch feature)
            sketch = None
            if isinstance(sketch_ref, str):
                # Look for sketch by name
                for s in part.sketches:
                    if s.name == sketch_ref:
                        sketch = s
                        break
                # Also check sketch features
                if not sketch:
                    for f in part.features:
                        if f.type == "sketch" and f.sketch and f.name == sketch_ref:
                            sketch = f.sketch
                            break
            
            if not sketch:
                raise ValueError(f"Sketch '{sketch_ref}' not found for extrude feature '{feature.name}'")
            
            # Resolve sketch plane to workplane (handles face references)
            sketch_plane_wp = _resolve_plane_to_workplane(sketch.plane, part, wp, feature_history)
            
            # Get extrude direction first (needed for distance resolution)
            direction = _get_extrude_direction(direction_param, sketch_plane_wp, operation)
            
            # Resolve distance (handles "through_all", "to_next", etc.)
            distance = _resolve_extrude_distance(distance_param, part, sketch_plane_wp, wp, operation, direction)
            
            # Detect profiles if not already present
            if not sketch.profiles:
                sketch.profiles = detect_profiles(sketch)
            
            # Detect profiles if not already present
            if not sketch.profiles:
                sketch.profiles = detect_profiles(sketch)
            
            # Build 2D profile from detected profiles (outer boundary + holes)
            # Note: _build_profile_workplane uses the sketch's plane, but we need to use sketch_plane_wp
            extrude_wp = _build_profile_workplane_on_face(sketch, distance, sketch_plane_wp, direction)
            
            if not extrude_wp:
                raise ValueError(f"Sketch '{sketch_ref}' has no valid geometry for extrusion")
            
            if operation == "cut":
                # For cut, we need existing geometry
                if wp.objects:
                    wp = wp.cut(extrude_wp)
                else:
                    raise ValueError(f"Cannot cut from empty geometry in feature '{feature.name}'")
            else:  # join
                # For join, if wp is empty, just use the extrude_wp directly
                if wp.objects:
                    wp = wp.union(extrude_wp)
                else:
                    wp = extrude_wp
            
            # Store in feature history for future face references
            feature_history[feature.name] = wp
    
    return wp


def generate_mesh(part: Part, per_feature: bool = False) -> MeshData | MultiMeshData:
    """
    Generate mesh data from a Part IR.
    
    Args:
        part: The part IR to mesh
        per_feature: If True, generate mesh with faceToFeature mapping for selection
        
    Returns:
        MeshData or MultiMeshData: Mesh vertices and faces for frontend rendering
    """
    # Build the full model
    wp = build_cad_model(part)
    solid = wp.val()
    
    try:
        mesh = solid.tessellate(0.1)
        vertices = [[v.x, v.y, v.z] for v in mesh[0]]
        faces = []
        face_to_feature: list[str | None] = []
        
        # Convert triangles to face indices
        for tri in mesh[1]:
            if len(tri) == 3:
                faces.append([tri[0], tri[1], tri[2]])
                # For MVP: assign faces to features based on order
                # In a full implementation, we'd track which feature created which geometry
                if per_feature and part.features:
                    # Simple heuristic: assign faces to features in order
                    # This is a placeholder - proper implementation would track feature contributions
                    feature_index = min(len(faces) // (len(mesh[1]) // len(part.features) + 1), len(part.features) - 1)
                    face_to_feature.append(part.features[feature_index].name if feature_index < len(part.features) else None)
                else:
                    face_to_feature.append(None)
        
        if per_feature and face_to_feature:
            # Return as MultiMeshData format (single mesh with faceToFeature mapping)
            single_mesh = MeshData(vertices=vertices, faces=faces)
            multi = MultiMeshData([single_mesh], face_to_feature=face_to_feature)
            return multi
        else:
            return MeshData(vertices=vertices, faces=faces)
            
    except Exception as e:
        print(f"Warning: Mesh generation failed: {e}")
        return MeshData(vertices=[], faces=[])


def build_cad_model_up_to_feature(part: Part, feature_name: str) -> cq.Workplane:
    """
    Build CadQuery model up to and including a specific feature.
    Used for per-feature mesh generation.
    This is a simplified version - for MVP we use the full build_cad_model.
    """
    # For MVP, just build the full model
    # In a full implementation, this would build incrementally
    return build_cad_model(part)

