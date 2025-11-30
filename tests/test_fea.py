"""
Tests for FEA endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_fea_linear_static(client, sample_part_ir):
    """Test linear static FEA (placeholder)."""
    response = await client.post(
        "/fea/linear-static",
        json={
            "part_ir": sample_part_ir,
            "material": {
                "name": "steel",
                "density": 7850.0
            },
            "boundary_conditions": [
                {
                    "type": "fixed",
                    "location": {"face": "bottom"},
                    "params": {}
                }
            ],
            "loads": [
                {
                    "type": "force",
                    "location": {"face": "top"},
                    "magnitude": [0.0, 0.0, -1000.0]
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "max_von_mises" in data
    assert "max_displacement" in data
    assert isinstance(data["max_von_mises"], float)
    assert isinstance(data["max_displacement"], float)

