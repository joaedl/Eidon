"""
FastAPI application entry point.

Main application setup with CORS and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_models, routes_analysis, routes_agent

app = FastAPI(
    title="Eidos CAD API",
    description="Parametric CAD system API",
    version="0.1.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(routes_models.router)
app.include_router(routes_analysis.router)
app.include_router(routes_agent.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Eidos CAD API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

