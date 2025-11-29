"""
Text edit models for DSL editing.

This module defines models for representing text edits to DSL files,
similar to how Cursor and other code editors handle edits.
"""

from pydantic import BaseModel, Field


class TextEdit(BaseModel):
    """
    Represents a single text edit operation.
    
    Edits are applied in order, with start/end being character offsets
    in the original text. The replacement string replaces the text from
    start to end (exclusive).
    """
    start: int = Field(..., description="Start character offset (0-based)")
    end: int = Field(..., description="End character offset (exclusive)")
    replacement: str = Field(..., description="Text to insert at this position")


def apply_text_edits_to_dsl(dsl_text: str, edits: list[TextEdit]) -> str:
    """
    Apply a list of text edits to DSL text.
    
    Edits are applied in reverse order (by start position) to avoid
    offset shifts when applying multiple edits.
    
    Args:
        dsl_text: Original DSL text
        edits: List of text edits to apply
        
    Returns:
        Modified DSL text
        
    Raises:
        ValueError: If edit ranges are invalid
    """
    if not edits:
        return dsl_text
    
    # Sort edits by start position in descending order
    # This ensures we apply edits from end to beginning, avoiding offset shifts
    sorted_edits = sorted(edits, key=lambda e: e.start, reverse=True)
    
    result = dsl_text
    for edit in sorted_edits:
        # Validate edit range
        if edit.start < 0 or edit.end > len(result):
            raise ValueError(f"Edit range [{edit.start}, {edit.end}) is out of bounds for text of length {len(result)}")
        if edit.start > edit.end:
            raise ValueError(f"Edit start ({edit.start}) must be <= end ({edit.end})")
        
        # Apply the edit
        result = result[:edit.start] + edit.replacement + result[edit.end:]
    
    return result

