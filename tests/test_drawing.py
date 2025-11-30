"""
Tests for drafting and drawing generation endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_generate_views(client, sample_part_ir):
    """Test generating drawing views."""
    response = await client.post(
        "/drawing/generate-views",
        json={
            "part_ir": sample_part_ir,
            "view_specs": [
                {
                    "type": "front",
                    "scale": 1.0,
                    "projection": "third_angle"
                },
                {
                    "type": "top",
                    "scale": 1.0,
                    "projection": "third_angle"
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "views" in data
    assert isinstance(data["views"], list)
    assert len(data["views"]) == 2
    
    # Check view structure
    if len(data["views"]) > 0:
        view = data["views"][0]
        assert "view_id" in view
        assert "view_type" in view
        assert "edges" in view


@pytest.mark.asyncio
async def test_dimension_layout(client, sample_part_ir):
    """Test dimension layout."""
    response = await client.post(
        "/drawing/dimension-layout",
        json={
            "part_ir": sample_part_ir,
            "view_id": "front"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "dimensions" in data
    assert "conflicts" in data
    assert isinstance(data["dimensions"], list)
    assert isinstance(data["conflicts"], list)
    
    # Check dimension structure if any exist
    if len(data["dimensions"]) > 0:
        dim = data["dimensions"][0]
        assert "start" in dim
        assert "end" in dim
        assert "text" in dim
        assert "orientation" in dim


@pytest.mark.asyncio
async def test_render_svg_from_drawing_ir(client, sample_part_ir):
    """Test SVG rendering from drawing IR."""
    response = await client.post(
        "/drawing/render-svg",
        json={
            "drawing_ir": {
                "part": sample_part_ir
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert isinstance(data["svg"], str)
    assert data["svg"].startswith("<svg")


@pytest.mark.asyncio
async def test_render_svg_from_views(client, sample_part_ir):
    """Test SVG rendering from views."""
    # First generate views
    views_response = await client.post(
        "/drawing/generate-views",
        json={
            "part_ir": sample_part_ir,
            "view_specs": [
                {
                    "type": "front",
                    "scale": 1.0,
                    "projection": "third_angle"
                }
            ]
        }
    )
    views = views_response.json()["views"]
    
    # Then render SVG
    response = await client.post(
        "/drawing/render-svg",
        json={
            "views": views
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert data["svg"].startswith("<svg")

