"""
Pytest configuration and fixtures for Eidos geometry service tests.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

# Test client fixture using httpx AsyncClient
@pytest_asyncio.fixture
async def client():
    """Create a test client for the FastAPI app."""
    # Use httpx AsyncClient with ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        yield ac


# Sample PartIR fixtures
@pytest.fixture
def sample_part_ir():
    """Sample Part IR for testing."""
    return {
        "name": "test_part",
        "params": {
            "width": {
                "name": "width",
                "value": 50.0,
                "unit": "mm",
                "tolerance_class": None
            },
            "height": {
                "name": "height",
                "value": 30.0,
                "unit": "mm",
                "tolerance_class": None
            },
            "depth": {
                "name": "depth",
                "value": 80.0,
                "unit": "mm",
                "tolerance_class": None
            }
        },
        "features": [
            {
                "type": "sketch",
                "name": "base_sketch",
                "params": {"plane": "front_plane"},
                "sketch": {
                    "name": "base_sketch",
                    "plane": "front_plane",
                    "entities": [
                        {
                            "id": "rect1",
                            "type": "rectangle",
                            "corner1": [0.0, 0.0],
                            "corner2": [50.0, 30.0]
                        }
                    ],
                    "constraints": [],
                    "dimensions": [
                        {
                            "id": "dim1",
                            "type": "length",
                            "entity_ids": ["rect1"],
                            "value": 50.0,
                            "unit": "mm"
                        }
                    ]
                },
                "critical": False
            },
            {
                "type": "extrude",
                "name": "base_extrude",
                "params": {
                    "sketch": "base_sketch",
                    "distance": 80.0,
                    "operation": "join"
                },
                "critical": False
            }
        ],
        "chains": [],
        "constraints": [],
        "sketches": []
    }


@pytest.fixture
def sample_sketch_ir():
    """Sample Sketch IR for testing."""
    return {
        "name": "test_sketch",
        "plane": "front_plane",
        "entities": [
            {
                "id": "line1",
                "type": "line",
                "start": [0.0, 0.0],
                "end": [50.0, 0.0]
            },
            {
                "id": "line2",
                "type": "line",
                "start": [50.0, 0.0],
                "end": [50.0, 30.0]
            },
            {
                "id": "line3",
                "type": "line",
                "start": [50.0, 30.0],
                "end": [0.0, 30.0]
            },
            {
                "id": "line4",
                "type": "line",
                "start": [0.0, 30.0],
                "end": [0.0, 0.0]
            },
            {
                "id": "circle1",
                "type": "circle",
                "center": [25.0, 15.0],
                "radius": 10.0
            }
        ],
        "constraints": [
            {
                "id": "const1",
                "type": "horizontal",
                "entity_ids": ["line1", "line3"],
                "params": {}
            },
            {
                "id": "const2",
                "type": "vertical",
                "entity_ids": ["line2", "line4"],
                "params": {}
            }
        ],
        "dimensions": [
            {
                "id": "dim1",
                "type": "length",
                "entity_ids": ["line1"],
                "value": 50.0,
                "unit": "mm"
            },
            {
                "id": "dim2",
                "type": "length",
                "entity_ids": ["line2"],
                "value": 30.0,
                "unit": "mm"
            },
            {
                "id": "dim3",
                "type": "diameter",
                "entity_ids": ["circle1"],
                "value": 20.0,
                "unit": "mm"
            }
        ]
    }


@pytest.fixture
def sample_part_ir_minimal():
    """Minimal Part IR for testing (just a simple box)."""
    return {
        "name": "simple_box",
        "params": {
            "size": {
                "name": "size",
                "value": 20.0,
                "unit": "mm",
                "tolerance_class": None
            }
        },
        "features": [
            {
                "type": "sketch",
                "name": "box_sketch",
                "params": {"plane": "front_plane"},
                "sketch": {
                    "name": "box_sketch",
                    "plane": "front_plane",
                    "entities": [
                        {
                            "id": "rect1",
                            "type": "rectangle",
                            "corner1": [0.0, 0.0],
                            "corner2": [20.0, 20.0]
                        }
                    ],
                    "constraints": [],
                    "dimensions": []
                },
                "critical": False
            },
            {
                "type": "extrude",
                "name": "box_extrude",
                "params": {
                    "sketch": "box_sketch",
                    "distance": 20.0,
                    "operation": "join"
                },
                "critical": False
            }
        ],
        "chains": [],
        "constraints": [],
        "sketches": []
    }

