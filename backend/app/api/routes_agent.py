"""
API routes for LLM agent integration (stubbed for MVP).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentCommandRequest(BaseModel):
    """Request body for agent commands."""
    part: dict  # Part IR as JSON dict
    prompt: str


class AgentCommandResponse(BaseModel):
    """Response from agent command."""
    part: dict  # Modified or same Part IR
    message: str
    success: bool


@router.post("/command")
async def agent_command(request: AgentCommandRequest) -> AgentCommandResponse:
    """
    Process an agent command (stubbed for MVP).
    
    In the future, this will:
    1. Send current IR + prompt to LLM
    2. Receive modified IR or commands
    3. Apply changes and return updated IR
    
    For MVP, just returns the same IR with a message.
    """
    try:
        # Validate that part is valid
        part = Part.model_validate(request.part)
        
        # Stub: return same part with message
        return AgentCommandResponse(
            part=part.model_dump(),
            message="Agent not implemented yet. This is a stub endpoint.",
            success=False
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agent command failed: {str(e)}")

