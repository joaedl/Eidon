"""
API routes for exporting parts to STL, STEP, and SVG drawing formats.
"""

from fastapi import APIRouter, HTTPException
import base64
import tempfile
import os
import cadquery as cq
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.api.schemas import (
    ExportStepRequest, ExportStepResponse,
    ExportStlRequest, ExportStlResponse, MeshParams,
    ExportDxfRequest, ExportDxfResponse
)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/step", response_model=ExportStepResponse)
async def export_step(request: ExportStepRequest):
    """
    Export part to STEP format.
    
    Returns base64-encoded STEP file.
    """
    try:
        part = Part.model_validate(request.part_ir)
        part_name = request.name or part.name
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Export to STEP using CadQuery's export method
        with tempfile.NamedTemporaryFile(mode='w', suffix='.step', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # CadQuery exportStep writes to a file
            # Try to use schema parameter if available
            try:
                solid.exportStep(tmp_path, schema=request.step_schema)
            except TypeError:
                # Fallback if schema parameter not supported
                solid.exportStep(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                step_data = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Encode to base64
        file_b64 = base64.b64encode(step_data).decode('utf-8')
        
        return ExportStepResponse(
            file_b64=file_b64,
            size_bytes=len(step_data),
            name=f"{part_name}.step"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"STEP export failed: {str(e)}")


@router.post("/stl", response_model=ExportStlResponse)
async def export_stl(request: ExportStlRequest):
    """
    Export part to STL format.
    
    Returns base64-encoded STL file.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        # Apply mesh parameters if provided
        # For MVP, we use tessellation tolerance
        tolerance = 0.1  # default
        if request.mesh_params:
            if request.mesh_params.linear_tolerance:
                tolerance = request.mesh_params.linear_tolerance
        
        # Export to STL using CadQuery's export method
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stl', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # CadQuery exportStl writes to a file
            # Note: mesh_params would ideally control tessellation, but CadQuery's exportStl
            # uses its own internal tessellation. For MVP, we accept this limitation.
            solid.exportStl(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                stl_data = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Encode to base64
        file_b64 = base64.b64encode(stl_data).decode('utf-8')
        
        return ExportStlResponse(
            file_b64=file_b64,
            size_bytes=len(stl_data)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"STL export failed: {str(e)}")


@router.post("/dxf", response_model=ExportDxfResponse)
async def export_dxf(request: ExportDxfRequest):
    """
    Export 2D drawings/sections as DXF.
    
    Can export from part IR with view spec, or from drawing IR.
    """
    try:
        import base64
        import tempfile
        import os
        
        # For MVP: simplified DXF export
        # Full implementation would use a DXF library (e.g., ezdxf)
        # For now, return a placeholder
        
        if request.part_ir:
            part = Part.model_validate(request.part_ir)
            # Generate DXF from part (simplified)
            # In full implementation, would generate proper DXF with entities
            dxf_content = f"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n"  # Minimal DXF
            
            file_b64 = base64.b64encode(dxf_content.encode()).decode('utf-8')
            return ExportDxfResponse(
                file_b64=file_b64,
                size_bytes=len(dxf_content)
            )
        elif request.drawing_ir:
            # Export from drawing IR
            dxf_content = f"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n"
            file_b64 = base64.b64encode(dxf_content.encode()).decode('utf-8')
            return ExportDxfResponse(
                file_b64=file_b64,
                size_bytes=len(dxf_content)
            )
        else:
            raise HTTPException(status_code=400, detail="Either part_ir or drawing_ir must be provided")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DXF export failed: {str(e)}")

