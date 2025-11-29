"""
DSL Store: manages DSL text representation of parts.

This module provides a simple in-memory store for DSL files, with validation
and parsing capabilities. In the future, this could be extended to use
actual file storage or a database.
"""

from typing import Optional
from app.core.ir import Part
from app.core.dsl_parser import parse_dsl_to_ir
from app.core.dsl_generator import ir_to_dsl
from app.core.builder import build_cad_model
from app.core.analysis import validate_part


# Simple in-memory store for MVP
# Keyed by part_id (for now, just "current" for single active part)
_dsl_store: dict[str, str] = {}
_part_store: dict[str, Part] = {}


def get_current_dsl(part_id: str = "current") -> Optional[str]:
    """
    Get the current DSL text for a part.
    
    Args:
        part_id: Identifier for the part (default: "current")
        
    Returns:
        DSL text string, or None if not found
    """
    return _dsl_store.get(part_id)


def get_current_part(part_id: str = "current") -> Optional[Part]:
    """
    Get the current Part IR for a part.
    
    Args:
        part_id: Identifier for the part (default: "current")
        
    Returns:
        Part IR, or None if not found
    """
    return _part_store.get(part_id)


def set_part(part: Part, dsl: Optional[str] = None, part_id: str = "current") -> None:
    """
    Store a part and optionally its DSL representation.
    
    If DSL is not provided, it will be generated from the Part IR.
    
    Args:
        part: The Part IR to store
        dsl: Optional DSL text (will be generated if not provided)
        part_id: Identifier for the part (default: "current")
    """
    if dsl is None:
        dsl = ir_to_dsl(part)
    
    _part_store[part_id] = part
    _dsl_store[part_id] = dsl


def update_dsl(part_id: str, new_dsl: str) -> tuple[Part, list[str]]:
    """
    Update DSL text, parse it, validate, and rebuild geometry.
    
    This is the main entry point for DSL edits. It:
    1. Parses the DSL into Part IR
    2. Validates that the geometry can be built
    3. Stores both the DSL and Part IR
    
    Args:
        part_id: Identifier for the part (default: "current")
        new_dsl: The new DSL text
        
    Returns:
        Tuple of (Part IR, list of error messages)
        If successful, error list is empty.
        
    Raises:
        ValueError: If parsing fails
        Exception: If geometry build fails
    """
    errors: list[str] = []
    
    try:
        # Parse DSL to IR
        part = parse_dsl_to_ir(new_dsl)
    except Exception as e:
        errors.append(f"DSL parsing failed: {str(e)}")
        raise ValueError(f"Failed to parse DSL: {str(e)}")
    
    try:
        # Validate that geometry can be built
        build_cad_model(part)
    except Exception as e:
        errors.append(f"Geometry build failed: {str(e)}")
        raise ValueError(f"Failed to build geometry: {str(e)}")
    
    # Run validation
    validation_issues = validate_part(part)
    for issue in validation_issues:
        if issue.severity == "error":
            errors.append(f"Validation error: {issue.message}")
    
    # Store the updated part and DSL
    _part_store[part_id] = part
    _dsl_store[part_id] = new_dsl
    
    return part, errors


def clear_part(part_id: str = "current") -> None:
    """
    Clear a part from the store.
    
    Args:
        part_id: Identifier for the part (default: "current")
    """
    _dsl_store.pop(part_id, None)
    _part_store.pop(part_id, None)

