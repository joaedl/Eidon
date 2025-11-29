"""
API routes for LLM agent integration with intent-based dispatch.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, Any
from app.core.ir import Part, ValidationIssue
from app.core.llm_agent import run_agent, AgentMode, AgentScope, AgentResult
from app.core.operations import Operation
from app.core.dsl_generator import ir_to_dsl
from app.core.agent_intent import AgentIntent, IntentContext, detect_intent
from app.core.llm_agent_handlers import (
    handle_chat_model,
    handle_edit_dsl,
    handle_edit_sketch,
    # MVP: handle_edit_params and handle_generate_script disabled
    HandlerResult
)
from app.core.dsl_store import get_current_dsl, set_part, get_current_part
from app.core.llm_agent import summarize_part

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentCommandRequest(BaseModel):
    """Request body for agent commands."""
    prompt: str
    part: Optional[dict] = None  # Part IR as JSON dict
    selection: dict[str, Any] = {}  # Selection context (features, text range, etc.)
    auto_detect_intent: bool = True  # Whether to auto-detect intent or use explicit mode
    mode: Optional[Literal["create", "edit", "explain"]] = None  # Legacy mode (used if auto_detect_intent=False)


class AgentCommandResponse(BaseModel):
    """Response from agent command."""
    intent: str  # Detected or used intent
    part: Optional[dict] = None  # Modified or new Part IR
    dsl: Optional[str] = None  # Generated DSL code
    message: str
    success: bool
    validation_issues: list[dict] = []  # Validation issues
    script_code: Optional[str] = None  # For GENERATE_SCRIPT intent
    sketch: Optional[dict] = None  # For EDIT_SKETCH intent


def _build_part_summary(part: Part) -> dict[str, Any]:
    """Build a compact summary of the part for intent detection."""
    return {
        "name": part.name,
        "params": {name: {"value": p.value, "unit": p.unit} for name, p in part.params.items()},
        "features": [{"name": f.name, "type": f.type} for f in part.features],
        "chains": [{"name": c.name, "terms": c.terms} for c in part.chains]
    }


@router.post("/command")
async def agent_command(request: AgentCommandRequest) -> AgentCommandResponse:
    """
    Process an agent command with intent-based dispatch.
    
    The system automatically detects the user's intent and routes to the appropriate handler:
    - CHAT_MODEL: Pure chat/explanation
    - EDIT_DSL: Edit DSL code (Cursor-style)
    MVP: Only chat, DSL editing, and sketch editing supported.
    
    If auto_detect_intent is False, uses legacy mode-based routing.
    """
    try:
        # Parse part if provided, otherwise get from store
        part = None
        if request.part:
            part = Part.model_validate(request.part)
            # Store it
            set_part(part)
        else:
            part = get_current_part()
        
        # Handle legacy mode if auto_detect is disabled
        if not request.auto_detect_intent and request.mode:
            # Legacy flow (for CREATE mode or explicit mode selection)
            if request.mode == "create" and not part:
                # Create new part - use legacy flow
                scope = AgentScope(
                    selected_feature_ids=request.selection.get("selected_feature_ids", []),
                    selected_param_names=request.selection.get("selected_param_names", []),
                    selected_chain_names=request.selection.get("selected_chain_names", []),
                )
                
                result: AgentResult = run_agent(
                    mode=AgentMode.CREATE,
                    scope=scope,
                    part=None,
                    user_prompt=request.prompt,
                )
                
                dsl = None
                if result.part:
                    try:
                        dsl = ir_to_dsl(result.part)
                        set_part(result.part, dsl)
                    except Exception as e:
                        print(f"Warning: Failed to generate DSL: {e}")
                
                return AgentCommandResponse(
                    intent="create",
                    part=result.part.model_dump() if result.part else None,
                    dsl=dsl,
                    message=result.message,
                    success=result.part is not None
                )
            else:
                # Other legacy modes - use intent-based flow but with explicit intent
                # This maintains backward compatibility
                if request.mode == "explain":
                    intent = AgentIntent.CHAT_MODEL
                elif request.mode == "edit":
                    intent = AgentIntent.EDIT_DSL
                else:
                    intent = AgentIntent.EDIT_DSL
                
                # Fall through to intent-based flow below
                pass
        
        # Intent-based flow
        # Build context for intent detection
        part_summary = _build_part_summary(part) if part else {}
        
        ctx = IntentContext(
            prompt=request.prompt,
            selection=request.selection,
            part_summary=part_summary
        )
        
        # Detect intent
        intent = detect_intent(ctx)
        
        # Dispatch to appropriate handler
        handler_result: HandlerResult
        
        if intent == AgentIntent.CHAT_MODEL:
            if not part:
                return AgentCommandResponse(
                    intent=intent.value,
                    message="No part loaded. Please create or load a part first.",
                    success=False
                )
            handler_result = handle_chat_model(request.prompt, part, part_summary)
            
        elif intent == AgentIntent.EDIT_DSL:
            if not part:
                return AgentCommandResponse(
                    intent=intent.value,
                    message="No part loaded. Please create or load a part first.",
                    success=False
                )
            current_dsl = get_current_dsl() or (ir_to_dsl(part) if part else "")
            if not current_dsl:
                return AgentCommandResponse(
                    intent=intent.value,
                    message="No DSL available. Please load a part with DSL first.",
                    success=False
                )
            handler_result = handle_edit_dsl(request.prompt, current_dsl, part)
            # Store updated part if successful
            if handler_result.success and handler_result.part:
                set_part(handler_result.part, handler_result.dsl)
            
        else:
            # Fallback to edit_dsl
            if not part:
                return AgentCommandResponse(
                    intent=intent.value,
                    message="No part loaded. Please create or load a part first.",
                    success=False
                )
            current_dsl = get_current_dsl() or (ir_to_dsl(part) if part else "")
            handler_result = handle_edit_dsl(request.prompt, current_dsl, part)
            if handler_result.success and handler_result.part:
                set_part(handler_result.part, handler_result.dsl)
        
        # Convert to response
        return AgentCommandResponse(
            intent=intent.value,
            part=handler_result.part.model_dump() if handler_result.part else None,
            dsl=handler_result.dsl,
            message=handler_result.message,
            success=handler_result.success,
            validation_issues=[issue.model_dump() for issue in handler_result.validation_issues] if handler_result.validation_issues else [],
            script_code=handler_result.script_code,
            sketch=handler_result.sketch.model_dump() if handler_result.sketch else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Agent configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Agent command failed: {str(e)}")

