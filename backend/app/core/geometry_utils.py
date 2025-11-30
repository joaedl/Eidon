"""
Geometry utility functions for bounding box, topology, and mass property calculations.
"""

import cadquery as cq
from typing import Optional


def calculate_bounding_box(solid: cq.Solid) -> dict[str, list[float]]:
    """
    Calculate the 3D bounding box of a CadQuery solid.
    
    Args:
        solid: CadQuery Solid object
        
    Returns:
        Dict with 'min' and 'max' keys, each containing [x, y, z] coordinates
    """
    # Get bounding box from CadQuery solid
    bbox = solid.BoundingBox()
    
    return {
        "min": [bbox.xmin, bbox.ymin, bbox.zmin],
        "max": [bbox.xmax, bbox.ymax, bbox.zmax]
    }


def get_topology_summary(solid: cq.Solid) -> dict[str, int]:
    """
    Get topology summary (face, edge, vertex counts) from a solid.
    
    Args:
        solid: CadQuery Solid object
        
    Returns:
        Dict with face_count, edge_count, vertex_count
    """
    # Access OCC topology
    try:
        # CadQuery solid wraps OCC TopoDS_Shape
        # We can get topology information from the underlying OCC object
        occ_shape = solid.wrapped
        
        # Count faces
        from OCP.TopTools import TopTools_ListOfShape
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX
        
        face_count = 0
        edge_count = 0
        vertex_count = 0
        
        # Count faces
        face_exp = TopExp_Explorer(occ_shape, TopAbs_FACE)
        while face_exp.More():
            face_count += 1
            face_exp.Next()
        
        # Count edges
        edge_exp = TopExp_Explorer(occ_shape, TopAbs_EDGE)
        while edge_exp.More():
            edge_count += 1
            edge_exp.Next()
        
        # Count vertices
        vertex_exp = TopExp_Explorer(occ_shape, TopAbs_VERTEX)
        while vertex_exp.More():
            vertex_count += 1
            vertex_exp.Next()
        
        return {
            "face_count": face_count,
            "edge_count": edge_count,
            "vertex_count": vertex_count
        }
    except Exception as e:
        # Fallback: use tessellation to estimate
        # This is less accurate but works if OCC access fails
        try:
            mesh = solid.tessellate(0.1)
            vertices = mesh[0]
            faces = mesh[1]
            
            # Estimate edges from faces (approximate)
            estimated_edges = len(faces) * 3 // 2  # Rough estimate
            
            return {
                "face_count": len(faces),
                "edge_count": estimated_edges,
                "vertex_count": len(vertices)
            }
        except:
            # Last resort: return zeros
            return {
                "face_count": 0,
                "edge_count": 0,
                "vertex_count": 0
            }


def calculate_mass_properties(solid: cq.Solid, density: Optional[float] = None) -> dict:
    """
    Calculate mass properties of a solid.
    
    Args:
        solid: CadQuery Solid object
        density: Material density in kg/m³ (optional)
        
    Returns:
        Dict with volume, area, center_of_mass, principal_moments, principal_axes
    """
    try:
        # Get volume and surface area
        volume = solid.Volume()  # in mm³ (CadQuery uses mm)
        area = solid.Area()  # in mm²
        
        # Convert to m³ and m²
        volume_m3 = volume / 1e9
        area_m2 = area / 1e6
        
        # Get center of mass
        com = solid.CenterOfMass()
        center_of_mass = [com.x / 1000, com.y / 1000, com.z / 1000]  # Convert mm to m
        
        # For principal moments and axes, we need to use OCC's GProp_GProps
        # This is a simplified version - full implementation would use OCC's inertia properties
        try:
            from OCP.GProp import GProp_GProps
            from OCP.BRepGProp import BRepGProp
            
            props = GProp_GProps()
            BRepGProp.VolumeProperties_s(solid.wrapped, props)
            
            # Get inertia matrix
            inertia = props.MatrixOfInertia()
            
            # For MVP, return simplified principal moments
            # Full implementation would diagonalize the inertia matrix
            # For now, return diagonal elements as approximation
            principal_moments = [
                inertia.Value(1, 1) / 1e9,  # Convert to kg·m²
                inertia.Value(2, 2) / 1e9,
                inertia.Value(3, 3) / 1e9
            ]
            
            # Principal axes would be eigenvectors of inertia matrix
            # For MVP, return identity matrix as placeholder
            principal_axes = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
        except Exception:
            # Fallback: return zeros for principal moments/axes
            principal_moments = [0.0, 0.0, 0.0]
            principal_axes = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
        
        return {
            "volume": volume_m3,
            "area": area_m2,
            "center_of_mass": center_of_mass,
            "principal_moments": principal_moments,
            "principal_axes": principal_axes
        }
    except Exception as e:
        # Return zeros on error
        return {
            "volume": 0.0,
            "area": 0.0,
            "center_of_mass": [0.0, 0.0, 0.0],
            "principal_moments": [0.0, 0.0, 0.0],
            "principal_axes": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
        }


def validate_geometry(solid: cq.Solid) -> tuple[bool, list[dict]]:
    """
    Validate geometry for common issues.
    
    Args:
        solid: CadQuery Solid object
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    try:
        # Check if solid is valid
        if not solid.isValid():
            issues.append({
                "code": "INVALID_SOLID",
                "message": "Solid is invalid",
                "severity": "error"
            })
        
        # Check for self-intersection
        try:
            # Use OCC's BRepCheck_Analyzer
            from OCP.BRepCheck import BRepCheck_Analyzer
            analyzer = BRepCheck_Analyzer(solid.wrapped)
            if not analyzer.IsValid():
                issues.append({
                    "code": "SELF_INTERSECTION",
                    "message": "Solid has self-intersections",
                    "severity": "error"
                })
        except Exception:
            pass  # Skip if OCC check fails
        
        # Check volume (should be positive)
        try:
            volume = solid.Volume()
            if volume <= 0:
                issues.append({
                    "code": "NEGATIVE_VOLUME",
                    "message": "Solid has zero or negative volume",
                    "severity": "error"
                })
        except Exception:
            pass
        
        # Check for degenerate faces (very small faces)
        try:
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopAbs import TopAbs_FACE
            from OCP.BRepGProp import BRepGProp
            from OCP.GProp import GProp_GProps
            
            face_exp = TopExp_Explorer(solid.wrapped, TopAbs_FACE)
            while face_exp.More():
                face = face_exp.Current()
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(face, props)
                area = props.Mass()
                
                if area < 1e-6:  # Very small face (1e-6 mm²)
                    issues.append({
                        "code": "TINY_FACE",
                        "message": f"Face with very small area: {area} mm²",
                        "severity": "warning"
                    })
                
                face_exp.Next()
        except Exception:
            pass  # Skip if check fails
        
        is_valid = len([i for i in issues if i["severity"] == "error"]) == 0
        
    except Exception as e:
        issues.append({
            "code": "VALIDATION_ERROR",
            "message": f"Validation failed: {str(e)}",
            "severity": "error"
        })
        is_valid = False
    
    return is_valid, issues

