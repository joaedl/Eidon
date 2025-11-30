"""
Tests for service endpoints (health, version).
"""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_version(client):
    """Test version endpoint."""
    response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "service_version" in data
    assert "cadquery_version" in data
    assert data["service_version"] == "0.1.0"


@pytest.mark.asyncio
async def test_root(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data

