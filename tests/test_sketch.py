"""
Tests for sketch constraint solving endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_sketch_solve(client, sample_sketch_ir):
    """Test sketch constraint solving."""
    response = await client.post(
        "/sketch/solve",
        json={
            "sketch_ir": sample_sketch_ir
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated_entities" in data
    assert "degrees_of_freedom" in data
    assert "constraint_status" in data
    assert "errors" in data
    
    assert isinstance(data["updated_entities"], list)
    assert isinstance(data["degrees_of_freedom"], int)
    assert "is_fully_constrained" in data["constraint_status"]
    assert isinstance(data["errors"], list)


@pytest.mark.asyncio
async def test_sketch_solve_with_guesses(client, sample_sketch_ir):
    """Test sketch solving with initial guesses."""
    response = await client.post(
        "/sketch/solve",
        json={
            "sketch_ir": sample_sketch_ir,
            "initial_guesses": {
                "line1": {"start": [0.0, 0.0], "end": [50.0, 0.0]}
            },
            "locked_entities": ["line1"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated_entities" in data


@pytest.mark.asyncio
async def test_infer_constraints(client, sample_sketch_ir):
    """Test constraint inference."""
    response = await client.post(
        "/sketch/infer-constraints",
        json={
            "sketch_ir": sample_sketch_ir,
            "tolerance": 1e-3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "suggested_constraints" in data
    assert isinstance(data["suggested_constraints"], list)
    
    # Check constraint structure if any are suggested
    if len(data["suggested_constraints"]) > 0:
        constraint = data["suggested_constraints"][0]
        assert "type" in constraint
        assert "entity_ids" in constraint

