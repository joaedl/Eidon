# JSON Schema Definitions

This directory contains JSON Schema definitions for the Eidos geometry service IR models. These schemas are used by both the Python backend and TypeScript frontend/Supabase edge functions to ensure type safety and validation.

## Structure

- `v1/` - Version 1 schemas (MVP)
  - `part_ir.schema.json` - Part Intermediate Representation
  - `sketch_ir.schema.json` - Sketch Intermediate Representation
  - `mesh.schema.json` - Mesh data structure

## Schema Versioning

Schemas are versioned by directory (`v1/`, `v2/`, etc.). When making breaking changes:

1. Create a new version directory
2. Update the `$id` field in schemas to reflect the new version
3. Maintain backward compatibility documentation

## Extensibility

Schemas use JSON Schema composition features:
- `allOf` - Combine multiple schemas
- `$ref` - Reference other schemas
- `$defs` - Local definitions

To extend schemas:
1. Add new optional fields (non-breaking)
2. Use `allOf` to compose with base schema (breaking changes go to new version)

## Generation

Schemas are generated from Pydantic models using:

```bash
python -m app.schemas.generator
```

This reads the models from `app.core.ir` and generates JSON Schema files in `v1/`.

## Usage

### Python (Backend)
```python
from app.core.ir import Part
part = Part.model_validate(json_data)  # Validates against Pydantic model
```

### TypeScript
```typescript
import partIrSchema from './schemas/v1/part_ir.schema.json';
// Use with a JSON Schema validator library
```

## PartIR vs Part

`PartIR` is a geometry-focused subset of the full `Part` model:
- **Included**: `name`, `params`, `features` (sketch/extrude), `sketches`
- **Excluded**: `chains`, `constraints` (semantic-only, handled by TS server)

The schema is generated from the full `Part` model but documents which fields are used by the geometry service.

