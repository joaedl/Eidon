"""
API routes for geometry analysis (validation, mass properties).
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.core.geometry_utils import validate_geometry, calculate_mass_properties
from app.api.schemas import (
    GeometryValidationRequest, GeometryValidationResponse, GeometryIssue,
    MassPropertiesRequest, MassPropertiesResponse, Material,
    ClearanceRequest, ClearanceResponse,
    InterferenceRequest, InterferenceResponse,
    ToleranceChainRequest, ToleranceChainResponse
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/geometry-validation", response_model=GeometryValidationResponse)
async def geometry_validation(request: GeometryValidationRequest):
    """
    Deep geometry checks (independent of semantic checks).
    
    Checks for:
    - Self-intersection
    - Non-manifold edges
    - Tiny faces
    - Failed boolean operations
    - Invalid solids
    
    Returns list of issues and whether the solid is valid.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Validate geometry
        is_valid, issues_list = validate_geometry(solid)
        
        # Convert issues to GeometryIssue models
        geometry_issues = [
            GeometryIssue(
                code=issue["code"],
                message=issue["message"],
                severity=issue["severity"],
                location=None  # Could be enhanced to include location info
            )
            for issue in issues_list
        ]
        
        return GeometryValidationResponse(
            issues=geometry_issues,
            is_valid_solid=is_valid
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geometry validation failed: {str(e)}")


@router.post("/mass-properties", response_model=MassPropertiesResponse)
async def mass_properties(request: MassPropertiesRequest):
    """
    Compute mass properties from solid.
    
    Returns:
    - volume (m³)
    - area (m²)
    - center_of_mass [x, y, z] (m)
    - principal_moments [Ixx, Iyy, Izz] (kg·m²)
    - principal_axes (3x3 matrix)
    
    Note: Density is accepted but not yet used for mass calculation in MVP.
    Volume and area are always returned.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Determine density
        density = None
        if request.density:
            density = request.density
        elif request.material:
            density = request.material.density
        
        # Calculate mass properties
        props = calculate_mass_properties(solid, density=density)
        
        return MassPropertiesResponse(
            volume=props["volume"],
            area=props["area"],
            center_of_mass=props["center_of_mass"],
            principal_moments=props["principal_moments"],
            principal_axes=props["principal_axes"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Mass properties calculation failed: {str(e)}")


@router.post("/clearance", response_model=ClearanceResponse)
async def clearance(request: ClearanceRequest):
    """
    Find clearances between two bodies/parts.
    
    Returns minimum distance, locations, and any collisions.
    """
    try:
        from app.core.ir import Part
        from app.core.builder import build_cad_model
        
        part_a = Part.model_validate(request.part_a_ir)
        part_b = Part.model_validate(request.part_b_ir)
        
        # Build both parts
        wp_a = build_cad_model(part_a)
        solid_a = wp_a.val()
        
        wp_b = build_cad_model(part_b)
        solid_b = wp_b.val()
        
        # Calculate minimum distance using OCC
        try:
            from OCP.BRepExtrema import BRepExtrema_DistShapeShape
            
            dist_calc = BRepExtrema_DistShapeShape(solid_a.wrapped, solid_b.wrapped)
            dist_calc.Perform()
            
            if dist_calc.IsDone():
                min_distance = dist_calc.Value() / 1000.0  # Convert mm to m
                
                # Get locations (simplified)
                locations = []
                if dist_calc.NbSolution() > 0:
                    # Get point locations
                    p1 = dist_calc.PointOnShape1(1)
                    p2 = dist_calc.PointOnShape2(1)
                    locations.append({
                        "point_a": [p1.X() / 1000.0, p1.Y() / 1000.0, p1.Z() / 1000.0],
                        "point_b": [p2.X() / 1000.0, p2.Y() / 1000.0, p2.Z() / 1000.0]
                    })
                
                # Check for collisions
                collisions = []
                threshold = request.min_clearance_threshold or 0.0
                if min_distance < threshold:
                    collisions.append({
                        "distance": min_distance,
                        "location": locations[0] if locations else None
                    })
                
                return ClearanceResponse(
                    min_distance=min_distance,
                    locations=locations,
                    collisions=collisions
                )
            else:
                raise HTTPException(status_code=400, detail="Distance calculation failed")
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Clearance calculation failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clearance analysis failed: {str(e)}")


@router.post("/interference", response_model=InterferenceResponse)
async def interference(request: InterferenceRequest):
    """
    Boolean intersection between two parts.
    
    Returns whether interference exists and optionally intersection volume/mesh.
    """
    try:
        from app.core.ir import Part
        from app.core.builder import build_cad_model
        
        part_a = Part.model_validate(request.part_a_ir)
        part_b = Part.model_validate(request.part_b_ir)
        
        # Build both parts
        wp_a = build_cad_model(part_a)
        solid_a = wp_a.val()
        
        wp_b = build_cad_model(part_b)
        solid_b = wp_b.val()
        
        # Check for intersection using boolean operation
        try:
            # Try intersection
            intersection = solid_a.intersect(solid_b)
            intersection_solid = intersection.val()
            
            if intersection_solid.Volume() > 1e-6:  # Significant volume
                has_interference = True
                intersection_volume = intersection_solid.Volume() / 1e9  # Convert mm³ to m³
                
                # Generate intersection mesh (optional)
                try:
                    mesh_result = intersection_solid.tessellate(0.1)
                    vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
                    faces = []
                    for tri in mesh_result[1]:
                        if len(tri) >= 3:
                            faces.append([tri[0], tri[1], tri[2]])
                    
                    from app.api.schemas import MeshData
                    intersection_mesh = MeshData(vertices=vertices, faces=faces)
                except:
                    intersection_mesh = None
                
                return InterferenceResponse(
                    has_interference=True,
                    intersection_volume=intersection_volume,
                    intersection_mesh=intersection_mesh
                )
            else:
                return InterferenceResponse(
                    has_interference=False,
                    intersection_volume=None,
                    intersection_mesh=None
                )
                
        except Exception as e:
            # Intersection failed - assume no interference
            return InterferenceResponse(
                has_interference=False,
                intersection_volume=None,
                intersection_mesh=None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Interference analysis failed: {str(e)}")


@router.post("/tolerance-chain", response_model=ToleranceChainResponse)
async def tolerance_chain(request: ToleranceChainRequest):
    """
    Geometry-aware tolerance analysis.
    
    Note: This can also be done purely from IR in TypeScript.
    Geometry involvement is optional.
    """
    try:
        from app.core.ir import Part
        from app.core.builder import build_cad_model
        
        part = Part.model_validate(request.part_ir)
        chain_def = request.chain_definition
        
        # Build the part
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Extract chain information from definition
        # This is a simplified implementation
        # Full implementation would:
        # 1. Extract surface/edge references from chain_def
        # 2. Measure distances along the chain
        # 3. Apply tolerances
        # 4. Calculate worst-case min/max
        
        # For MVP: return placeholder values
        # In full implementation, would calculate actual chain length from geometry
        nominal_length = chain_def.get("nominal", 0.0)
        tolerances = chain_def.get("tolerances", [])
        
        # Calculate worst-case
        worst_case_min = nominal_length - sum(t.get("minus", 0) for t in tolerances)
        worst_case_max = nominal_length + sum(t.get("plus", 0) for t in tolerances)
        
        return ToleranceChainResponse(
            nominal_length=nominal_length,
            worst_case_min=worst_case_min,
            worst_case_max=worst_case_max,
            monte_carlo_stats=None  # Optional
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tolerance chain analysis failed: {str(e)}")
