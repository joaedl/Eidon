"""
API routes for sketch constraint solving.
"""

from fastapi import APIRouter, HTTPException
from app.core.ir import Sketch
from app.api.schemas import (
    SketchSolveRequest, SketchSolveResponse, ConstraintStatus,
    InferConstraintsRequest, InferConstraintsResponse
)

router = APIRouter(prefix="/sketch", tags=["sketch"])


@router.post("/solve", response_model=SketchSolveResponse)
async def sketch_solve(request: SketchSolveRequest):
    """
    Run a constraint solver on the sketch.
    
    For MVP, this is a placeholder. Full implementation would use a proper constraint solver.
    """
    try:
        sketch = Sketch.model_validate(request.sketch_ir)
        
        # MVP: Simplified constraint solving
        # Full implementation would:
        # 1. Build constraint system
        # 2. Solve for entity coordinates
        # 3. Return updated entities with DOF count
        
        # For now, return entities as-is with basic DOF estimation
        updated_entities = []
        for entity in sketch.entities:
            entity_dict = entity.model_dump()
            # In full implementation, coordinates would be updated by solver
            updated_entities.append(entity_dict)
        
        # Estimate DOF (simplified)
        num_entities = len(sketch.entities)
        num_constraints = len(sketch.constraints)
        num_dimensions = len(sketch.dimensions)
        estimated_dof = num_entities * 4 - num_constraints - num_dimensions
        
        constraint_status = ConstraintStatus(
            is_fully_constrained=estimated_dof <= 0,
            is_overconstrained=estimated_dof < 0,
            degrees_of_freedom=estimated_dof if estimated_dof > 0 else None
        )
        
        errors = []
        if constraint_status.is_overconstrained:
            errors.append("Sketch is overconstrained")
        
        return SketchSolveResponse(
            updated_entities=updated_entities,
            degrees_of_freedom=max(0, estimated_dof),
            constraint_status=constraint_status,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sketch solving failed: {str(e)}")


@router.post("/infer-constraints", response_model=InferConstraintsResponse)
async def infer_constraints(request: InferConstraintsRequest):
    """
    Suggest constraints based on approximate geometry.
    
    Analyzes sketch entities and suggests horizontal, vertical, equal lengths, symmetry, etc.
    """
    try:
        sketch = Sketch.model_validate(request.sketch_ir)
        tolerance = request.tolerance
        
        suggested_constraints = []
        
        # Analyze entities for constraint suggestions
        # Horizontal/Vertical detection
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                dx = entity.end[0] - entity.start[0]
                dy = entity.end[1] - entity.start[1]
                
                # Check if approximately horizontal
                if abs(dy) < tolerance:
                    suggested_constraints.append({
                        "type": "horizontal",
                        "entity_ids": [entity.id],
                        "confidence": 1.0 - abs(dy) / tolerance
                    })
                
                # Check if approximately vertical
                if abs(dx) < tolerance:
                    suggested_constraints.append({
                        "type": "vertical",
                        "entity_ids": [entity.id],
                        "confidence": 1.0 - abs(dx) / tolerance
                    })
        
        # Equal length detection
        lines = [e for e in sketch.entities if e.type == "line" and e.start and e.end]
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                len1 = ((line1.end[0] - line1.start[0])**2 + (line1.end[1] - line1.start[1])**2)**0.5
                len2 = ((line2.end[0] - line2.start[0])**2 + (line2.end[1] - line2.start[1])**2)**0.5
                
                if abs(len1 - len2) < tolerance:
                    suggested_constraints.append({
                        "type": "equal_length",
                        "entity_ids": [line1.id, line2.id],
                        "confidence": 1.0 - abs(len1 - len2) / tolerance
                    })
        
        # Coincident point detection
        points = []
        for entity in sketch.entities:
            if entity.type == "line" and entity.start and entity.end:
                points.append((entity.start, entity.id, "start"))
                points.append((entity.end, entity.id, "end"))
            elif entity.type == "circle" and entity.center:
                points.append((entity.center, entity.id, "center"))
        
        for i, (p1, id1, type1) in enumerate(points):
            for p2, id2, type2 in points[i+1:]:
                dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
                if dist < tolerance and id1 != id2:
                    suggested_constraints.append({
                        "type": "coincident",
                        "entity_ids": [id1, id2],
                        "confidence": 1.0 - dist / tolerance
                    })
        
        return InferConstraintsResponse(
            suggested_constraints=suggested_constraints
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Constraint inference failed: {str(e)}")

