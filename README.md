# Eidos - Geometry Service

A pure geometry service for parametric CAD operations, built with Python, FastAPI, and CadQuery/OpenCascade.

## Overview

Eidos is a geometry service that accepts Part IR (Intermediate Representation) as JSON and performs:
- 3D geometry building via CadQuery/OpenCascade
- Mesh generation for visualization
- Geometry validation and analysis
- Mass property calculations
- Export to STEP, STL, DXF formats
- Assembly operations
- Sketch constraint solving
- Technical drawing generation

The service operates purely on IR (no DSL parsing), making it suitable for integration with TypeScript backends and Supabase edge functions.

## Project Structure

```
Eidos/
├── app/                  # Python FastAPI geometry service
│   ├── api/              # API route handlers
│   │   ├── routes_service.py    # Health, version
│   │   ├── routes_build.py      # Build endpoints
│   │   ├── routes_mesh.py        # Meshing endpoints
│   │   ├── routes_export.py      # Export endpoints
│   │   ├── routes_import.py      # Import endpoints
│   │   ├── routes_analysis.py    # Analysis endpoints
│   │   ├── routes_sketch.py      # Sketch endpoints
│   │   ├── routes_drawing.py     # Drawing endpoints
│   │   ├── routes_assembly.py    # Assembly endpoints
│   │   ├── routes_selection.py   # Selection/topology endpoints
│   │   ├── routes_fea.py          # FEA endpoints
│   │   └── schemas.py            # Request/response models
│   ├── core/             # Core modules
│   │   ├── ir.py                 # IR models (Part, Sketch, etc.)
│   │   ├── builder.py            # Geometry building
│   │   ├── geometry_utils.py     # Geometry utilities
│   │   ├── analysis.py          # Analysis functions
│   │   └── drawing.py           # Drawing generation
│   ├── schemas/          # JSON Schema definitions
│   │   ├── v1/                  # Version 1 schemas
│   │   │   ├── part_ir.schema.json
│   │   │   ├── sketch_ir.schema.json
│   │   │   └── mesh.schema.json
│   │   └── generator.py         # Schema generator
│   └── main.py           # FastAPI entrypoint
├── pyproject.toml        # Python dependencies
└── README.md             # This file
```

## Installation

```bash
pip install -e .
```

## Running

```bash
uvicorn app.main:app --reload --port 8000
```

The geometry service API will be available at `http://localhost:8000`

API documentation (Swagger UI) is available at `http://localhost:8000/docs`

## Testing

Install test dependencies:
```bash
pip install -e ".[dev]"
```

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_build.py
```

See `tests/README.md` for more details on the test suite.

## Deployment

The service can be deployed to Fly.io. See `DEPLOY.md` for deployment instructions.

Quick deployment:
```bash
fly launch
fly deploy
```

## API Endpoints

### Service & Metadata

- **GET /health** - Health check endpoint
  - Returns: `{"status": "ok", "timestamp": "..."}`

- **GET /version** - Version information
  - Returns: Service version, CadQuery version, OCC version

### Core Build (MVP)

- **POST /build/solid** - Build a full solid from PartIR
  - Input: `part_ir` (JSON), `detail_level` (coarse/normal/high), `return_mesh` (bool)
  - Output: Mesh data, bounding box, topology summary, status, warnings

- **POST /build/sketch** - Evaluate a sketch from IR
  - Input: `sketch_ir` (JSON), `resolve_constraints` (bool), `plane` (optional)
  - Output: 2D curves, constraint status, validation issues

- **POST /build/feature** - Build geometry for a single feature
  - Input: `part_ir` (JSON), `feature_id` (string)
  - Output: Feature mesh, bounding box, dependencies

### Meshing & Visualization

- **POST /mesh/solid** - Generate mesh with custom tolerance
  - Input: `part_ir` (JSON), `mesh_params` (linear/angle tolerance)
  - Output: Mesh data, metrics (triangle count, etc.)

- **POST /section/plane** - Compute 2D cross-section at a plane
  - Input: `part_ir` (JSON), `plane` (point + normal)
  - Output: 2D section curves, optional 2D mesh

### Export

- **POST /export/step** - Export part as STEP file
  - Input: `part_ir` (JSON), `step_schema` (AP214/AP242), `name` (optional)
  - Output: Base64-encoded STEP file, size, name

- **POST /export/stl** - Export part as STL file
  - Input: `part_ir` (JSON), `mesh_params` (optional)
  - Output: Base64-encoded STL file, size

- **POST /export/dxf** - Export 2D drawings/sections as DXF
  - Input: `part_ir` or `drawing_ir` (JSON), `view_spec` (optional)
  - Output: Base64-encoded DXF file, size

### Import

- **POST /import/step** - Import STEP file to IR-like representation
  - Input: `file_b64` or `file_url` (STEP file)
  - Output: BRep summary, wrapper IR

### Analysis

- **POST /analysis/geometry-validation** - Deep geometry checks
  - Input: `part_ir` (JSON)
  - Output: Validation issues, `is_valid_solid` flag
  - Checks: Self-intersection, non-manifold edges, tiny faces, failed boolean operations

- **POST /analysis/mass-properties** - Compute mass properties
  - Input: `part_ir` (JSON), `material` or `density` (optional)
  - Output: Volume, area, center of mass, principal moments, principal axes

- **POST /analysis/clearance** - Find clearances between two parts
  - Input: `part_a_ir`, `part_b_ir` (JSON), `min_clearance_threshold` (optional)
  - Output: Minimum distance, locations, collisions

- **POST /analysis/interference** - Boolean intersection check
  - Input: `part_a_ir`, `part_b_ir` (JSON)
  - Output: `has_interference`, intersection volume, optional intersection mesh

- **POST /analysis/tolerance-chain** - Geometry-aware tolerance analysis
  - Input: `part_ir` (JSON), `chain_definition` (surfaces/edges + tolerances)
  - Output: Nominal length, worst-case min/max, optional Monte Carlo stats

### Sketch Constraint Solving

- **POST /sketch/solve** - Run constraint solver on sketch
  - Input: `sketch_ir` (JSON), `initial_guesses` (optional), `locked_entities` (optional)
  - Output: Updated entity coordinates, DOF count, constraint status, errors

- **POST /sketch/infer-constraints** - Suggest constraints from geometry
  - Input: `sketch_ir` (JSON), `tolerance` (float)
  - Output: List of suggested constraints (horizontal, vertical, equal length, coincident, etc.)

### Drafting / Drawing Generation

- **POST /drawing/generate-views** - Generate drawing views
  - Input: `part_ir` (JSON), `view_specs` (front/top/right/isometric, scale, projection)
  - Output: Vector representation of views (edges as polylines, hidden line visibility)

- **POST /drawing/dimension-layout** - Auto-place dimensions on views
  - Input: `part_ir` (JSON), `view_id`, `dimension_preferences` (optional)
  - Output: Dimension entities (start/end points, text, orientation), conflicts

- **POST /drawing/render-svg** - Convert views + dimensions to SVG
  - Input: `drawing_ir` or `views` + `dimensions` (JSON)
  - Output: SVG string

### Assemblies

- **POST /assembly/build** - Build assembly from parts + mates
  - Input: `parts` (list of part IRs), `mate_definitions`, `configuration` (optional)
  - Output: Combined solid, assembly mesh, mate status

- **POST /assembly/interference-check** - Check collisions in assembly
  - Input: `assembly_ir` (JSON)
  - Output: Colliding part pairs, collision volumes, contact points

- **POST /assembly/motion-sweep** - Mechanism sweep analysis
  - Input: `assembly_ir` (JSON), `joint_definitions`, `parameter_sweep`
  - Output: Contact/interference events, optional envelope geometry

### Utilities / Selection Mapping

- **POST /selection/map-pick** - Map 3D pick (ray) to topological elements
  - Input: `part_ir` (JSON), `pick_ray` (origin + direction), `view_transform` (optional)
  - Output: Face/edge/vertex IDs, corresponding feature reference

- **POST /topology/tagging** - Maintain stable IDs between rebuilds
  - Input: `old_solid_signature`, `new_solid_signature`, `mapping_hints` (optional)
  - Output: Mapping from old IDs to new IDs (faces, edges, vertices)

### Simulation / FEA

- **POST /fea/linear-static** - Run linear static FEA (placeholder)
  - Input: `part_ir` (JSON), `material`, `boundary_conditions`, `loads`
  - Output: Displacement field, stress field, max von Mises, max displacement
  - Note: This is a placeholder. Real FEA would be offloaded to a specialized service.

## IR (Intermediate Representation)

The service operates on Part IR and Sketch IR, defined as JSON schemas in `app/schemas/v1/`.

### PartIR Schema

```json
{
  "name": "string",
  "params": {
    "param_name": {
      "name": "string",
      "value": 0.0,
      "unit": "mm",
      "tolerance_class": "string | null"
    }
  },
  "features": [
    {
      "type": "sketch | extrude",
      "name": "string",
      "params": {},
      "sketch": { /* SketchIR */ },
      "critical": false
    }
  ],
  "sketches": [ /* SketchIR */ ]
}
```

### SketchIR Schema

```json
{
  "name": "string",
  "plane": "string",
  "entities": [
    {
      "id": "string",
      "type": "line | circle | rectangle",
      "start": [0.0, 0.0],
      "end": [0.0, 0.0],
      "center": [0.0, 0.0],
      "radius": 0.0,
      "corner1": [0.0, 0.0],
      "corner2": [0.0, 0.0]
    }
  ],
  "constraints": [
    {
      "id": "string",
      "type": "horizontal | vertical | coincident",
      "entity_ids": ["string"],
      "params": {}
    }
  ],
  "dimensions": [
    {
      "id": "string",
      "type": "length | diameter",
      "entity_ids": ["string"],
      "value": 0.0,
      "unit": "mm"
    }
  ]
}
```

JSON schemas are available in `app/schemas/v1/` for validation in TypeScript and other languages.

## Technical Stack

### Technology Stack
- Python 3.11+
- FastAPI - Web framework
- CadQuery - CAD kernel (OpenCascade wrapper)
- Pydantic - Data validation
- Uvicorn - ASGI server

## Development

The codebase is structured for extensibility:
- Modular architecture with clear separation of concerns
- JSON Schema definitions for type safety across languages
- IR-based design (easy to extend with new feature types)
- Comprehensive API documentation via FastAPI/OpenAPI

## Schema Versioning

Schemas are versioned in `app/schemas/v1/`. When making breaking changes:
1. Create a new version directory (e.g., `v2/`)
2. Update `$id` fields in schemas
3. Maintain backward compatibility documentation

## License

MIT
