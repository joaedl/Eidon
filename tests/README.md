# Test Suite

Comprehensive test suite for Eidos Geometry Service endpoints.

## Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_service.py` - Service endpoints (health, version)
- `test_build.py` - Build endpoints (solid, sketch, feature)
- `test_mesh.py` - Meshing and visualization endpoints
- `test_export.py` - Export endpoints (STEP, STL, DXF)
- `test_import.py` - Import endpoints (STEP)
- `test_analysis.py` - Analysis endpoints (validation, mass properties, clearance, interference, tolerance-chain)
- `test_sketch.py` - Sketch constraint solving endpoints
- `test_drawing.py` - Drafting and drawing generation endpoints
- `test_assembly.py` - Assembly endpoints
- `test_selection.py` - Selection mapping and topology utilities
- `test_fea.py` - FEA endpoints

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_build.py
```

### Run specific test
```bash
pytest tests/test_build.py::test_build_solid
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

## Test Fixtures

The test suite includes several fixtures in `conftest.py`:

- `client` - FastAPI TestClient instance
- `sample_part_ir` - Complete Part IR with sketch and extrude features
- `sample_sketch_ir` - Complete Sketch IR with entities, constraints, and dimensions
- `sample_part_ir_minimal` - Minimal Part IR for simple tests

## Test Coverage

The test suite covers all 33 endpoints:

### MVP Endpoints (8)
- ✅ GET /health
- ✅ GET /version
- ✅ POST /build/solid
- ✅ POST /build/sketch
- ✅ POST /export/step
- ✅ POST /export/stl
- ✅ POST /analysis/geometry-validation
- ✅ POST /analysis/mass-properties

### LATER Endpoints (25)
- ✅ POST /build/feature
- ✅ POST /mesh/solid
- ✅ POST /section/plane
- ✅ POST /export/dxf
- ✅ POST /import/step
- ✅ POST /analysis/clearance
- ✅ POST /analysis/interference
- ✅ POST /analysis/tolerance-chain
- ✅ POST /sketch/solve
- ✅ POST /sketch/infer-constraints
- ✅ POST /drawing/generate-views
- ✅ POST /drawing/dimension-layout
- ✅ POST /drawing/render-svg
- ✅ POST /assembly/build
- ✅ POST /assembly/interference-check
- ✅ POST /assembly/motion-sweep
- ✅ POST /selection/map-pick
- ✅ POST /topology/tagging
- ✅ POST /fea/linear-static

## Notes

- Tests use FastAPI's `TestClient` for integration testing
- All tests validate response structure and status codes
- Some endpoints may return placeholder data (e.g., FEA, constraint solving)
- Tests are designed to be run against the actual service implementation

