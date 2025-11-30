"""
API routes for service metadata (health, version).
"""

from fastapi import APIRouter
from datetime import datetime
import cadquery as cq

from app.api.schemas import HealthResponse, VersionResponse

router = APIRouter(tags=["service"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns service status and timestamp.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/version", response_model=VersionResponse)
async def version():
    """
    Version information endpoint.
    
    Returns versions of the geometry service, CadQuery, and OpenCascade.
    """
    try:
        cadquery_version = cq.__version__
    except AttributeError:
        cadquery_version = "unknown"
    
    try:
        # Try to get OCC version
        from OCP import __version__ as occ_version_str
        occ_version = occ_version_str
    except (ImportError, AttributeError):
        try:
            # Alternative: try OCC.Core
            from OCP.Core import __version__ as occ_version_str
            occ_version = occ_version_str
        except (ImportError, AttributeError):
            occ_version = None
    
    return VersionResponse(
        service_version="0.1.0",
        cadquery_version=cadquery_version,
        occ_version=occ_version
    )

