"""
Analysis module: tolerance and dimensional chain analysis.

This module evaluates parameters with tolerances and calculates
1D dimensional chains (stackups) using worst-case analysis.
"""

from typing import Optional
from app.core.ir import Part, Param, Chain


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

