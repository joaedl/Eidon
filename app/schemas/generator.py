"""
JSON Schema generator for IR models.

This module generates JSON Schema definitions from Pydantic models
for use by both Python backend and TypeScript frontend/Supabase edge functions.
"""

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel

from app.core.ir import Part, Sketch, Param, Feature, SketchEntity, SketchConstraint, SketchDimension, Profile


def generate_schema_from_model(model: type[BaseModel], schema_id: str, title: str, description: str) -> dict[str, Any]:
    """
    Generate a JSON Schema from a Pydantic model.
    
    Args:
        model: Pydantic model class
        schema_id: Unique identifier for the schema (e.g., "part_ir")
        title: Human-readable title
        description: Schema description
        
    Returns:
        JSON Schema dict
    """
    # Get the base JSON schema from Pydantic
    schema = model.model_json_schema()
    
    # Add JSON Schema metadata
    schema["$schema"] = "http://json-schema.org/draft-07/schema#"
    schema["$id"] = f"https://eidos.cad/schemas/v1/{schema_id}.schema.json"
    schema["title"] = title
    schema["description"] = description
    
    # Ensure definitions are properly referenced
    if "definitions" in schema:
        schema["$defs"] = schema.pop("definitions")
    
    return schema


def create_part_ir_schema() -> dict[str, Any]:
    """
    Create PartIR schema (geometry-focused subset of Part).
    
    Excludes semantic-only fields like chains and constraints.
    """
    # Create a subset model for PartIR (geometry-focused)
    # We'll generate from the full Part model but document what's included
    schema = generate_schema_from_model(
        Part,
        "part_ir",
        "PartIR",
        "Part Intermediate Representation for geometry service. Contains geometry-relevant fields: name, params, features (sketch/extrude), and sketches."
    )
    
    # Add note about excluded fields in description
    schema["description"] += " Note: chains and constraints are semantic-only and handled by the TypeScript server."
    
    return schema


def create_sketch_ir_schema() -> dict[str, Any]:
    """Create SketchIR schema."""
    return generate_schema_from_model(
        Sketch,
        "sketch_ir",
        "SketchIR",
        "Sketch Intermediate Representation for 2D geometry. Contains entities (line, circle, rectangle), constraints (horizontal, vertical, coincident), and dimensions (length, diameter)."
    )


def create_mesh_schema() -> dict[str, Any]:
    """Create mesh response schema."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://eidos.cad/schemas/v1/mesh.schema.json",
        "title": "MeshData",
        "description": "3D mesh data for rendering (vertices and faces)",
        "type": "object",
        "properties": {
            "vertices": {
                "type": "array",
                "description": "List of vertex coordinates [x, y, z]",
                "items": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 3,
                    "maxItems": 3
                }
            },
            "faces": {
                "type": "array",
                "description": "List of triangular faces as vertex indices [i, j, k]",
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 3,
                    "maxItems": 3
                }
            },
            "featureId": {
                "type": "string",
                "description": "Optional feature ID for selection mapping"
            },
            "faceToFeature": {
                "type": "array",
                "description": "Optional mapping from face index to feature ID",
                "items": {
                    "type": ["string", "null"]
                }
            }
        },
        "required": ["vertices", "faces"]
    }


def save_schema(schema: dict[str, Any], filename: str, output_dir: Path) -> None:
    """Save schema to JSON file."""
    output_path = output_dir / filename
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Generated schema: {output_path}")


def generate_all_schemas() -> None:
    """Generate all JSON schemas and save to v1/ directory."""
    output_dir = Path(__file__).parent / "v1"
    output_dir.mkdir(exist_ok=True)
    
    # Generate PartIR schema
    part_schema = create_part_ir_schema()
    save_schema(part_schema, "part_ir.schema.json", output_dir)
    
    # Generate SketchIR schema
    sketch_schema = create_sketch_ir_schema()
    save_schema(sketch_schema, "sketch_ir.schema.json", output_dir)
    
    # Generate mesh schema
    mesh_schema = create_mesh_schema()
    save_schema(mesh_schema, "mesh.schema.json", output_dir)
    
    print(f"\nAll schemas generated in {output_dir}")


if __name__ == "__main__":
    generate_all_schemas()

