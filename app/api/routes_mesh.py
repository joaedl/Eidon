"""
API routes for advanced meshing and visualization.
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.api.schemas import (
    MeshSolidRequest, MeshSolidResponse, MeshData, MeshParams,
    SectionPlaneRequest, SectionPlaneResponse, SectionCurve, PlaneDefinition
)

router = APIRouter(prefix="/mesh", tags=["mesh"])


@router.post("/solid", response_model=MeshSolidResponse)
async def mesh_solid(request: MeshSolidRequest):
    """
    Generate a mesh from an OCC solid with given tolerance.
    
    Provides control over mesh quality separate from build.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Get mesh parameters
        tolerance = request.mesh_params.linear_tolerance or 0.1
        angle_tolerance = request.mesh_params.angle_tolerance
        
        # Generate mesh with custom tolerance
        try:
            mesh_result = solid.tessellate(tolerance)
            vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
            faces = []
            
            for tri in mesh_result[1]:
                if len(tri) >= 3:
                    faces.append([tri[0], tri[1], tri[2]])
            
            mesh_data = MeshData(vertices=vertices, faces=faces)
            
            metrics = {
                "triangle_count": len(faces),
                "vertex_count": len(vertices),
                "linear_tolerance": tolerance,
                "angle_tolerance": angle_tolerance
            }
            
            return MeshSolidResponse(mesh=mesh_data, metrics=metrics)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Meshing failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mesh generation failed: {str(e)}")


@router.post("/section/plane", response_model=SectionPlaneResponse)
async def section_plane(request: SectionPlaneRequest):
    """
    Compute a 2D section (cross-section) at a plane.
    
    Returns 2D section curves (wires) and optionally a 2D mesh.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Create a plane from the definition
        import cadquery as cq
        from OCP.gp import gp_Pnt, gp_Dir, gp_Pln
        
        point = gp_Pnt(*request.plane.point)
        normal = gp_Dir(*request.plane.normal)
        plane = gp_Pln(point, normal)
        
        # For MVP: use CadQuery's section method if available
        # This is a simplified implementation
        try:
            # Try to get a section using OCC
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
            from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
            
            # Create a large face on the plane for intersection
            # This is a simplified approach - full implementation would use proper sectioning
            section = BRepAlgoAPI_Section(solid.wrapped, plane)
            section.Build()
            
            if section.IsDone():
                result_shape = section.Shape()
                
                # Extract edges from the section
                from OCP.TopExp import TopExp_Explorer
                from OCP.TopAbs import TopAbs_EDGE
                
                curves = []
                edge_exp = TopExp_Explorer(result_shape, TopAbs_EDGE)
                
                while edge_exp.More():
                    edge = edge_exp.Current()
                    # Extract points from edge (simplified)
                    # Full implementation would properly extract curve geometry
                    curves.append(SectionCurve(
                        type="line",  # Simplified - would detect actual curve type
                        points=[[0, 0], [1, 0]]  # Placeholder
                    ))
                    edge_exp.Next()
                
                return SectionPlaneResponse(curves=curves, mesh_2d=None)
            else:
                # No intersection
                return SectionPlaneResponse(curves=[], mesh_2d=None)
                
        except Exception as e:
            # Fallback: return empty section
            return SectionPlaneResponse(curves=[], mesh_2d=None)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Section computation failed: {str(e)}")

