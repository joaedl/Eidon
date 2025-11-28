"""
API routes for tolerance and chain analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ir import Part
from app.core.analysis import evaluate_all_chains

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """Request body for chain analysis."""
    part: dict  # Part IR as JSON dict


@router.post("/chains")
async def analyze_chains(request: AnalysisRequest) -> dict:
    """
    Analyze all dimensional chains in a part.
    
    Returns evaluation results for all chains.
    """
    try:
        part = Part.model_validate(request.part)
        results = evaluate_all_chains(part)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")

