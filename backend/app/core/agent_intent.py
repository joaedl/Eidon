"""
Agent Intent Classification.

This module classifies user prompts into different intents to determine
how the LLM agent should respond.
"""

import os
from enum import Enum
from typing import Any
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


class AgentIntent(str, Enum):
    """Intent classification for agent requests.
    
    MVP: Only chat, DSL editing, and sketch editing supported.
    """
    CHAT_MODEL = "chat_model"  # Pure chat/explanation, no code changes
    EDIT_DSL = "edit_dsl"  # Edit the DSL code
    EDIT_SKETCH = "edit_sketch"  # Edit sketch geometry/constraints/dimensions


class IntentContext(BaseModel):
    """Context for intent classification."""
    prompt: str
    selection: dict[str, Any] = {}  # e.g. selected_feature_ids, selected_text_range, etc.
    part_summary: dict[str, Any] = {}  # compact summary (params, features, chains)


def detect_intent(ctx: IntentContext) -> AgentIntent:
    """
    Classify user prompt into an intent using LLM.
    
    Args:
        ctx: Context containing prompt, selection, and part summary
        
    Returns:
        AgentIntent: The detected intent
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback to heuristics if no API key
        return _heuristic_intent_detection(ctx.prompt)
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are an intent classifier for a CAD system.

Classify the user's prompt into one of these intents:

1. CHAT_MODEL: User wants to ask questions, get explanations, or discuss the model WITHOUT making any changes.
   Examples:
   - "What is this part?"
   - "Explain the tolerance issue"
   - "Why is there a validation error?"
   - "What does this feature do?"

2. EDIT_DSL: User wants to modify the DSL code directly.
   Examples:
   - "Change the distance to 50mm"
   - "Add a new extrude feature"
   - "Update the sketch profile"
   - "Modify the part parameters"

3. EDIT_SKETCH: User is in sketch mode and wants to modify sketch geometry, constraints, or dimensions.
   Examples:
   - "Draw a rectangle 50 by 30mm"
   - "Make this line horizontal and dimension it to 50mm"
   - "Add a circle at the origin"
   - "Make these points coincident"

Respond with ONLY the intent name: CHAT_MODEL, EDIT_DSL, or EDIT_SKETCH."""

    user_message = f"""User prompt: {ctx.prompt}

Context:
- Has selection: {bool(ctx.selection)}
- Part has {len(ctx.part_summary.get('params', {}))} parameters, {len(ctx.part_summary.get('features', []))} features"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=20
        )
        
        intent_str = response.choices[0].message.content.strip().upper()
        
        # Map response to enum (MVP: only chat, DSL, and sketch)
        intent_map = {
            "CHAT_MODEL": AgentIntent.CHAT_MODEL,
            "EDIT_DSL": AgentIntent.EDIT_DSL,
            "EDIT_SKETCH": AgentIntent.EDIT_SKETCH,
        }
        
        return intent_map.get(intent_str, AgentIntent.EDIT_DSL)  # Default to EDIT_DSL
        
    except Exception as e:
        # Fallback to heuristics on error
        print(f"Intent detection failed: {e}, using heuristics")
        return _heuristic_intent_detection(ctx.prompt)


def _heuristic_intent_detection(prompt: str) -> AgentIntent:
    """
    Fallback heuristic-based intent detection.
    
    Args:
        prompt: User prompt
        
    Returns:
        AgentIntent: Detected intent
    """
    prompt_lower = prompt.lower()
    
    # Keywords for chat
    chat_keywords = ["what", "why", "how", "explain", "tell me", "describe", "question"]
    if any(keyword in prompt_lower for keyword in chat_keywords):
        return AgentIntent.CHAT_MODEL
    
    # MVP: No script generation - default to DSL editing
    return AgentIntent.EDIT_DSL

