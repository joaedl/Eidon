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
    
    def __init__(self, vertices: list[list[float]], faces: list[list[int]]):
        self.vertices = vertices  # List of [x, y, z] coordinates
        self.faces = faces  # List of face indices (triangles: [i, j, k])
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "vertices": self.vertices,
            "faces": self.faces
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
    
    return wp


def generate_mesh(part: Part) -> MeshData:
    """
    Generate mesh data from a Part IR.
    
    Args:
        part: The part IR to mesh
        
    Returns:
        MeshData: Mesh vertices and faces for frontend rendering
    """
    # Build the CadQuery model
    wp = build_cad_model(part)
    
    # Get the solid
    solid = wp.val()
    
    # Export to mesh format
    # CadQuery can export to STL or we can use the underlying OCC mesh
    # For simplicity, we'll use CadQuery's tessellation
    try:
        # Get tessellated mesh from the solid
        mesh = solid.tessellate(0.1)  # 0.1 is tolerance
        
        # Extract vertices and faces
        vertices = [[v.x, v.y, v.z] for v in mesh[0]]
        faces = []
        
        # Convert triangles to face indices
        # mesh[1] contains the triangle indices
        for tri in mesh[1]:
            if len(tri) == 3:
                faces.append([tri[0], tri[1], tri[2]])
        
        return MeshData(vertices=vertices, faces=faces)
        
    except Exception as e:
        # Fallback: create a simple box if tessellation fails
        print(f"Warning: Mesh generation failed: {e}")
        # Return empty mesh for now
        return MeshData(vertices=[], faces=[])

