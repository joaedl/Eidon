"""
Intermediate Representation (IR) for parametric CAD models.

This module defines the core data structures that represent a parametric part
in a language-agnostic way. The IR can be generated from DSL, modified by users,
and used to build geometry and perform analyses.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Param(BaseModel):
    """Represents a parameter with value, unit, and optional tolerance class."""
    
    name: str = Field(..., description="Parameter name")
    value: float = Field(..., description="Nominal value")
    unit: str = Field(default="mm", description="Unit (e.g., 'mm', 'in')")
    tolerance_class: Optional[str] = Field(
        default=None, 
        description="Tolerance class (e.g., 'g6', 'H7')"
    )


class Feature(BaseModel):
    """Represents a geometric feature in the part."""
    
    type: Literal["cylinder", "hole", "chamfer", "joint_interface", "link_body", "pocket", "fillet"] = Field(
        ..., 
        description="Type of feature"
    )
    name: str = Field(..., description="Feature name")
    
    # Feature-specific parameters (stored as dict for flexibility in MVP)
    # For cylinder: {"dia_param": "dia", "length_param": "length"}
    # For hole: {"dia_param": "hole_dia", "position": [...]}
    # For chamfer: {"edge": "end", "size_param": "chamfer_size"}
    params: dict[str, str | float] = Field(
        default_factory=dict,
        description="Feature parameters (can reference param names or be direct values)"
    )
    
    critical: bool = Field(
        default=False,
        description="Whether this feature is critical and should have constraints"
    )


class Chain(BaseModel):
    """Represents a 1D dimensional chain (stackup) for tolerance analysis."""
    
    name: str = Field(..., description="Chain name")
    terms: list[str] = Field(
        ..., 
        description="List of parameter names that make up the chain"
    )
    target_value: Optional[float] = Field(
        default=None,
        description="Target nominal value for the chain (optional)"
    )
    target_tolerance: Optional[float] = Field(
        default=None,
        description="Target total tolerance (±value) for the chain (optional)"
    )


class Constraint(BaseModel):
    """Represents a geometric constraint between entities."""
    
    name: str = Field(..., description="Constraint name")
    type: Literal["coincident", "parallel", "perpendicular", "distance", "angle", "reference"] = Field(
        ...,
        description="Type of constraint"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="References to features/edges/faces by name"
    )
    params: dict[str, float | str] = Field(
        default_factory=dict,
        description="Constraint parameters (distance, angle, etc.)"
    )


class ValidationIssue(BaseModel):
    """Represents a validation issue found in a part."""
    
    code: str = Field(..., description="Issue code (e.g., 'UNCONSTRAINED_FEATURE')")
    severity: Literal["info", "warning", "error"] = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable message")
    related_params: list[str] = Field(default_factory=list, description="Related parameter names")
    related_features: list[str] = Field(default_factory=list, description="Related feature names")
    related_chains: list[str] = Field(default_factory=list, description="Related chain names")


class Part(BaseModel):
    """Represents a complete parametric part."""
    
    name: str = Field(..., description="Part name")
    params: dict[str, Param] = Field(
        default_factory=dict,
        description="Dictionary of parameters by name"
    )
    features: list[Feature] = Field(
        default_factory=list,
        description="List of features in the part"
    )
    chains: list[Chain] = Field(
        default_factory=list,
        description="List of dimensional chains for analysis"
    )
    constraints: list[Constraint] = Field(
        default_factory=list,
        description="List of geometric constraints"
    )

