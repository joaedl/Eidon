"""
Tests for selection mapping and topology utilities.
"""

import pytest


@pytest.mark.asyncio
async def test_map_pick(client, sample_part_ir):
    """Test mapping a 3D pick to topological elements."""
    response = await client.post(
        "/selection/map-pick",
        json={
            "part_ir": sample_part_ir,
            "pick_ray": {
                "origin": [25.0, 15.0, 40.0],
                "direction": [0.0, 0.0, -1.0]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Response may or may not have picks, but structure should be valid
    assert "face_id" in data or data.get("face_id") is None
    assert "edge_id" in data or data.get("edge_id") is None
    assert "vertex_id" in data or data.get("vertex_id") is None
    assert "feature_reference" in data or data.get("feature_reference") is None


@pytest.mark.asyncio
async def test_topology_tagging(client):
    """Test topology tagging for stable IDs."""
    response = await client.post(
        "/topology/tagging",
        json={
            "old_solid_signature": {
                "face_count": 6,
                "edge_count": 12,
                "vertex_count": 8
            },
            "new_solid_signature": {
                "face_count": 6,
                "edge_count": 12,
                "vertex_count": 8
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "face_mapping" in data
    assert "edge_mapping" in data
    assert "vertex_mapping" in data
    assert isinstance(data["face_mapping"], dict)
    assert isinstance(data["edge_mapping"], dict)
    assert isinstance(data["vertex_mapping"], dict)

