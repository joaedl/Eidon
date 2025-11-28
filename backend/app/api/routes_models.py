"""
API routes for model management: DSL parsing and geometry building.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part, ValidationIssue
from app.core.dsl_parser import parse_dsl_to_ir
from app.core.builder import generate_mesh, MultiMeshData
from app.core.analysis import evaluate_all_params, evaluate_all_chains, validate_part
from app.core.operations import apply_operations, Operation, SetParameter, UpdateParameterTolerance

router = APIRouter(prefix="/models", tags=["models"])


class DSLRequest(BaseModel):
    """Request body for DSL parsing."""
    dsl: str


class RebuildRequest(BaseModel):
    """Request body for rebuilding geometry from IR."""
    part: dict  # Part IR as JSON dict


class RebuildResponse(BaseModel):
    """Response from rebuild endpoint."""
    mesh: dict
    params_eval: dict[str, dict[str, float]]
    chains_eval: dict[str, dict[str, float]]
    issues: list[dict]  # ValidationIssue as dict


@router.post("/from-dsl")
async def parse_dsl(request: DSLRequest) -> dict:
    """
    Parse DSL text into Part IR.
    
    Returns the Part IR as JSON.
    """
    try:
        part = parse_dsl_to_ir(request.dsl)
        return part.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DSL parsing failed: {str(e)}")


@router.post("/rebuild")
async def rebuild_model(request: RebuildRequest) -> RebuildResponse:
    """
    Rebuild geometry and analysis from Part IR.
    
    Returns mesh data, evaluated parameters, evaluated chains, and validation issues.
    """
    try:
        # Parse Part from dict
        part = Part.model_validate(request.part)
        
        # Generate mesh with per-feature metadata for selection
        mesh_data = generate_mesh(part, per_feature=True)
        
        # Convert to dict (handles both MeshData and MultiMeshData)
        if isinstance(mesh_data, MultiMeshData):
            mesh_dict = mesh_data.to_dict()
        else:
            mesh_dict = mesh_data.to_dict()
        
        # Evaluate parameters and chains
        params_eval = evaluate_all_params(part)
        chains_eval = evaluate_all_chains(part)
        
        # Validate part
        issues = validate_part(part)
        
        return RebuildResponse(
            mesh=mesh_dict,
            params_eval=params_eval,
            chains_eval=chains_eval,
            issues=[issue.model_dump() for issue in issues]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rebuild failed: {str(e)}")

