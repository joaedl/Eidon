"""
Tests for export endpoints (STEP, STL, DXF).
"""

import pytest
import base64


@pytest.mark.asyncio
async def test_export_step(client, sample_part_ir):
    """Test STEP export."""
    response = await client.post(
        "/export/step",
        json={
            "part_ir": sample_part_ir,
            "step_schema": "AP214",
            "name": "test_part"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_b64" in data
    assert "size_bytes" in data
    assert "name" in data
    assert data["name"] == "test_part.step"
    assert data["size_bytes"] > 0
    
    # Verify base64 can be decoded
    try:
        decoded = base64.b64decode(data["file_b64"])
        assert len(decoded) == data["size_bytes"]
    except Exception:
        pytest.fail("Invalid base64 encoding")


@pytest.mark.asyncio
async def test_export_step_ap242(client, sample_part_ir):
    """Test STEP export with AP242 schema."""
    response = await client.post(
        "/export/step",
        json={
            "part_ir": sample_part_ir,
            "step_schema": "AP242"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_b64" in data


@pytest.mark.asyncio
async def test_export_stl(client, sample_part_ir):
    """Test STL export."""
    response = await client.post(
        "/export/stl",
        json={
            "part_ir": sample_part_ir
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_b64" in data
    assert "size_bytes" in data
    assert data["size_bytes"] > 0
    
    # Verify base64 can be decoded
    try:
        decoded = base64.b64decode(data["file_b64"])
        assert len(decoded) == data["size_bytes"]
    except Exception:
        pytest.fail("Invalid base64 encoding")


@pytest.mark.asyncio
async def test_export_stl_with_mesh_params(client, sample_part_ir):
    """Test STL export with mesh parameters."""
    response = await client.post(
        "/export/stl",
        json={
            "part_ir": sample_part_ir,
            "mesh_params": {
                "linear_tolerance": 0.05,
                "angle_tolerance": 0.1
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_b64" in data


@pytest.mark.asyncio
async def test_export_dxf_from_part(client, sample_part_ir):
    """Test DXF export from part IR."""
    response = await client.post(
        "/export/dxf",
        json={
            "part_ir": sample_part_ir
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_b64" in data
    assert "size_bytes" in data

