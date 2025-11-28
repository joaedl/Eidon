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
    for feature in part.features:
        if feature.type == "cylinder":
            # Extract parameters
            dia_param = feature.params.get("dia_param") or feature.params.get("dia")
            length_param = feature.params.get("length_param") or feature.params.get("length")
            
            if not dia_param or not length_param:
                raise ValueError(f"Cylinder feature '{feature.name}' missing dia or length parameter")
            
            dia = resolve_param_value(part, dia_param)
            length = resolve_param_value(part, length_param)
            
            # Create cylinder
            wp = wp.cylinder(length, dia / 2.0)
            
        elif feature.type == "hole":
            # For MVP: simple through-hole at origin
            dia_param = feature.params.get("dia_param") or feature.params.get("dia")
            if not dia_param:
                raise ValueError(f"Hole feature '{feature.name}' missing dia parameter")
            
            dia = resolve_param_value(part, dia_param)
            
            # Create hole (subtract from current solid)
            wp = wp.faces(">Z").workplane().hole(dia)
            
        elif feature.type == "chamfer":
            # For MVP: chamfer on the end face
            size_param = feature.params.get("size_param") or feature.params.get("size")
            edge_ref = feature.params.get("edge")
            target_feature = feature.params.get("target_feature")
            
            if not size_param:
                raise ValueError(f"Chamfer feature '{feature.name}' missing size parameter")
            
            size = resolve_param_value(part, size_param)
            
            # Apply chamfer to the end face
            # edge_ref can be "end" (string literal) or a parameter name
            if edge_ref:
                # If it's a string that looks like a parameter name, try to resolve it
                # Otherwise treat it as a literal string like "end"
                if isinstance(edge_ref, str) and edge_ref not in ["end", "start"] and edge_ref in part.params:
                    edge_val = resolve_param_value(part, edge_ref)
                else:
                    edge_val = edge_ref
                
                if edge_val == "end" or str(edge_val) == "end":
                    # Chamfer the top edge
                    wp = wp.edges(">Z").chamfer(size)
                else:
                    # Default: chamfer all edges
                    wp = wp.edges().chamfer(size)
            else:
                # Default: chamfer all edges
                wp = wp.edges().chamfer(size)
        
        elif feature.type == "fillet":
            # Round/fillet edges
            radius_param = feature.params.get("radius") or feature.params.get("radius_param")
            target_feature = feature.params.get("target_feature")
            
            if not radius_param:
                raise ValueError(f"Fillet feature '{feature.name}' missing radius parameter")
            
            radius = resolve_param_value(part, radius_param)
            
            # Apply fillet to all edges (can be refined later)
            wp = wp.edges().fillet(radius)
        
        elif feature.type == "joint_interface":
            # Create a joint interface (bolt circle pattern)
            # For MVP: create a simple cylinder with holes
            dia_param = feature.params.get("dia") or feature.params.get("dia_param")
            hole_dia_param = feature.params.get("hole_dia") or feature.params.get("hole_dia_param")
            holes_param = feature.params.get("holes")
            thickness_param = feature.params.get("thickness") or feature.params.get("thickness_param", 10.0)
            
            if not dia_param:
                raise ValueError(f"Joint interface '{feature.name}' missing dia parameter")
            
            dia = resolve_param_value(part, dia_param)
            thickness = resolve_param_value(part, thickness_param) if thickness_param else 10.0
            
            # Create base cylinder for interface
            wp = wp.cylinder(thickness, dia / 2.0)
            
            # Add bolt holes if specified
            if hole_dia_param and holes_param:
                hole_dia = resolve_param_value(part, hole_dia_param)
                num_holes = int(holes_param) if isinstance(holes_param, (int, float)) else int(holes_param)
                bolt_circle_dia = dia * 0.7  # Bolt circle at 70% of interface diameter
                
                # Create bolt circle pattern
                for i in range(num_holes):
                    angle = (360.0 / num_holes) * i
                    import math
                    x = (bolt_circle_dia / 2.0) * math.cos(math.radians(angle))
                    y = (bolt_circle_dia / 2.0) * math.sin(math.radians(angle))
                    wp = wp.workplane(offset=thickness/2).center(x, y).hole(hole_dia)
        
        elif feature.type == "link_body":
            # Create a link body between two interfaces
            # For MVP: create a rectangular or tubular cross-section swept between interfaces
            section_type = feature.params.get("section_type", "rect")
            width_param = feature.params.get("width") or feature.params.get("width_param")
            height_param = feature.params.get("height") or feature.params.get("height_param")
            thickness_param = feature.params.get("thickness") or feature.params.get("thickness_param")
            from_interface = feature.params.get("from")
            to_interface = feature.params.get("to")
            
            if not width_param or not height_param:
                raise ValueError(f"Link body '{feature.name}' missing width or height parameter")
            
            width = resolve_param_value(part, width_param)
            height = resolve_param_value(part, height_param)
            thickness = resolve_param_value(part, thickness_param) if thickness_param else 4.0
            
            # For MVP: create a simple rectangular box positioned after previous features
            # In full implementation, would compute path between interfaces and sweep
            # For now, translate and create box
            if section_type == "rect":
                # Position the link body (simple translation for MVP)
                wp = wp.translate((0, 0, 0)).box(width, height, thickness)
            elif section_type == "tube":
                # Create a tube (hollow rectangle)
                outer_box = cq.Workplane("XY").box(width, height, thickness)
                inner_box = cq.Workplane("XY").box(width - 2*thickness, height - 2*thickness, thickness + 1)
                wp = outer_box.cut(inner_box)
            else:
                wp = wp.box(width, height, thickness)
        
        elif feature.type == "pocket":
            # Create a pocket (cutout) in a host feature
            host = feature.params.get("host")
            depth_param = feature.params.get("depth") or feature.params.get("depth_param")
            width_param = feature.params.get("width") or feature.params.get("width_param")
            height_param = feature.params.get("height") or feature.params.get("height_param")
            fillet_param = feature.params.get("fillet") or feature.params.get("fillet_param")
            
            if not depth_param or not width_param or not height_param:
                raise ValueError(f"Pocket '{feature.name}' missing required parameters")
            
            depth = resolve_param_value(part, depth_param)
            width = resolve_param_value(part, width_param)
            height = resolve_param_value(part, height_param)
            fillet = resolve_param_value(part, fillet_param) if fillet_param else 0.0
            
            # Create pocket as a cut
            pocket_wp = cq.Workplane("XY")
            if fillet > 0:
                # Rounded rectangle pocket
                pocket_wp = pocket_wp.rect(width, height).extrude(depth)
                # Apply fillet to edges (simplified)
            else:
                # Rectangular pocket
                pocket_wp = pocket_wp.rect(width, height).extrude(depth)
            
            # Cut the pocket from the current solid
            wp = wp.cut(pocket_wp)
    
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

