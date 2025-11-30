"""
API routes for importing geometry files.
"""

from fastapi import APIRouter, HTTPException
import base64
import tempfile
import os
import cadquery as cq
from app.api.schemas import ImportStepRequest, ImportStepResponse

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/step", response_model=ImportStepResponse)
async def import_step(request: ImportStepRequest):
    """
    Import a STEP file to get a usable IR-like representation.
    
    Returns BRep summary and optionally a wrapper IR for referencing imported geometry.
    """
    try:
        step_data = None
        
        if request.file_b64:
            # Decode base64
            step_data = base64.b64decode(request.file_b64)
        elif request.file_url:
            # Download from URL (simplified - would use requests in full implementation)
            raise HTTPException(status_code=501, detail="URL import not yet implemented")
        else:
            raise HTTPException(status_code=400, detail="Either file_b64 or file_url must be provided")
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.step', delete=False) as tmp:
            tmp.write(step_data)
            tmp_path = tmp.name
        
        try:
            # Import STEP using CadQuery
            # Note: CadQuery's importStep may not be available in all versions
            # This is a placeholder implementation
            try:
                # Try to import using CadQuery
                imported = cq.importers.importStep(tmp_path)
                
                # Get BRep summary
                if hasattr(imported, 'val'):
                    solid = imported.val()
                    brep_summary = {
                        "volume": solid.Volume(),
                        "area": solid.Area(),
                        "is_valid": solid.isValid(),
                        "face_count": 0,  # Would count faces in full implementation
                        "edge_count": 0,
                        "vertex_count": 0
                    }
                else:
                    brep_summary = {
                        "volume": 0.0,
                        "area": 0.0,
                        "is_valid": False,
                        "face_count": 0,
                        "edge_count": 0,
                        "vertex_count": 0
                    }
                
                # Create wrapper IR (read-only body reference)
                wrapper_ir = {
                    "name": "imported_geometry",
                    "type": "imported_step",
                    "file_reference": tmp_path,  # In production, would store reference
                    "read_only": True
                }
                
                return ImportStepResponse(
                    brep_summary=brep_summary,
                    wrapper_ir=wrapper_ir
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"STEP import failed: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

