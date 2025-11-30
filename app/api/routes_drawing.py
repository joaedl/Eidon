"""
API routes for drafting and drawing generation.
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Part
from app.core.builder import build_cad_model
from app.core.drawing import generate_front_view_svg
from app.api.schemas import (
    GenerateViewsRequest, GenerateViewsResponse, DrawingView, DrawingEdge, ViewSpec,
    DimensionLayoutRequest, DimensionLayoutResponse, DimensionEntity,
    RenderSvgRequest, RenderSvgResponse
)

router = APIRouter(prefix="/drawing", tags=["drawing"])


@router.post("/generate-views", response_model=GenerateViewsResponse)
async def generate_views(request: GenerateViewsRequest):
    """
    Generate drawing views (no dimensions yet).
    
    Creates front/top/right/isometric views with edge visibility.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Build the CadQuery model
        wp = build_cad_model(part)
        solid = wp.val()
        
        views = []
        
        for view_spec in request.view_specs:
            # For MVP: simplified view generation
            # Full implementation would:
            # 1. Project solid onto view plane
            # 2. Determine visible/hidden edges
            # 3. Extract edge geometry
            
            # Placeholder: generate simple edges
            edges = []
            
            # In full implementation, would extract actual edges from projection
            # For MVP, return placeholder
            if view_spec.type in ["front", "top", "right"]:
                # Orthographic view
                edges.append(DrawingEdge(
                    type="visible",
                    points=[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]
                ))
            elif view_spec.type == "isometric":
                # Isometric view
                edges.append(DrawingEdge(
                    type="visible",
                    points=[[0, 0], [86.6, 50], [86.6, 150], [0, 100], [0, 0]]
                ))
            
            views.append(DrawingView(
                view_id=f"view_{view_spec.type}",
                view_type=view_spec.type,
                edges=edges
            ))
        
        return GenerateViewsResponse(views=views)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"View generation failed: {str(e)}")


@router.post("/dimension-layout", response_model=DimensionLayoutResponse)
async def dimension_layout(request: DimensionLayoutRequest):
    """
    Place dimensions on views automatically using semantic parameters.
    
    Uses part parameters to create dimension entities with automatic layout.
    """
    try:
        part = Part.model_validate(request.part_ir)
        
        # Extract dimensions from part parameters and sketch dimensions
        dimensions = []
        
        # Get dimensions from sketches
        for sketch in part.sketches:
            for dim in sketch.dimensions:
                # Place dimension (simplified - would use proper layout algorithm)
                dimensions.append(DimensionEntity(
                    start=[0, 0],  # Placeholder
                    end=[dim.value, 0],  # Placeholder
                    text=f"{dim.value} {dim.unit}",
                    orientation=0.0
                ))
        
        # Also create dimensions from part parameters
        for param_name, param in part.params.items():
            dimensions.append(DimensionEntity(
                start=[0, len(dimensions) * 20],  # Stack dimensions
                end=[param.value, len(dimensions) * 20],
                text=f"{param.value} {param.unit}",
                orientation=0.0
            ))
        
        # Check for conflicts (simplified)
        conflicts = []
        # In full implementation, would detect overlapping dimensions
        
        return DimensionLayoutResponse(
            dimensions=dimensions,
            conflicts=conflicts
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dimension layout failed: {str(e)}")


@router.post("/render-svg", response_model=RenderSvgResponse)
async def render_svg(request: RenderSvgRequest):
    """
    Convert drawing views + dimensions into a final SVG.
    
    Combines views and dimensions into a complete technical drawing.
    """
    try:
        if request.drawing_ir:
            # Use drawing IR
            # For MVP, use existing SVG generation
            part = Part.model_validate(request.drawing_ir.get("part", {}))
            svg_content = generate_front_view_svg(part)
            return RenderSvgResponse(svg=svg_content)
        elif request.views:
            # Generate SVG from views and dimensions
            # Simplified SVG generation
            svg_lines = [
                '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">',
                '  <g id="views">'
            ]
            
            # Draw views
            for view in request.views:
                for edge in view.edges:
                    if len(edge.points) >= 2:
                        points_str = " ".join([f"{p[0]},{p[1]}" for p in edge.points])
                        stroke = "#000" if edge.type == "visible" else "#999"
                        svg_lines.append(f'    <polyline points="{points_str}" stroke="{stroke}" fill="none" stroke-width="2"/>')
            
            svg_lines.append('  </g>')
            
            # Draw dimensions if provided
            if request.dimensions:
                svg_lines.append('  <g id="dimensions">')
                for dim in request.dimensions:
                    svg_lines.append(f'    <line x1="{dim.start[0]}" y1="{dim.start[1]}" x2="{dim.end[0]}" y2="{dim.end[1]}" stroke="#0066cc" stroke-width="1"/>')
                    svg_lines.append(f'    <text x="{(dim.start[0] + dim.end[0])/2}" y="{(dim.start[1] + dim.end[1])/2 - 5}" fill="#0066cc" font-size="12">{dim.text}</text>')
                svg_lines.append('  </g>')
            
            svg_lines.append('</svg>')
            svg_content = "\n".join(svg_lines)
            
            return RenderSvgResponse(svg=svg_content)
        else:
            raise HTTPException(status_code=400, detail="Either drawing_ir or views must be provided")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SVG rendering failed: {str(e)}")

