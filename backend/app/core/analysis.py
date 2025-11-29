"""
Analysis module: tolerance and dimensional chain analysis.

This module evaluates parameters with tolerances and calculates
1D dimensional chains (stackups) using worst-case analysis.
"""

from typing import Optional
from app.core.ir import Part, Param, Chain, ValidationIssue, Sketch, SketchEntity, SketchConstraint, SketchDimension, Feature


# Simple tolerance class lookup table (MVP: hardcoded for a few common classes)
# Format: {tolerance_class: {nominal_range: (min_deviation, max_deviation)}}
# For MVP, we'll use simplified values
TOLERANCE_LOOKUP: dict[str, dict[tuple[float, float], tuple[float, float]]] = {
    "g6": {
        # For nominal 10-50mm: -0.009 to -0.025 (example values)
        (10.0, 50.0): (-0.009, -0.025),
        # For nominal >50mm: -0.010 to -0.030
        (50.0, 100.0): (-0.010, -0.030),
    },
    "H7": {
        # For nominal 10-50mm: +0.000 to +0.025
        (10.0, 50.0): (0.000, 0.025),
        # For nominal >50mm: +0.000 to +0.030
        (50.0, 100.0): (0.000, 0.030),
    },
    # Add more tolerance classes as needed
}


def get_tolerance_deviations(param: Param) -> tuple[float, float]:
    """
    Get min and max deviations for a parameter based on its tolerance class.
    
    Args:
        param: The parameter with tolerance class
        
    Returns:
        tuple: (min_deviation, max_deviation) from nominal
    """
    if not param.tolerance_class:
        return (0.0, 0.0)
    
    tolerance_class = param.tolerance_class
    if tolerance_class not in TOLERANCE_LOOKUP:
        # Unknown tolerance class: return zero deviation
        return (0.0, 0.0)
    
    # Find the appropriate range for the nominal value
    nominal = param.value
    ranges = TOLERANCE_LOOKUP[tolerance_class]
    
    for (min_nominal, max_nominal), (min_dev, max_dev) in ranges.items():
        if min_nominal <= nominal < max_nominal:
            return (min_dev, max_dev)
    
    # Default: use the last range or zero
    if ranges:
        last_range = list(ranges.values())[-1]
        return last_range
    
    return (0.0, 0.0)


def evaluate_param_with_tolerance(param: Param) -> dict[str, float]:
    """
    Evaluate a parameter with its tolerance, returning nominal, min, and max values.
    
    Args:
        param: The parameter to evaluate
        
    Returns:
        dict with keys: 'nominal', 'min', 'max'
    """
    nominal = param.value
    min_dev, max_dev = get_tolerance_deviations(param)
    
    return {
        "nominal": nominal,
        "min": nominal + min_dev,
        "max": nominal + max_dev,
    }


def evaluate_chain(part: Part, chain: Chain) -> dict[str, float]:
    """
    Evaluate a dimensional chain using worst-case analysis.
    
    The chain is a sum of parameters: chain_value = sum(terms)
    We calculate min and max by summing the min/max of each term.
    
    Args:
        part: The part containing parameters
        chain: The chain to evaluate
        
    Returns:
        dict with keys: 'nominal', 'min', 'max'
    """
    nominal_sum = 0.0
    min_sum = 0.0
    max_sum = 0.0
    
    for term_name in chain.terms:
        if term_name not in part.params:
            # Parameter not found: skip or raise error
            continue
        
        param = part.params[term_name]
        param_eval = evaluate_param_with_tolerance(param)
        
        nominal_sum += param_eval["nominal"]
        min_sum += param_eval["min"]
        max_sum += param_eval["max"]
    
    return {
        "nominal": nominal_sum,
        "min": min_sum,
        "max": max_sum,
    }


def evaluate_all_chains(part: Part) -> dict[str, dict[str, float]]:
    """
    Evaluate all chains in a part.
    
    Args:
        part: The part to evaluate
        
    Returns:
        dict mapping chain name to evaluation result
    """
    results = {}
    for chain in part.chains:
        results[chain.name] = evaluate_chain(part, chain)
    
    return results


def evaluate_all_params(part: Part) -> dict[str, dict[str, float]]:
    """
    Evaluate all parameters in a part with tolerances.
    
    Args:
        part: The part to evaluate
        
    Returns:
        dict mapping parameter name to evaluation result
    """
    results = {}
    for param_name, param in part.params.items():
        results[param_name] = evaluate_param_with_tolerance(param)
    
    return results


def validate_part(part: Part) -> list[ValidationIssue]:
    """
    Validate a Part and return a list of validation issues.
    
    Checks for:
    - Missing/undefined parameters referenced by features
    - Unused parameters
    - Tolerance feasibility issues
    - Underconstrained models
    
    Args:
        part: The part to validate
        
    Returns:
        List of ValidationIssue objects
    """
    issues: list[ValidationIssue] = []
    
    # Collect all parameter names referenced in features
    referenced_params: set[str] = set()
    
    # Check for missing parameters in features
    for feature in part.features:
        for param_key, param_value in feature.params.items():
            # If param_value is a string, it might be a parameter reference
            if isinstance(param_value, str):
                # Check if it's a parameter name (not a string literal or number with unit)
                # Simple heuristic: if it doesn't contain spaces and isn't a number, it might be a param ref
                if param_value not in ["end", "start"] and not any(c in param_value for c in " \t\n"):
                    # Check if it exists in params
                    if param_value not in part.params:
                        issues.append(ValidationIssue(
                            code="MISSING_PARAM",
                            severity="error",
                            message=f"Feature '{feature.name}' references undefined parameter '{param_value}' in '{param_key}'",
                            related_params=[param_value],
                            related_features=[feature.name]
                        ))
                    else:
                        referenced_params.add(param_value)
    
    # Check for unused parameters
    # Also check chains for parameter references
    for chain in part.chains:
        for term in chain.terms:
            if term in part.params:
                referenced_params.add(term)
            elif term not in part.params:
                issues.append(ValidationIssue(
                    code="MISSING_PARAM",
                    severity="error",
                    message=f"Chain '{chain.name}' references undefined parameter '{term}'",
                    related_params=[term],
                    related_chains=[chain.name]
                ))
    
    # Find unused parameters
    for param_name in part.params:
        if param_name not in referenced_params:
            issues.append(ValidationIssue(
                code="UNUSED_PARAM",
                severity="warning",
                message=f"Parameter '{param_name}' is never used in any feature or chain",
                related_params=[param_name]
            ))
    
    # Check tolerance feasibility for chains with targets
    for chain in part.chains:
        if chain.target_value is not None and chain.target_tolerance is not None:
            chain_eval = evaluate_chain(part, chain)
            target_min = chain.target_value - chain.target_tolerance
            target_max = chain.target_value + chain.target_tolerance
            
            if chain_eval["min"] > target_max or chain_eval["max"] < target_min:
                issues.append(ValidationIssue(
                    code="TOLERANCE_INFEASIBLE",
                    severity="error",
                    message=f"Chain '{chain.name}' cannot meet target tolerance. "
                           f"Actual range: [{chain_eval['min']:.3f}, {chain_eval['max']:.3f}], "
                           f"Target: [{target_min:.3f}, {target_max:.3f}]",
                    related_chains=[chain.name],
                    related_params=chain.terms
                ))
            elif chain_eval["min"] < target_min or chain_eval["max"] > target_max:
                issues.append(ValidationIssue(
                    code="TOLERANCE_TIGHT",
                    severity="warning",
                    message=f"Chain '{chain.name}' is close to target tolerance limits",
                    related_chains=[chain.name],
                    related_params=chain.terms
                ))
    
    # MVP: Removed generic underconstrained model check (too generic)
    # MVP: Removed critical features check (not in MVP scope)
    
    # Rule 6: Validate sketches
    for sketch in part.sketches:
        issues.extend(validate_sketch(sketch))
    
    # Also validate sketches embedded in sketch features
    for feature in part.features:
        if feature.type == "sketch" and feature.sketch:
            issues.extend(validate_sketch(feature.sketch))
    
    return issues


def validate_sketch(sketch: Sketch) -> list[ValidationIssue]:
    """
    Validate a sketch for constraint and dimension issues.
    
    For MVP, performs simple checks:
    - Unconstrained entities (entities without constraints or dimensions)
    - Trivial contradictions (dimensions that don't match entity geometry)
    - Over/under-constrained detection (simple heuristic)
    
    Args:
        sketch: The sketch to validate
        
    Returns:
        List of validation issues
    """
    issues: list[ValidationIssue] = []
    
    # Build a map of which entities are referenced
    entity_ids = {e.id for e in sketch.entities}
    constrained_entities = set()
    dimensioned_entities = set()
    
    # Check constraints
    for constraint in sketch.constraints:
        for entity_id in constraint.entity_ids:
            if entity_id in entity_ids:
                constrained_entities.add(entity_id)
            else:
                issues.append(ValidationIssue(
                    code="SKETCH_CONSTRAINT_REF_INVALID",
                    severity="error",
                    message=f"Constraint '{constraint.id}' references non-existent entity '{entity_id}' in sketch '{sketch.name}'",
                    related_features=[sketch.name]
                ))
    
    # Check dimensions
    for dimension in sketch.dimensions:
        for entity_id in dimension.entity_ids:
            if entity_id in entity_ids:
                dimensioned_entities.add(entity_id)
            else:
                issues.append(ValidationIssue(
                    code="SKETCH_DIMENSION_REF_INVALID",
                    severity="error",
                    message=f"Dimension '{dimension.id}' references non-existent entity '{entity_id}' in sketch '{sketch.name}'",
                    related_features=[sketch.name]
                ))
    
    # Check for unconstrained entities (warning, not error)
    for entity in sketch.entities:
        if entity.id not in constrained_entities and entity.id not in dimensioned_entities:
            issues.append(ValidationIssue(
                code="SKETCH_ENTITY_UNCONSTRAINED",
                severity="warning",
                message=f"Entity '{entity.id}' in sketch '{sketch.name}' has no constraints or dimensions",
                related_features=[sketch.name]
            ))
    
    # Simple geometry validation: check if dimensions match entity geometry (for lines)
    for dimension in sketch.dimensions:
        if dimension.type == "length":
            entity_id = dimension.entity_ids[0]
            entity = next((e for e in sketch.entities if e.id == entity_id), None)
            if entity and entity.type == "line":
                # Calculate actual length
                if entity.start and entity.end:
                    dx = entity.end[0] - entity.start[0]
                    dy = entity.end[1] - entity.start[1]
                    actual_length = (dx**2 + dy**2)**0.5
                    # Allow small tolerance (1% or 0.1mm)
                    tolerance = max(actual_length * 0.01, 0.1)
                    if abs(actual_length - dimension.value) > tolerance:
                        issues.append(ValidationIssue(
                            code="SKETCH_DIMENSION_MISMATCH",
                            severity="warning",
                            message=f"Dimension '{dimension.id}' value ({dimension.value} {dimension.unit}) doesn't match entity '{entity_id}' geometry (length ≈ {actual_length:.2f} {dimension.unit})",
                            related_features=[sketch.name]
                        ))
    
    # MVP: Check for conflicting dimensions (same entity dimensioned multiple times with different values)
    entity_dimensions: dict[str, list[SketchDimension]] = {}
    for dimension in sketch.dimensions:
        for entity_id in dimension.entity_ids:
            if entity_id not in entity_dimensions:
                entity_dimensions[entity_id] = []
            entity_dimensions[entity_id].append(dimension)
    
    for entity_id, dims in entity_dimensions.items():
        if len(dims) > 1:
            # Check if values conflict (for same dimension type)
            length_dims = [d for d in dims if d.type == "length"]
            diameter_dims = [d for d in dims if d.type == "diameter"]
            
            if len(length_dims) > 1:
                values = [d.value for d in length_dims]
                if len(set(values)) > 1:
                    issues.append(ValidationIssue(
                        code="SKETCH_CONFLICTING_DIMENSIONS",
                        severity="error",
                        message=f"Entity '{entity_id}' has conflicting length dimensions: {values}",
                        related_features=[sketch.name]
                    ))
            
            if len(diameter_dims) > 1:
                values = [d.value for d in diameter_dims]
                if len(set(values)) > 1:
                    issues.append(ValidationIssue(
                        code="SKETCH_CONFLICTING_DIMENSIONS",
                        severity="error",
                        message=f"Entity '{entity_id}' has conflicting diameter dimensions: {values}",
                        related_features=[sketch.name]
                    ))
    
    # MVP: Simple check for overlapping entities (lines that are too close)
    for i, entity1 in enumerate(sketch.entities):
        for entity2 in sketch.entities[i+1:]:
            if entity1.type == "line" and entity2.type == "line":
                if entity1.start and entity1.end and entity2.start and entity2.end:
                    # Check if lines are very close (within 0.1mm)
                    dist1 = point_to_line_distance(entity2.start, entity1.start, entity1.end)
                    dist2 = point_to_line_distance(entity2.end, entity1.start, entity1.end)
                    if dist1 < 0.1 and dist2 < 0.1:
                        issues.append(ValidationIssue(
                            code="SKETCH_OVERLAPPING_ENTITIES",
                            severity="warning",
                            message=f"Entities '{entity1.id}' and '{entity2.id}' appear to overlap",
                            related_features=[sketch.name]
                        ))
    
    return issues


def point_to_line_distance(point: tuple[float, float], line_start: tuple[float, float], line_end: tuple[float, float]) -> float:
    """Calculate distance from a point to a line segment."""
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    A = x0 - x1
    B = y0 - y1
    C = x2 - x1
    D = y2 - y1
    
    dot = A * C + B * D
    len_sq = C * C + D * D
    param = -1
    if len_sq != 0:
        param = dot / len_sq
    
    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D
    
    dx = x0 - xx
    dy = y0 - yy
    return (dx * dx + dy * dy) ** 0.5


