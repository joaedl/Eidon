"""
Tests for analysis endpoints (validation, mass properties, clearance, interference, tolerance-chain).
"""

import pytest


@pytest.mark.asyncio
async def test_geometry_validation(client, sample_part_ir):
    """Test geometry validation."""
    response = await client.post(
        "/analysis/geometry-validation",
        json={
            "part_ir": sample_part_ir
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "is_valid_solid" in data
    assert isinstance(data["issues"], list)
    assert isinstance(data["is_valid_solid"], bool)


@pytest.mark.asyncio
async def test_mass_properties(client, sample_part_ir):
    """Test mass properties calculation."""
    response = await client.post(
        "/analysis/mass-properties",
        json={
            "part_ir": sample_part_ir
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "volume" in data
    assert "area" in data
    assert "center_of_mass" in data
    assert "principal_moments" in data
    assert "principal_axes" in data
    
    assert isinstance(data["volume"], float)
    assert isinstance(data["area"], float)
    assert len(data["center_of_mass"]) == 3
    assert len(data["principal_moments"]) == 3
    assert len(data["principal_axes"]) == 3


@pytest.mark.asyncio
async def test_mass_properties_with_material(client, sample_part_ir):
    """Test mass properties with material definition."""
    response = await client.post(
        "/analysis/mass-properties",
        json={
            "part_ir": sample_part_ir,
            "material": {
                "name": "steel",
                "density": 7850.0
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "volume" in data


@pytest.mark.asyncio
async def test_mass_properties_with_density(client, sample_part_ir):
    """Test mass properties with density value."""
    response = await client.post(
        "/analysis/mass-properties",
        json={
            "part_ir": sample_part_ir,
            "density": 7850.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "volume" in data


@pytest.mark.asyncio
async def test_clearance(client, sample_part_ir, sample_part_ir_minimal):
    """Test clearance analysis between two parts."""
    response = await client.post(
        "/analysis/clearance",
        json={
            "part_a_ir": sample_part_ir,
            "part_b_ir": sample_part_ir_minimal
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "min_distance" in data
    assert "locations" in data
    assert "collisions" in data
    assert isinstance(data["min_distance"], float)
    assert isinstance(data["locations"], list)
    assert isinstance(data["collisions"], list)


@pytest.mark.asyncio
async def test_clearance_with_threshold(client, sample_part_ir, sample_part_ir_minimal):
    """Test clearance analysis with threshold."""
    response = await client.post(
        "/analysis/clearance",
        json={
            "part_a_ir": sample_part_ir,
            "part_b_ir": sample_part_ir_minimal,
            "min_clearance_threshold": 1.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "min_distance" in data
    assert "collisions" in data


@pytest.mark.asyncio
async def test_interference(client, sample_part_ir, sample_part_ir_minimal):
    """Test interference analysis."""
    response = await client.post(
        "/analysis/interference",
        json={
            "part_a_ir": sample_part_ir,
            "part_b_ir": sample_part_ir_minimal
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "has_interference" in data
    assert isinstance(data["has_interference"], bool)


@pytest.mark.asyncio
async def test_tolerance_chain(client, sample_part_ir):
    """Test tolerance chain analysis."""
    response = await client.post(
        "/analysis/tolerance-chain",
        json={
            "part_ir": sample_part_ir,
            "chain_definition": {
                "nominal": 100.0,
                "tolerances": [
                    {"plus": 0.1, "minus": 0.1},
                    {"plus": 0.2, "minus": 0.2}
                ]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "nominal_length" in data
    assert "worst_case_min" in data
    assert "worst_case_max" in data
    assert isinstance(data["nominal_length"], float)
    assert isinstance(data["worst_case_min"], float)
    assert isinstance(data["worst_case_max"], float)

