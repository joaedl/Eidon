"""
API routes for part templates.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part
from app.core.dsl_parser import parse_dsl_to_ir

router = APIRouter(prefix="/models", tags=["templates"])


class NewPartRequest(BaseModel):
    """Request body for creating a new part from template."""
    template: str  # Template name, e.g., "shaft", "shaft_with_flange"


class NewPartResponse(BaseModel):
    """Response from new part endpoint."""
    dsl: str
    part: dict  # Part IR as JSON dict


# Template DSL definitions
TEMPLATES = {
    "shaft": """part shaft {
  param dia = 20 mm tolerance g6
  param length = 80 mm

  feature base = cylinder(dia_param=dia, length_param=length)
  feature chamfer_end = chamfer(edge="end", size=1)

  chain length_chain {
    terms = [length]
  }
}""",
    
    "shaft_with_flange": """part shaft_with_flange {
  param shaft_dia = 20 mm tolerance g6
  param shaft_length = 80 mm
  param flange_dia = 60 mm
  param flange_thickness = 10 mm

  feature shaft = cylinder(dia_param=shaft_dia, length_param=shaft_length)
  feature flange_1 = cylinder(dia_param=flange_dia, length_param=flange_thickness)

  chain length_chain {
    terms = [shaft_length]
  }
}""",
    
    "robot_leg": """part robot_leg {
  param hip_to_knee_distance = 320 mm
  param lateral_offset = 15 mm
  param interface_dia = 40 mm
  param interface_hole_dia = 6 mm
  param interface_thickness = 10 mm
  param link_width = 40 mm
  param link_height = 60 mm
  param link_thickness = 4 mm

  feature hip_mount = joint_interface(
    dia=interface_dia,
    hole_dia=interface_hole_dia,
    holes=4,
    thickness=interface_thickness
  )

  feature knee_mount = joint_interface(
    dia=interface_dia,
    hole_dia=interface_hole_dia,
    holes=4,
    thickness=interface_thickness
  )
}"""
}


@router.post("/new")
async def create_new_part(request: NewPartRequest) -> NewPartResponse:
    """
    Create a new part from a template.
    
    Returns the DSL and parsed Part IR.
    """
    if request.template not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template: {request.template}. Available: {list(TEMPLATES.keys())}"
        )
    
    try:
        dsl = TEMPLATES[request.template]
        part = parse_dsl_to_ir(dsl)
        
        return NewPartResponse(
            dsl=dsl,
            part=part.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create part from template: {str(e)}")


@router.get("/templates")
async def list_templates() -> dict[str, list[str]]:
    """List available part templates."""
    return {"templates": list(TEMPLATES.keys())}

