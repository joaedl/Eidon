"""
API routes for model management: DSL parsing and geometry building.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part
from app.core.dsl_parser import parse_dsl_to_ir
from app.core.builder import generate_mesh
from app.core.analysis import evaluate_all_params, evaluate_all_chains

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
    
    Returns mesh data, evaluated parameters, and evaluated chains.
    """
    try:
        # Parse Part from dict
        part = Part.model_validate(request.part)
        
        # Generate mesh
        mesh_data = generate_mesh(part)
        
        # Evaluate parameters and chains
        params_eval = evaluate_all_params(part)
        chains_eval = evaluate_all_chains(part)
        
        return RebuildResponse(
            mesh=mesh_data.to_dict(),
            params_eval=params_eval,
            chains_eval=chains_eval
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rebuild failed: {str(e)}")

