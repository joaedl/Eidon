"""
Tests for analysis module.
"""

import pytest
from app.core.ir import Part, Param, Chain
from app.core.analysis import (
    evaluate_param_with_tolerance,
    evaluate_chain,
    evaluate_all_chains,
    evaluate_all_params,
)


def test_evaluate_param_without_tolerance():
    """Test parameter evaluation without tolerance."""
    param = Param(name="length", value=80.0, unit="mm", tolerance_class=None)
    result = evaluate_param_with_tolerance(param)
    
    assert result["nominal"] == 80.0
    assert result["min"] == 80.0
    assert result["max"] == 80.0


def test_evaluate_param_with_tolerance():
    """Test parameter evaluation with tolerance class."""
    param = Param(name="dia", value=20.0, unit="mm", tolerance_class="g6")
    result = evaluate_param_with_tolerance(param)
    
    assert result["nominal"] == 20.0
    # Should have some deviation (exact values depend on tolerance lookup)
    assert result["min"] <= result["nominal"]
    assert result["max"] >= result["nominal"]


def test_evaluate_chain():
    """Test chain evaluation."""
    part = Part(
        name="test",
        params={
            "length": Param(name="length", value=80.0, unit="mm", tolerance_class=None),
            "width": Param(name="width", value=20.0, unit="mm", tolerance_class=None),
        },
        features=[],
        chains=[
            Chain(name="total", terms=["length", "width"])
        ]
    )
    
    chain = part.chains[0]
    result = evaluate_chain(part, chain)
    
    assert result["nominal"] == 100.0  # 80 + 20
    assert result["min"] == 100.0
    assert result["max"] == 100.0


def test_evaluate_all_chains():
    """Test evaluating all chains in a part."""
    part = Part(
        name="test",
        params={
            "length": Param(name="length", value=80.0, unit="mm", tolerance_class=None),
        },
        features=[],
        chains=[
            Chain(name="chain1", terms=["length"]),
            Chain(name="chain2", terms=["length"]),
        ]
    )
    
    results = evaluate_all_chains(part)
    
    assert len(results) == 2
    assert "chain1" in results
    assert "chain2" in results


def test_evaluate_all_params():
    """Test evaluating all parameters in a part."""
    part = Part(
        name="test",
        params={
            "length": Param(name="length", value=80.0, unit="mm", tolerance_class=None),
            "width": Param(name="width", value=20.0, unit="mm", tolerance_class="g6"),
        },
        features=[],
        chains=[]
    )
    
    results = evaluate_all_params(part)
    
    assert len(results) == 2
    assert "length" in results
    assert "width" in results
    assert results["length"]["nominal"] == 80.0

