"""
API routes for part templates.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part
from app.core.dsl_parser import parse_dsl_to_ir
from app.core.dsl_store import set_part

router = APIRouter(prefix="/models", tags=["templates"])


class NewPartRequest(BaseModel):
    """Request body for creating a new part from template."""
    template: str  # Template name, e.g., "shaft", "shaft_with_flange"


class NewPartResponse(BaseModel):
    """Response from new part endpoint."""
    dsl: str
    part: dict  # Part IR as JSON dict


# MVP: Templates disabled - start with empty DSL
TEMPLATES = {}


@router.post("/new")
async def create_new_part(request: NewPartRequest) -> NewPartResponse:
    """
    Create a new part with empty DSL.
    
    MVP: Templates disabled - always returns empty DSL.
    Returns the DSL and parsed Part IR.
    """
    try:
        # MVP: Always return empty DSL
        dsl = "part new_part {\n}"
        part = parse_dsl_to_ir(dsl)
        # Store in DSL store
        set_part(part, dsl)
        
        return NewPartResponse(
            dsl=dsl,
            part=part.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create new part: {str(e)}")


@router.get("/templates")
async def list_templates() -> dict[str, list[str]]:
    """List available part templates.
    
    MVP: Templates disabled - returns empty list.
    """
    return {"templates": []}

