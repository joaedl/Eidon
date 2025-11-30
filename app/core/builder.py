"""
Geometry builder: converts IR (Part) to CadQuery models and meshes.

This module takes a Part IR object and builds the corresponding 3D geometry
using CadQuery, then exports it as mesh data for the frontend.
"""

import cadquery as cq
from typing import Any
from app.core.ir import Part, Feature, Param


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


def build_cad_model(part: Part) -> cq.Workplane:
    """
    Build a CadQuery model from a Part IR.
    
    Args:
        part: The part IR to build
        
    Returns:
        cq.Workplane: The resulting CadQuery workplane with the solid
    """
    wp = cq.Workplane("XY")
    
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
            
            distance = resolve_param_value(part, distance_param)
            
            # Build 2D profile from sketch entities
            # For MVP: convert sketch entities to CadQuery 2D workplane, then extrude
            sketch_wp = cq.Workplane("XY")  # Default plane, could be mapped from sketch.plane
            
            # Process entities to build the profile
            # For MVP, we'll create a simple closed profile from lines
            # In a full implementation, we'd use a proper constraint solver
            for entity in sketch.entities:
                if entity.type == "line" and entity.start and entity.end:
                    # Add line to sketch (simplified - in full impl, would build proper wire)
                    # For MVP, we'll create a rectangle from the bounding box
                    pass  # Placeholder
            
            # For MVP: create a simple box from sketch bounding box
            # Calculate bounding box from all entities (including rectangles and circles)
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            has_geometry = False
            
            for entity in sketch.entities:
                # Skip construction lines
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
                # Ensure minimum dimensions (avoid zero-size geometry)
                if width <= 0:
                    width = 1.0
                if height <= 0:
                    height = 1.0
                # Create a box from the bounding box (simplified for MVP)
                # In full implementation, would build proper wire from sketch entities
                extrude_wp = cq.Workplane("XY").rect(width, height).extrude(distance)
                
                if operation == "cut":
                    wp = wp.cut(extrude_wp)
                else:  # join
                    wp = wp.union(extrude_wp)
            else:
                raise ValueError(f"Sketch '{sketch_ref}' has no valid geometry for extrusion")
    
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

