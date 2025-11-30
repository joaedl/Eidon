"""
Tests for build endpoints (solid, sketch, feature).
"""

import pytest


@pytest.mark.asyncio
async def test_build_solid(client, sample_part_ir):
    """Test building a solid from PartIR."""
    response = await client.post(
        "/build/solid",
        json={
            "part_ir": sample_part_ir,
            "detail_level": "normal",
            "return_mesh": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "mesh" in data
    assert "bounding_box" in data
    assert "topology_summary" in data
    assert "status" in data
    assert data["status"] == "ok"
    
    # Check mesh structure
    if data["mesh"]:
        assert "vertices" in data["mesh"]
        assert "faces" in data["mesh"]
        assert len(data["mesh"]["vertices"]) > 0
        assert len(data["mesh"]["faces"]) > 0
    
    # Check bounding box
    assert "min" in data["bounding_box"]
    assert "max" in data["bounding_box"]
    assert len(data["bounding_box"]["min"]) == 3
    assert len(data["bounding_box"]["max"]) == 3
    
    # Check topology summary
    assert "face_count" in data["topology_summary"]
    assert "edge_count" in data["topology_summary"]
    assert "vertex_count" in data["topology_summary"]


@pytest.mark.asyncio
async def test_build_solid_coarse_detail(client, sample_part_ir):
    """Test building with coarse detail level."""
    response = await client.post(
        "/build/solid",
        json={
            "part_ir": sample_part_ir,
            "detail_level": "coarse",
            "return_mesh": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_build_solid_high_detail(client, sample_part_ir):
    """Test building with high detail level."""
    response = await client.post(
        "/build/solid",
        json={
            "part_ir": sample_part_ir,
            "detail_level": "high",
            "return_mesh": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_build_solid_no_mesh(client, sample_part_ir):
    """Test building without returning mesh."""
    response = await client.post(
        "/build/solid",
        json={
            "part_ir": sample_part_ir,
            "detail_level": "normal",
            "return_mesh": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mesh"] is None
    assert "bounding_box" in data
    assert "topology_summary" in data


@pytest.mark.asyncio
async def test_build_sketch(client, sample_sketch_ir):
    """Test building/evaluating a sketch."""
    response = await client.post(
        "/build/sketch",
        json={
            "sketch_ir": sample_sketch_ir,
            "resolve_constraints": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "curves" in data
    assert "constraint_status" in data
    assert "issues" in data
    
    # Check curves
    assert isinstance(data["curves"], list)
    if len(data["curves"]) > 0:
        curve = data["curves"][0]
        assert "type" in curve
        assert "points" in curve
    
    # Check constraint status
    assert "is_fully_constrained" in data["constraint_status"]
    assert "is_overconstrained" in data["constraint_status"]


@pytest.mark.asyncio
async def test_build_feature(client, sample_part_ir):
    """Test building a single feature."""
    response = await client.post(
        "/build/feature",
        json={
            "part_ir": sample_part_ir,
            "feature_id": "base_extrude"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "mesh" in data
    assert "bounding_box" in data
    assert "depends_on_features" in data


@pytest.mark.asyncio
async def test_build_feature_not_found(client, sample_part_ir):
    """Test building a non-existent feature."""
    response = await client.post(
        "/build/feature",
        json={
            "part_ir": sample_part_ir,
            "feature_id": "nonexistent_feature"
        }
    )
    assert response.status_code == 404

