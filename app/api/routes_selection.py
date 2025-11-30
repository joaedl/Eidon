"""
API routes for selection mapping and topology utilities.
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.api.schemas import (
    MapPickRequest, MapPickResponse, PickRay,
    TopologyTaggingRequest, TopologyTaggingResponse
)

router = APIRouter(tags=["selection"])


@router.post("/selection/map-pick", response_model=MapPickResponse)
async def map_pick(request: MapPickRequest):
    """
    Map a 3D pick (ray) to topological elements and features.
    
    Useful for "click in 3D → know which feature/param to highlight".
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Create ray from request
        ray_origin = request.pick_ray.origin
        ray_dir = request.pick_ray.direction
        
        # For MVP: simplified ray casting
        # Full implementation would:
        # 1. Cast ray through solid
        # 2. Find intersection with faces/edges/vertices
        # 3. Map back to feature references
        
        try:
            from OCP.BRepExtrema import BRepExtrema_DistShapeShape
            from OCP.gp import gp_Pnt, gp_Lin, gp_Dir
            
            # Create ray as a line
            ray_point = gp_Pnt(*ray_origin)
            ray_direction = gp_Dir(*ray_dir)
            ray_line = gp_Lin(ray_point, ray_direction)
            
            # Find closest point on solid to ray
            # This is simplified - full implementation would find actual intersection
            dist_calc = BRepExtrema_DistShapeShape(solid.wrapped, ray_line)
            dist_calc.Perform()
            
            if dist_calc.IsDone() and dist_calc.NbSolution() > 0:
                # Found intersection (simplified)
                # In full implementation, would identify specific face/edge/vertex
                return MapPickResponse(
                    face_id="face_0",  # Placeholder
                    edge_id=None,
                    vertex_id=None,
                    feature_reference=None  # Could map to feature name
                )
            else:
                return MapPickResponse(
                    face_id=None,
                    edge_id=None,
                    vertex_id=None,
                    feature_reference=None
                )
        except Exception as e:
            # Fallback: return no pick
            return MapPickResponse(
                face_id=None,
                edge_id=None,
                vertex_id=None,
                feature_reference=None
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pick mapping failed: {str(e)}")


@router.post("/topology/tagging", response_model=TopologyTaggingResponse)
async def topology_tagging(request: TopologyTaggingRequest):
    """
    Maintain stable IDs for faces/edges between rebuilds.
    
    Maps old topology IDs to new topology IDs after geometry changes.
    """
    try:
        old_sig = request.old_solid_signature
        new_sig = request.new_solid_signature
        
        # MVP: Simplified topology mapping
        # Full implementation would:
        # 1. Compare solid signatures
        # 2. Use geometric hashing or feature-based matching
        # 3. Create mapping from old IDs to new IDs
        
        # For MVP: return empty mappings (assume no stable IDs)
        # In full implementation, would use sophisticated matching algorithms
        
        return TopologyTaggingResponse(
            face_mapping={},
            edge_mapping={},
            vertex_mapping={}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Topology tagging failed: {str(e)}")

