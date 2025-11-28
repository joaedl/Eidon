"""
Analysis module: tolerance and dimensional chain analysis.

This module evaluates parameters with tolerances and calculates
1D dimensional chains (stackups) using worst-case analysis.
"""

from typing import Optional
from app.core.ir import Part, Param, Chain, ValidationIssue, Feature


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
    
    # Check for underconstrained models
    # If there are multiple features but no constraints, warn
    if len(part.features) > 1 and len(part.constraints) == 0:
        issues.append(ValidationIssue(
            code="UNDERCONSTRAINED_MODEL",
            severity="warning",
            message=f"Model has {len(part.features)} features but no constraints defined. "
                   f"Model may be underconstrained.",
            related_features=[f.name for f in part.features]
        ))
    
    # Check for critical features without constraints
    critical_features = [f for f in part.features if f.critical]
    if critical_features and len(part.constraints) == 0:
        issues.append(ValidationIssue(
            code="UNCONSTRAINED_FEATURE",
            severity="warning",
            message=f"Critical features {[f.name for f in critical_features]} have no constraints",
            related_features=[f.name for f in critical_features]
        ))
    
    return issues


