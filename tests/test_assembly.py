"""
Tests for assembly endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_assembly_build(client, sample_part_ir, sample_part_ir_minimal):
    """Test building an assembly."""
    response = await client.post(
        "/assembly/build",
        json={
            "parts": [sample_part_ir, sample_part_ir_minimal],
            "mate_definitions": [
                {
                    "type": "planar",
                    "part_a": "part_0",
                    "part_b": "part_1",
                    "params": {}
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "mate_status" in data
    assert "solved" in data["mate_status"]


@pytest.mark.asyncio
async def test_assembly_interference_check(client, sample_part_ir, sample_part_ir_minimal):
    """Test assembly interference check."""
    response = await client.post(
        "/assembly/interference-check",
        json={
            "assembly_ir": {
                "parts": [sample_part_ir, sample_part_ir_minimal],
                "mates": []
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "colliding_pairs" in data
    assert isinstance(data["colliding_pairs"], list)


@pytest.mark.asyncio
async def test_motion_sweep(client, sample_part_ir):
    """Test motion sweep analysis."""
    response = await client.post(
        "/assembly/motion-sweep",
        json={
            "assembly_ir": {
                "parts": [sample_part_ir]
            },
            "joint_definitions": [
                {
                    "name": "joint1",
                    "type": "revolute",
                    "params": {}
                }
            ],
            "parameter_sweep": {
                "joint1": {
                    "min": 0.0,
                    "max": 90.0,
                    "steps": 10
                }
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "contact_events" in data
    assert isinstance(data["contact_events"], list)

