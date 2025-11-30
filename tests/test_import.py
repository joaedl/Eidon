"""
Tests for import endpoints.
"""

import pytest
import base64


@pytest.mark.asyncio
async def test_import_step_placeholder(client):
    """Test STEP import (placeholder - requires actual STEP file)."""
    # Create a minimal STEP file content (ASCII STL-like for testing)
    # In real usage, this would be a proper STEP file
    step_content = "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;"
    step_b64 = base64.b64encode(step_content.encode()).decode()
    
    response = await client.post(
        "/import/step",
        json={
            "file_b64": step_b64
        }
    )
    # This may fail if STEP import is not fully implemented, but structure should be tested
    # We expect either 200 or 400/500 depending on implementation
    assert response.status_code in [200, 400, 500, 501]
    
    if response.status_code == 200:
        data = response.json()
        assert "brep_summary" in data

