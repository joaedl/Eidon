"""
API routes for semantic operations on Part IR.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from app.core.ir import Part, ValidationIssue
from app.core.operations import apply_operations, Operation, SetParameter, UpdateParameterTolerance, AddFeature
from app.core.ir import Feature
from app.core.builder import generate_mesh
from app.core.analysis import evaluate_all_params, evaluate_all_chains, validate_part

router = APIRouter(prefix="/models", tags=["operations"])


class ApplyOperationsRequest(BaseModel):
    """Request body for applying operations."""
    part: dict  # Part IR as JSON dict
    operations: list[dict]  # List of operation dicts


class ApplyOperationsResponse(BaseModel):
    """Response from apply-operations endpoint."""
    part: dict  # Updated Part IR
    mesh: dict
    params_eval: dict[str, dict[str, float]]
    chains_eval: dict[str, dict[str, float]]
    issues: list[dict]  # ValidationIssue as dict


def parse_operation(op_dict: dict) -> Operation:
    """
    Parse an operation dict into an Operation object.
    
    Expected formats:
    - {"type": "SetParameter", "name": "dia", "value": 22.0}
    - {"type": "UpdateParameterTolerance", "name": "dia", "tolerance_class": "H7"}
    - {"type": "AddFeature", "feature": {...}}
    """
    op_type = op_dict.get("type")
    
    if op_type == "SetParameter":
        return SetParameter(
            name=op_dict["name"],
            value=float(op_dict["value"])
        )
    elif op_type == "UpdateParameterTolerance":
        return UpdateParameterTolerance(
            name=op_dict["name"],
            tolerance_class=op_dict.get("tolerance_class")
        )
    elif op_type == "AddFeature":
        feature_dict = op_dict.get("feature")
        if not feature_dict:
            raise ValueError("AddFeature operation missing 'feature' field")
        feature = Feature.model_validate(feature_dict)
        return AddFeature(feature=feature)
    else:
        raise ValueError(f"Unknown operation type: {op_type}")


@router.post("/apply-operations")
async def apply_operations_endpoint(request: ApplyOperationsRequest) -> ApplyOperationsResponse:
    """
    Apply semantic operations to a Part IR.
    
    Returns updated Part, rebuilt mesh, analysis, and validation issues.
    """
    try:
        # Parse Part from dict
        part = Part.model_validate(request.part)
        
        # Parse operations
        ops = [parse_operation(op_dict) for op_dict in request.operations]
        
        # Apply operations
        updated_part = apply_operations(part, ops)
        
        # Generate mesh
        mesh_data = generate_mesh(updated_part)
        
        # Evaluate parameters and chains
        params_eval = evaluate_all_params(updated_part)
        chains_eval = evaluate_all_chains(updated_part)
        
        # Validate part
        issues = validate_part(updated_part)
        
        return ApplyOperationsResponse(
            part=updated_part.model_dump(),
            mesh=mesh_data.to_dict(),
            params_eval=params_eval,
            chains_eval=chains_eval,
            issues=[issue.model_dump() for issue in issues]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Apply operations failed: {str(e)}")

