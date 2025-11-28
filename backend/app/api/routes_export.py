"""
API routes for exporting parts to STL and STEP formats.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import cadquery as cq
from app.core.ir import Part
from app.core.builder import build_cad_model

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request body for export operations."""
    part: dict  # Part IR as JSON dict


@router.post("/stl")
async def export_stl(request: ExportRequest):
    """
    Export part to STL format.
    
    Returns a downloadable STL file.
    """
    try:
        part = Part.model_validate(request.part)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        
        # Export to STL using CadQuery's export method
        # Use a temporary file or string buffer
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as tmp:
            wp.val().exportStl(tmp.name)
            with open(tmp.name, 'rb') as f:
                stl_data = f.read()
            os.unlink(tmp.name)
        
        # Create a BytesIO stream
        stl_stream = io.BytesIO(stl_data)
        
        return StreamingResponse(
            stl_stream,
            media_type="application/sla",
            headers={
                "Content-Disposition": f'attachment; filename="{part.name}.stl"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"STL export failed: {str(e)}")


@router.post("/step")
async def export_step(request: ExportRequest):
    """
    Export part to STEP format.
    
    Returns a downloadable STEP file.
    """
    try:
        part = Part.model_validate(request.part)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Export to STEP using CadQuery's export method
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.step', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # CadQuery exportStep writes to a file
            solid.exportStep(tmp_path)
            with open(tmp_path, 'rb') as f:
                step_data = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Create a BytesIO stream
        step_stream = io.BytesIO(step_data)
        
        return StreamingResponse(
            step_stream,
            media_type="application/step",
            headers={
                "Content-Disposition": f'attachment; filename="{part.name}.step"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"STEP export failed: {str(e)}")

