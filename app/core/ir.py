"""
Intermediate Representation (IR) for parametric CAD models.

This module defines the core data structures that represent a parametric part
in a language-agnostic way. The IR can be generated from DSL, modified by users,
and used to build geometry and perform analyses.
"""

from typing import Literal, Optional, Any
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
    
    # MVP: Only sketch and extrude supported
    type: Literal["sketch", "extrude"] = Field(
        ..., 
        description="Type of feature (MVP: only sketch and extrude)"
    )
    name: str = Field(..., description="Feature name")
    
    # Feature-specific parameters (stored as dict for flexibility in MVP)
    # MVP: Only sketch and extrude supported
    # For sketch: {"plane": "right_plane"} or {"plane": "face:feature_name"} (sketch object embedded in sketch field)
    # For extrude: {
    #   "sketch": "sketch_name", 
    #   "distance": value | "through_all" | "to_next", 
    #   "operation": "join"|"cut",
    #   "direction": [x, y, z] | "normal" | "reverse" (optional, defaults to sketch plane normal)
    # }
    params: dict[str, str | float | dict | list] = Field(
        default_factory=dict,
        description="Feature parameters. For extrude: 'sketch' (sketch name), 'distance' (number | 'through_all' | 'to_next'), 'operation' ('join' | 'cut'), 'direction' (optional: 'normal' | 'reverse' | [x,y,z]). For sketch: 'plane' (plane reference). Can reference param names or be direct values."
    )
    
    # For sketch features, embed the Sketch directly
    sketch: Optional["Sketch"] = Field(None, description="Embedded sketch (for sketch features)")
    
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


# Sketch models for 2D sketch mode
class SketchEntity(BaseModel):
    """Represents a 2D sketch entity (line, arc, circle, rectangle)."""
    
    id: str = Field(..., description="Unique identifier for the entity")
    # MVP: Only line, circle, and rectangle supported (no arc)
    type: Literal["line", "circle", "rectangle"] = Field(..., description="Entity type")
    
    # Geometry fields (varies by type)
    # For line: start and end points
    start: Optional[tuple[float, float]] = Field(None, description="Start point (x, y) for line/arc")
    end: Optional[tuple[float, float]] = Field(None, description="End point (x, y) for line/arc")
    
    # For circle: center and radius
    center: Optional[tuple[float, float]] = Field(None, description="Center point (x, y) for circle/arc")
    radius: Optional[float] = Field(None, description="Radius for circle/arc")
    
    # For rectangle: corner points
    corner1: Optional[tuple[float, float]] = Field(None, description="First corner for rectangle")
    corner2: Optional[tuple[float, float]] = Field(None, description="Second corner for rectangle")
    
    # MVP: Arc not supported - removed start_angle and end_angle


class SketchConstraint(BaseModel):
    """Represents a geometric constraint on sketch entities."""
    
    id: str = Field(..., description="Unique identifier for the constraint")
    # MVP: Only horizontal, vertical, and coincident supported
    type: Literal["horizontal", "vertical", "coincident"] = Field(
        ..., description="Constraint type"
    )
    entity_ids: list[str] = Field(..., description="IDs of entities involved in the constraint")
    params: dict[str, Any] = Field(default_factory=dict, description="Additional constraint parameters")


class SketchDimension(BaseModel):
    """Represents a dimension on sketch entities."""
    
    id: str = Field(..., description="Unique identifier for the dimension")
    # MVP: Only length and diameter supported
    type: Literal["length", "diameter"] = Field(..., description="Dimension type")
    entity_ids: list[str] = Field(..., description="IDs of entities being dimensioned (1 or 2)")
    value: float = Field(..., description="Dimension value")
    unit: str = Field(default="mm", description="Unit for the dimension")


class Profile(BaseModel):
    """Represents a closed profile region in a sketch (outer boundary or hole)."""
    
    id: str = Field(..., description="Unique identifier for the profile")
    type: Literal["outer", "hole"] = Field(..., description="Profile type: outer boundary or inner hole")
    entity_ids: list[str] = Field(..., description="IDs of entities that form this closed profile")
    area: Optional[float] = Field(None, description="Calculated area of the profile (for sorting)")
    is_outer: bool = Field(..., description="True if this is the outer boundary, False if it's a hole")


class Sketch(BaseModel):
    """Represents a 2D sketch on a plane."""
    
    name: str = Field(..., description="Sketch name")
    plane: str = Field(
        ..., 
        description="Plane reference. Can be: "
        "'front_plane', 'right_plane', 'top_plane' (standard planes), "
        "or 'face:feature_name' (default face of a feature), "
        "or 'face:feature_name:index:N' (face by index, 0-based), "
        "or 'face:feature_name:normal:+X' (face with normal in +X direction), "
        "or 'face:feature_name:normal:[1,0,0]' (face with specific normal vector), "
        "or 'face:feature_name:center:[x,y,z]' (face containing point), "
        "or 'face:feature_name:largest' (largest face by area), "
        "or 'face:feature_name:smallest' (smallest face by area), "
        "or 'face:feature_name:top' (top face by Z), "
        "or 'face:feature_name:bottom' (bottom face by Z), "
        "or 'face:feature_name:front' (front face by Y), "
        "or 'face:feature_name:back' (back face by Y), "
        "or 'face:feature_name:right' (right face by X), "
        "or 'face:feature_name:left' (left face by X)"
    )
    entities: list[SketchEntity] = Field(default_factory=list, description="Sketch entities")
    constraints: list[SketchConstraint] = Field(default_factory=list, description="Geometric constraints")
    dimensions: list[SketchDimension] = Field(default_factory=list, description="Dimensions")
    profiles: list[Profile] = Field(
        default_factory=list,
        description="Detected closed profiles (outer boundary and holes). Auto-detected if not provided."
    )


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
    sketches: list[Sketch] = Field(default_factory=list, description="2D sketches (can also be embedded in sketch features)")

