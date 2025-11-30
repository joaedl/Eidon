"""
API routes for building geometry from IR (solids and sketches).
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part, Sketch
from app.core.builder import build_cad_model, generate_mesh
from app.core.geometry_utils import calculate_bounding_box, get_topology_summary
from app.api.schemas import (
    BuildSolidRequest, BuildSolidResponse, BoundingBox, TopologySummary, MeshData,
    BuildSketchRequest, BuildSketchResponse, Curve2D, ConstraintStatus,
    BuildFeatureRequest, BuildFeatureResponse
)

router = APIRouter(prefix="/build", tags=["build"])


@router.post("/solid", response_model=BuildSolidResponse)
async def build_solid(request: BuildSolidRequest):
    """
    Build a full solid for a single part from IR.
    
    Input:
    - part_ir: Part IR as JSON
    - detail_level: "coarse" | "normal" | "high" (affects tessellation)
    - return_mesh: bool (whether to return mesh data)
    
    Output:
    - mesh: Mesh data (if return_mesh=True)
    - bounding_box: 3D bounding box
    - topology_summary: Face/edge/vertex counts
    - status: Build status
    - warnings: List of warnings
    """
    try:
        # Parse Part IR
        part = Part.model_validate(request.part_ir)
        
        # Build CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Calculate bounding box
        bbox_dict = calculate_bounding_box(solid)
        bbox = BoundingBox(min=bbox_dict["min"], max=bbox_dict["max"])
        
        # Get topology summary
        topo_dict = get_topology_summary(solid)
        topology = TopologySummary(
            face_count=topo_dict["face_count"],
            edge_count=topo_dict["edge_count"],
            vertex_count=topo_dict["vertex_count"]
        )
        
        # Generate mesh if requested
        mesh_data = None
        if request.return_mesh:
            # Map detail_level to tessellation tolerance
            tolerance_map = {
                "coarse": 0.5,
                "normal": 0.1,
                "high": 0.01
            }
            tolerance = tolerance_map.get(request.detail_level, 0.1)
            
            try:
                mesh_result = solid.tessellate(tolerance)
                vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
                faces = []
                
                for tri in mesh_result[1]:
                    if len(tri) >= 3:
                        faces.append([tri[0], tri[1], tri[2]])
                
                mesh_data = MeshData(vertices=vertices, faces=faces)
            except Exception as e:
                # Mesh generation failed, but we can still return other data
                warnings = [f"Mesh generation failed: {str(e)}"]
                return BuildSolidResponse(
                    mesh=None,
                    bounding_box=bbox,
                    topology_summary=topology,
                    status="partial",
                    warnings=warnings
                )
        
        return BuildSolidResponse(
            mesh=mesh_data,
            bounding_box=bbox,
            topology_summary=topology,
            status="ok",
            warnings=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Build failed: {str(e)}")


@router.post("/sketch", response_model=BuildSketchResponse)
async def build_sketch(request: BuildSketchRequest):
    """
    Evaluate a single sketch from IR, mainly for 2D view.
    
    Input:
    - sketch_ir: Sketch IR as JSON
    - resolve_constraints: bool (placeholder for MVP)
    - plane: Optional plane override
    
    Output:
    - curves: List of 2D curve representations
    - constraint_status: Constraint solving status
    - issues: Validation issues
    """
    try:
        # Parse Sketch IR
        sketch = Sketch.model_validate(request.sketch_ir)
        
        # Convert entities to 2D curves
        curves = []
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                curves.append(Curve2D(
                    type="line",
                    points=[list(entity.start), list(entity.end)]
                ))
            elif entity.type == "circle" and entity.center and entity.radius:
                curves.append(Curve2D(
                    type="circle",
                    points=[],
                    radius=entity.radius,
                    center=list(entity.center)
                ))
            elif entity.type == "rectangle" and entity.corner1 and entity.corner2:
                # Convert rectangle to 4 points
                c1 = entity.corner1
                c2 = entity.corner2
                points = [
                    [c1[0], c1[1]],
                    [c2[0], c1[1]],
                    [c2[0], c2[1]],
                    [c1[0], c2[1]]
                ]
                curves.append(Curve2D(
                    type="rectangle",
                    points=points
                ))
        
        # Basic constraint validation (MVP: simplified)
        # Count constraints and entities to estimate DOF
        num_entities = len(sketch.entities)
        num_constraints = len(sketch.constraints)
        num_dimensions = len(sketch.dimensions)
        
        # Rough DOF estimate: 2 DOF per entity point, minus constraints/dimensions
        # This is a simplification - proper constraint solving would be more accurate
        estimated_dof = num_entities * 4 - num_constraints - num_dimensions  # Rough estimate
        
        is_fully_constrained = estimated_dof <= 0
        is_overconstrained = estimated_dof < 0
        
        constraint_status = ConstraintStatus(
            is_fully_constrained=is_fully_constrained,
            is_overconstrained=is_overconstrained,
            degrees_of_freedom=estimated_dof if estimated_dof > 0 else None
        )
        
        # Check for issues
        issues = []
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                # Check for zero-length lines
                dx = entity.end[0] - entity.start[0]
                dy = entity.end[1] - entity.start[1]
                length = (dx**2 + dy**2)**0.5
                if length < 1e-6:
                    issues.append({
                        "code": "ZERO_LENGTH_SEGMENT",
                        "message": f"Line entity {entity.id} has zero length",
                        "severity": "warning"
                    })
            elif entity.type == "circle" and entity.radius:
                if entity.radius <= 0:
                    issues.append({
                        "code": "INVALID_CIRCLE",
                        "message": f"Circle entity {entity.id} has non-positive radius",
                        "severity": "error"
                    })
        
        return BuildSketchResponse(
            curves=curves,
            constraint_status=constraint_status,
            issues=issues
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sketch build failed: {str(e)}")


@router.post("/feature", response_model=BuildFeatureResponse)
async def build_feature(request: BuildFeatureRequest):
    """
    Build geometry for one feature inside a part.
    
    Used for preview, highlighting, and feature-level tools.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Find the feature
        feature = None
        for f in part.features:
            if f.name == request.feature_id:
                feature = f
                break
        
        if not feature:
            raise HTTPException(status_code=404, detail=f"Feature '{request.feature_id}' not found")
        
        # For MVP: build up to this feature
        # In a full implementation, we'd build incrementally
        # For now, we build the full model and extract feature-specific geometry
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Generate mesh
        try:
            mesh_result = solid.tessellate(0.1)
            vertices = [[v.x, v.y, v.z] for v in mesh_result[0]]
            faces = []
            
            for tri in mesh_result[1]:
                if len(tri) >= 3:
                    faces.append([tri[0], tri[1], tri[2]])
            
            mesh_data = MeshData(vertices=vertices, faces=faces, featureId=feature.name)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Mesh generation failed: {str(e)}")
        
        # Calculate bounding box
        from app.core.geometry_utils import calculate_bounding_box
        bbox_dict = calculate_bounding_box(solid)
        bbox = BoundingBox(min=bbox_dict["min"], max=bbox_dict["max"])
        
        # Find dependencies (features that come before this one)
        depends_on = []
        for f in part.features:
            if f.name == feature.name:
                break
            depends_on.append(f.name)
        
        return BuildFeatureResponse(
            mesh=mesh_data,
            bounding_box=bbox,
            affected_region=None,  # Could be enhanced
            depends_on_features=depends_on
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature build failed: {str(e)}")

