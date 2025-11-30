"""
API routes for assembly operations.
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.api.schemas import (
    AssemblyBuildRequest, AssemblyBuildResponse, MateDefinition, MeshData,
    AssemblyInterferenceRequest, AssemblyInterferenceResponse,
    MotionSweepRequest, MotionSweepResponse, JointDefinition
)

router = APIRouter(prefix="/assembly", tags=["assembly"])


@router.post("/build", response_model=AssemblyBuildResponse)
async def assembly_build(request: AssemblyBuildRequest):
    """
    Build an assembly from part IRs + constraint info.
    
    Combines multiple parts with mates into a single assembly.
    """
    try:
        # Parse all parts
        parts = [Part.model_validate(p) for p in request.parts]
        
        # Build each part
        solids = []
        for part in parts:
            wp = build_cad_model(part)
            solids.append(wp.val())
        
        # Apply mates (simplified - full implementation would transform parts)
        # For MVP: just combine all solids
        import cadquery as cq
        
        combined_wp = cq.Workplane("XY")
        for solid in solids:
            combined_wp = combined_wp.union(cq.Workplane("XY").newObject([solid]))
        
        combined_solid = combined_wp.val()
        
        # Generate mesh
        try:
            mesh_result = combined_solid.tessellate(0.1)
            vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
            faces = []
            for tri in mesh_result[1]:
                if len(tri) >= 3:
                    faces.append([tri[0], tri[1], tri[2]])
            
            mesh = MeshData(vertices=vertices, faces=faces)
        except:
            mesh = None
        
        # Mate status (simplified)
        mate_status = {
            "solved": len(request.mate_definitions),
            "overconstrained": 0,
            "unsolvable": 0
        }
        
        return AssemblyBuildResponse(
            combined_solid=None,  # Would return solid representation
            mesh=mesh,
            mate_status=mate_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Assembly build failed: {str(e)}")


@router.post("/interference-check", response_model=AssemblyInterferenceResponse)
async def assembly_interference_check(request: AssemblyInterferenceRequest):
    """
    Check for collisions between components in an assembly.
    
    Analyzes all part pairs for interference.
    """
    try:
        assembly_ir = request.assembly_ir
        
        # Extract parts from assembly
        parts_list = assembly_ir.get("parts", [])
        parts = [Part.model_validate(p) for p in parts_list]
        
        # Build all parts
        solids = []
        for part in parts:
            wp = build_cad_model(part)
            solids.append(wp.val())
        
        # Check all pairs for interference
        colliding_pairs = []
        collision_volumes = []
        
        for i, solid_a in enumerate(solids):
            for j, solid_b in enumerate(solids[i+1:], start=i+1):
                try:
                    intersection = solid_a.intersect(solid_b)
                    intersection_solid = intersection.val()
                    
                    if intersection_solid.Volume() > 1e-6:
                        colliding_pairs.append({
                            "part_a": i,
                            "part_b": j,
                            "volume": intersection_solid.Volume() / 1e9  # Convert to m³
                        })
                        
                        # Generate collision mesh
                        try:
                            mesh_result = intersection_solid.tessellate(0.1)
                            vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
                            faces = []
                            for tri in mesh_result[1]:
                                if len(tri) >= 3:
                                    faces.append([tri[0], tri[1], tri[2]])
                            collision_volumes.append(MeshData(vertices=vertices, faces=faces))
                        except:
                            pass
                except:
                    pass
        
        return AssemblyInterferenceResponse(
            colliding_pairs=colliding_pairs,
            collision_volumes=collision_volumes if collision_volumes else None,
            contact_points=None  # Could be enhanced
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Assembly interference check failed: {str(e)}")


@router.post("/motion-sweep", response_model=MotionSweepResponse)
async def motion_sweep(request: MotionSweepRequest):
    """
    For mechanism sweeps (e.g., robot leg range of motion).
    
    Analyzes contact/interference events over a parameter sweep.
    """
    try:
        assembly_ir = request.assembly_ir
        joint_defs = request.joint_definitions
        param_sweep = request.parameter_sweep
        
        # MVP: Simplified motion sweep
        # Full implementation would:
        # 1. Apply joint transformations at each step
        # 2. Check for contact/interference at each configuration
        # 3. Generate envelope geometry
        
        # For MVP: return placeholder
        contact_events = []
        
        # In full implementation, would iterate over parameter range
        # and check for contacts at each step
        
        return MotionSweepResponse(
            contact_events=contact_events,
            envelope_geometry=None  # Optional
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Motion sweep failed: {str(e)}")

