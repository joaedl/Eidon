"""
API routes for LLM agent integration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from app.core.ir import Part
from app.core.llm_agent import run_agent, AgentMode, AgentScope, AgentResult
from app.core.operations import Operation

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentCommandRequest(BaseModel):
    """Request body for agent commands."""
    mode: Literal["create", "edit", "explain"]
    scope: dict[str, list[str]] = {}  # { "selected_feature_ids": [...], "selected_param_names": [...], "selected_chain_names": [...] }
    part: Optional[dict] = None  # Part IR as JSON dict (None for create mode)
    prompt: str


class AgentCommandResponse(BaseModel):
    """Response from agent command."""
    part: Optional[dict] = None  # Modified or new Part IR (None for explain mode)
    operations: list[dict] = []  # List of operations applied
    message: str
    success: bool


@router.post("/command")
async def agent_command(request: AgentCommandRequest) -> AgentCommandResponse:
    """
    Process an agent command using LLM.
    
    Modes:
    - "create": Create a new part from scratch
    - "edit": Modify an existing part
    - "explain": Explain the part without modifying it
    """
    try:
        # Parse part if provided
        part = None
        if request.part:
            part = Part.model_validate(request.part)
        
        # Build scope
        scope = AgentScope(
            selected_feature_ids=request.scope.get("selected_feature_ids", []),
            selected_param_names=request.scope.get("selected_param_names", []),
            selected_chain_names=request.scope.get("selected_chain_names", []),
        )
        
        # Run agent
        result: AgentResult = run_agent(
            mode=AgentMode(request.mode),
            scope=scope,
            part=part,
            user_prompt=request.prompt,
        )
        
        # Convert to response
        return AgentCommandResponse(
            part=result.part.model_dump() if result.part else None,
            operations=[op.model_dump() for op in result.operations],
            message=result.message,
            success=result.part is not None or request.mode == "explain"
        )
    except ValueError as e:
        # Handle missing API key or other configuration errors
        raise HTTPException(status_code=500, detail=f"Agent configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agent command failed: {str(e)}")

