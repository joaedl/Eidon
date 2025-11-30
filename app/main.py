"""
FastAPI application entry point.

Main application setup with CORS and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Geometry service routes
from app.api import (
    routes_service, routes_build, routes_export, routes_analysis,
    routes_mesh, routes_import, routes_sketch, routes_drawing,
    routes_assembly, routes_selection, routes_fea
)

app = FastAPI(
    title="Eidos Geometry Service",
    description="Geometry service API for CAD operations",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for service API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register geometry service routes (MVP)
app.include_router(routes_service.router)
app.include_router(routes_build.router)
app.include_router(routes_export.router)
app.include_router(routes_analysis.router)

# Register LATER endpoints
app.include_router(routes_mesh.router)
app.include_router(routes_import.router)
app.include_router(routes_sketch.router)
app.include_router(routes_drawing.router)
app.include_router(routes_assembly.router)
app.include_router(routes_selection.router)
app.include_router(routes_fea.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Eidos Geometry Service",
        "version": "0.1.0",
        "endpoints": {
            "service": ["/health", "/version"],
            "build": ["/build/solid", "/build/sketch", "/build/feature"],
            "mesh": ["/mesh/solid", "/section/plane"],
            "export": ["/export/step", "/export/stl", "/export/dxf"],
            "import": ["/import/step"],
            "analysis": [
                "/analysis/geometry-validation",
                "/analysis/mass-properties",
                "/analysis/clearance",
                "/analysis/interference",
                "/analysis/tolerance-chain"
            ],
            "sketch": ["/sketch/solve", "/sketch/infer-constraints"],
            "drawing": [
                "/drawing/generate-views",
                "/drawing/dimension-layout",
                "/drawing/render-svg"
            ],
            "assembly": [
                "/assembly/build",
                "/assembly/interference-check",
                "/assembly/motion-sweep"
            ],
            "selection": [
                "/selection/map-pick",
                "/topology/tagging"
            ],
            "fea": ["/fea/linear-static"]
        }
    }

