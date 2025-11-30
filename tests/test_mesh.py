"""
Tests for meshing and visualization endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_mesh_solid(client, sample_part_ir):
    """Test meshing a solid with custom parameters."""
    response = await client.post(
        "/mesh/solid",
        json={
            "part_ir": sample_part_ir,
            "mesh_params": {
                "linear_tolerance": 0.1,
                "angle_tolerance": 0.05
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "mesh" in data
    assert "metrics" in data
    
    # Check mesh
    assert "vertices" in data["mesh"]
    assert "faces" in data["mesh"]
    
    # Check metrics
    assert "triangle_count" in data["metrics"]
    assert "vertex_count" in data["metrics"]
    assert "linear_tolerance" in data["metrics"]


@pytest.mark.asyncio
async def test_section_plane(client, sample_part_ir):
    """Test computing a 2D section at a plane."""
    response = await client.post(
        "/mesh/section/plane",
        json={
            "part_ir": sample_part_ir,
            "plane": {
                "point": [25.0, 15.0, 40.0],
                "normal": [0.0, 0.0, 1.0]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "curves" in data
    assert isinstance(data["curves"], list)

