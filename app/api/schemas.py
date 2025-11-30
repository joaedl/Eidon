"""
Request and response models for geometry service API endpoints.

These Pydantic models define the API contract for all geometry service endpoints.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

from app.core.ir import Part, Sketch


# ============================================================================
# Service & Metadata
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="ok", description="Service status")
    timestamp: str = Field(..., description="ISO timestamp")


class VersionResponse(BaseModel):
    """Version information response."""
    service_version: str = Field(..., description="Geometry service version")
    cadquery_version: str = Field(..., description="CadQuery library version")
    occ_version: Optional[str] = Field(None, description="OpenCascade version")


# ============================================================================
# Build Endpoints
# ============================================================================

class BuildSolidRequest(BaseModel):
    """Request for building a solid from PartIR."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    detail_level: Literal["coarse", "normal", "high"] = Field(
        default="normal",
        description="Mesh detail level (affects tessellation tolerance)"
    )
    return_mesh: bool = Field(default=True, description="Whether to return mesh data")


class BoundingBox(BaseModel):
    """3D bounding box."""
    min: list[float] = Field(..., description="Minimum corner [x, y, z]")
    max: list[float] = Field(..., description="Maximum corner [x, y, z]")


class TopologySummary(BaseModel):
    """Topology summary of a solid."""
    face_count: int = Field(..., description="Number of faces")
    edge_count: int = Field(..., description="Number of edges")
    vertex_count: int = Field(..., description="Number of vertices")


class MeshData(BaseModel):
    """Mesh data for 3D rendering."""
    vertices: list[list[float]] = Field(..., description="List of [x, y, z] coordinates")
    faces: list[list[int]] = Field(..., description="List of triangular face indices [i, j, k]")
    featureId: Optional[str] = Field(None, description="Optional feature ID")
    faceToFeature: Optional[list[Optional[str]]] = Field(None, description="Face-to-feature mapping")


class BuildSolidResponse(BaseModel):
    """Response from building a solid."""
    mesh: Optional[MeshData] = Field(None, description="Mesh data (if return_mesh=True)")
    bounding_box: BoundingBox = Field(..., description="3D bounding box")
    topology_summary: TopologySummary = Field(..., description="Topology statistics")
    status: str = Field(default="ok", description="Build status")
    warnings: list[str] = Field(default_factory=list, description="Build warnings")


class BuildSketchRequest(BaseModel):
    """Request for building/evaluating a sketch."""
    sketch_ir: dict = Field(..., description="Sketch IR as JSON dict")
    resolve_constraints: bool = Field(
        default=False,
        description="Whether to solve constraints (placeholder for MVP)"
    )
    plane: Optional[str] = Field(None, description="Plane override (optional)")


class Curve2D(BaseModel):
    """2D curve representation."""
    type: Literal["line", "circle", "arc", "rectangle"] = Field(..., description="Curve type")
    points: list[list[float]] = Field(..., description="Points defining the curve [[x, y], ...]")
    radius: Optional[float] = Field(None, description="Radius for circles/arcs")
    center: Optional[list[float]] = Field(None, description="Center point [x, y] for circles/arcs")


class ConstraintStatus(BaseModel):
    """Constraint solving status."""
    is_fully_constrained: bool = Field(..., description="Whether sketch is fully constrained")
    is_overconstrained: bool = Field(..., description="Whether sketch is overconstrained")
    degrees_of_freedom: Optional[int] = Field(None, description="Estimated DOF (if available)")


class BuildSketchResponse(BaseModel):
    """Response from building a sketch."""
    curves: list[Curve2D] = Field(..., description="2D curve representations")
    constraint_status: ConstraintStatus = Field(..., description="Constraint solving status")
    issues: list[dict] = Field(default_factory=list, description="Validation issues")


# ============================================================================
# Export Endpoints
# ============================================================================

class ExportStepRequest(BaseModel):
    """Request for STEP export."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    step_schema: Literal["AP214", "AP242"] = Field(default="AP214", description="STEP schema version")
    name: Optional[str] = Field(None, description="Optional part name for file")


class ExportStepResponse(BaseModel):
    """Response from STEP export."""
    file_b64: str = Field(..., description="Base64-encoded STEP file")
    size_bytes: int = Field(..., description="File size in bytes")
    name: str = Field(..., description="File name")


class MeshParams(BaseModel):
    """Mesh generation parameters."""
    linear_tolerance: Optional[float] = Field(None, description="Linear tolerance for meshing")
    angle_tolerance: Optional[float] = Field(None, description="Angle tolerance for meshing")


class ExportStlRequest(BaseModel):
    """Request for STL export."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    mesh_params: Optional[MeshParams] = Field(None, description="Optional mesh parameters")


class ExportStlResponse(BaseModel):
    """Response from STL export."""
    file_b64: str = Field(..., description="Base64-encoded STL file")
    size_bytes: int = Field(..., description="File size in bytes")


# ============================================================================
# Analysis Endpoints
# ============================================================================

class GeometryValidationRequest(BaseModel):
    """Request for geometry validation."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")


class GeometryIssue(BaseModel):
    """Geometry validation issue."""
    code: str = Field(..., description="Issue code (e.g., 'SELF_INTERSECTION')")
    message: str = Field(..., description="Human-readable message")
    severity: Literal["info", "warning", "error"] = Field(..., description="Severity level")
    location: Optional[dict] = Field(None, description="Location information (if available)")


class GeometryValidationResponse(BaseModel):
    """Response from geometry validation."""
    issues: list[GeometryIssue] = Field(..., description="List of validation issues")
    is_valid_solid: bool = Field(..., description="Whether the solid is valid")


class Material(BaseModel):
    """Material definition."""
    name: str = Field(..., description="Material name")
    density: float = Field(..., description="Density in kg/m³")


class MassPropertiesRequest(BaseModel):
    """Request for mass properties calculation."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    material: Optional[Material] = Field(None, description="Material definition")
    density: Optional[float] = Field(None, description="Density in kg/m³ (alternative to material)")


class MassPropertiesResponse(BaseModel):
    """Response from mass properties calculation."""
    volume: float = Field(..., description="Volume in m³")
    area: float = Field(..., description="Surface area in m²")
    center_of_mass: list[float] = Field(..., description="Center of mass [x, y, z]")
    principal_moments: list[float] = Field(..., description="Principal moments of inertia [Ixx, Iyy, Izz]")
    principal_axes: list[list[float]] = Field(..., description="Principal axes [[x, y, z], ...]")


# ============================================================================
# Build Extensions (LATER)
# ============================================================================

class BuildFeatureRequest(BaseModel):
    """Request for building a single feature."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    feature_id: str = Field(..., description="Feature ID to build")


class BuildFeatureResponse(BaseModel):
    """Response from building a feature."""
    mesh: MeshData = Field(..., description="Mesh data for the feature")
    bounding_box: BoundingBox = Field(..., description="Bounding box of the feature")
    affected_region: Optional[dict] = Field(None, description="Affected region information")
    depends_on_features: list[str] = Field(default_factory=list, description="Feature dependencies")


# ============================================================================
# Meshing & Visualization (LATER)
# ============================================================================

class MeshSolidRequest(BaseModel):
    """Request for meshing a solid with custom parameters."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    mesh_params: MeshParams = Field(..., description="Mesh generation parameters")


class MeshSolidResponse(BaseModel):
    """Response from meshing a solid."""
    mesh: MeshData = Field(..., description="Generated mesh")
    metrics: dict = Field(..., description="Mesh metrics (triangle count, etc.)")


class PlaneDefinition(BaseModel):
    """Plane definition for sectioning."""
    point: list[float] = Field(..., description="Point on plane [x, y, z]")
    normal: list[float] = Field(..., description="Plane normal vector [x, y, z]")


class SectionPlaneRequest(BaseModel):
    """Request for computing a 2D section."""
    part_ir: dict = Field(..., description="Part IR as JSON dict")
    plane: PlaneDefinition = Field(..., description="Plane definition")


class SectionCurve(BaseModel):
    """2D section curve."""
    type: str = Field(..., description="Curve type (line, arc, etc.)")
    points: list[list[float]] = Field(..., description="Points defining the curve")


class SectionPlaneResponse(BaseModel):
    """Response from section computation."""
    curves: list[SectionCurve] = Field(..., description="2D section curves")
    mesh_2d: Optional[MeshData] = Field(None, description="Optional 2D mesh")


# ============================================================================
# Export Extensions (LATER)
# ============================================================================

class ExportDxfRequest(BaseModel):
    """Request for DXF export."""
    part_ir: Optional[dict] = Field(None, description="Part IR (if exporting from part)")
    drawing_ir: Optional[dict] = Field(None, description="Drawing IR (if exporting drawing)")
    view_spec: Optional[dict] = Field(None, description="View specification (front/top/side, scale)")


class ExportDxfResponse(BaseModel):
    """Response from DXF export."""
    file_b64: str = Field(..., description="Base64-encoded DXF file")
    size_bytes: int = Field(..., description="File size in bytes")


class ImportStepRequest(BaseModel):
    """Request for STEP import."""
    file_b64: Optional[str] = Field(None, description="Base64-encoded STEP file")
    file_url: Optional[str] = Field(None, description="URL to STEP file")


class ImportStepResponse(BaseModel):
    """Response from STEP import."""
    brep_summary: dict = Field(..., description="BRep summary")
    wrapper_ir: Optional[dict] = Field(None, description="Wrapper IR for referencing imported geometry")


# ============================================================================
# Analysis Extensions (LATER)
# ============================================================================

class ClearanceRequest(BaseModel):
    """Request for clearance analysis."""
    part_a_ir: dict = Field(..., description="First part IR")
    part_b_ir: dict = Field(..., description="Second part IR")
    min_clearance_threshold: Optional[float] = Field(None, description="Minimum clearance threshold")


class ClearanceResponse(BaseModel):
    """Response from clearance analysis."""
    min_distance: float = Field(..., description="Minimum distance between bodies")
    locations: list[dict] = Field(..., description="Locations of minimum clearance")
    collisions: list[dict] = Field(default_factory=list, description="Collisions if any")


class InterferenceRequest(BaseModel):
    """Request for interference analysis."""
    part_a_ir: dict = Field(..., description="First part IR")
    part_b_ir: dict = Field(..., description="Second part IR")


class InterferenceResponse(BaseModel):
    """Response from interference analysis."""
    has_interference: bool = Field(..., description="Whether interference exists")
    intersection_volume: Optional[float] = Field(None, description="Intersection volume")
    intersection_mesh: Optional[MeshData] = Field(None, description="Optional intersection mesh")


class ToleranceChainRequest(BaseModel):
    """Request for tolerance chain analysis."""
    part_ir: dict = Field(..., description="Part IR")
    chain_definition: dict = Field(..., description="Chain definition (surfaces/edges + tolerances)")


class ToleranceChainResponse(BaseModel):
    """Response from tolerance chain analysis."""
    nominal_length: float = Field(..., description="Nominal chain length")
    worst_case_min: float = Field(..., description="Worst-case minimum")
    worst_case_max: float = Field(..., description="Worst-case maximum")
    monte_carlo_stats: Optional[dict] = Field(None, description="Optional Monte Carlo statistics")


# ============================================================================
# Sketch Constraint Solving (LATER)
# ============================================================================

class SketchSolveRequest(BaseModel):
    """Request for sketch constraint solving."""
    sketch_ir: dict = Field(..., description="Sketch IR")
    initial_guesses: Optional[dict] = Field(None, description="Initial guesses for entities")
    locked_entities: Optional[list[str]] = Field(None, description="IDs of locked entities")


class SketchSolveResponse(BaseModel):
    """Response from sketch constraint solving."""
    updated_entities: list[dict] = Field(..., description="Updated entity coordinates")
    degrees_of_freedom: int = Field(..., description="Remaining DOF count")
    constraint_status: ConstraintStatus = Field(..., description="Constraint status")
    errors: list[str] = Field(default_factory=list, description="Errors if inconsistent")


class InferConstraintsRequest(BaseModel):
    """Request for constraint inference."""
    sketch_ir: dict = Field(..., description="Sketch IR (mostly unconstrained)")
    tolerance: float = Field(default=1e-3, description="Tolerance for detection")


class InferConstraintsResponse(BaseModel):
    """Response from constraint inference."""
    suggested_constraints: list[dict] = Field(..., description="List of suggested constraints")


# ============================================================================
# Drafting / Drawing Generation (LATER)
# ============================================================================

class ViewSpec(BaseModel):
    """View specification."""
    type: Literal["front", "top", "right", "isometric"] = Field(..., description="View type")
    scale: float = Field(default=1.0, description="Scale factor")
    projection: Literal["first_angle", "third_angle"] = Field(default="third_angle", description="Projection type")


class GenerateViewsRequest(BaseModel):
    """Request for generating drawing views."""
    part_ir: dict = Field(..., description="Part IR")
    view_specs: list[ViewSpec] = Field(..., description="View specifications")


class DrawingEdge(BaseModel):
    """Drawing edge representation."""
    type: str = Field(..., description="Edge type (visible, hidden)")
    points: list[list[float]] = Field(..., description="Edge points")


class DrawingView(BaseModel):
    """Drawing view representation."""
    view_id: str = Field(..., description="View identifier")
    view_type: str = Field(..., description="View type")
    edges: list[DrawingEdge] = Field(..., description="Edges in the view")


class GenerateViewsResponse(BaseModel):
    """Response from view generation."""
    views: list[DrawingView] = Field(..., description="Generated views")


class DimensionLayoutRequest(BaseModel):
    """Request for dimension layout."""
    part_ir: dict = Field(..., description="Part IR")
    view_id: str = Field(..., description="View ID or spec")
    dimension_preferences: Optional[dict] = Field(None, description="Dimension preferences")


class DimensionEntity(BaseModel):
    """Dimension entity."""
    start: list[float] = Field(..., description="Start point [x, y]")
    end: list[float] = Field(..., description="End point [x, y]")
    text: str = Field(..., description="Dimension text")
    orientation: float = Field(..., description="Orientation angle")


class DimensionLayoutResponse(BaseModel):
    """Response from dimension layout."""
    dimensions: list[DimensionEntity] = Field(..., description="Placed dimensions")
    conflicts: list[dict] = Field(default_factory=list, description="Potential conflicts/overlaps")


class RenderSvgRequest(BaseModel):
    """Request for SVG rendering."""
    drawing_ir: Optional[dict] = Field(None, description="Drawing IR")
    views: Optional[list[DrawingView]] = Field(None, description="Views (if not using drawing_ir)")
    dimensions: Optional[list[DimensionEntity]] = Field(None, description="Dimensions")


class RenderSvgResponse(BaseModel):
    """Response from SVG rendering."""
    svg: str = Field(..., description="SVG string")


# ============================================================================
# Assemblies (LATER)
# ============================================================================

class MateDefinition(BaseModel):
    """Mate definition."""
    type: Literal["planar", "concentric", "distance", "coincident"] = Field(..., description="Mate type")
    part_a: str = Field(..., description="First part reference")
    part_b: str = Field(..., description="Second part reference")
    params: dict = Field(default_factory=dict, description="Mate parameters")


class AssemblyBuildRequest(BaseModel):
    """Request for building an assembly."""
    parts: list[dict] = Field(..., description="List of part IRs")
    mate_definitions: list[MateDefinition] = Field(..., description="Mate definitions")
    configuration: Optional[dict] = Field(None, description="Assembly configuration")


class AssemblyBuildResponse(BaseModel):
    """Response from assembly build."""
    combined_solid: Optional[dict] = Field(None, description="Combined solid in global coordinates")
    mesh: Optional[MeshData] = Field(None, description="Assembly mesh")
    mate_status: dict = Field(..., description="Mate status (solved, overconstrained, etc.)")


class AssemblyInterferenceRequest(BaseModel):
    """Request for assembly interference check."""
    assembly_ir: dict = Field(..., description="Assembly IR (or list of parts + mates)")


class AssemblyInterferenceResponse(BaseModel):
    """Response from assembly interference check."""
    colliding_pairs: list[dict] = Field(..., description="Colliding part pairs")
    collision_volumes: Optional[list[MeshData]] = Field(None, description="Collision volumes")
    contact_points: Optional[list[list[float]]] = Field(None, description="Contact points")


class JointDefinition(BaseModel):
    """Joint definition for motion sweep."""
    name: str = Field(..., description="Joint name")
    type: str = Field(..., description="Joint type")
    params: dict = Field(default_factory=dict, description="Joint parameters")


class MotionSweepRequest(BaseModel):
    """Request for motion sweep."""
    assembly_ir: dict = Field(..., description="Assembly IR")
    joint_definitions: list[JointDefinition] = Field(..., description="Joint definitions")
    parameter_sweep: dict = Field(..., description="Parameter sweep (e.g., joint angle range)")


class MotionSweepResponse(BaseModel):
    """Response from motion sweep."""
    contact_events: list[dict] = Field(..., description="Contact/interference events")
    envelope_geometry: Optional[MeshData] = Field(None, description="Optional envelope geometry")


# ============================================================================
# Utilities / Selection Mapping (LATER)
# ============================================================================

class PickRay(BaseModel):
    """Pick ray definition."""
    origin: list[float] = Field(..., description="Ray origin [x, y, z]")
    direction: list[float] = Field(..., description="Ray direction [x, y, z]")


class MapPickRequest(BaseModel):
    """Request for mapping a 3D pick."""
    part_ir: dict = Field(..., description="Part IR")
    pick_ray: PickRay = Field(..., description="Pick ray")
    view_transform: Optional[dict] = Field(None, description="Current view transform")


class MapPickResponse(BaseModel):
    """Response from pick mapping."""
    face_id: Optional[str] = Field(None, description="Face ID")
    edge_id: Optional[str] = Field(None, description="Edge ID")
    vertex_id: Optional[str] = Field(None, description="Vertex ID")
    feature_reference: Optional[str] = Field(None, description="Corresponding feature/sketch reference")


class TopologyTaggingRequest(BaseModel):
    """Request for topology tagging."""
    old_solid_signature: dict = Field(..., description="Old solid signature")
    new_solid_signature: dict = Field(..., description="New solid signature")
    mapping_hints: Optional[dict] = Field(None, description="Mapping hints")


class TopologyTaggingResponse(BaseModel):
    """Response from topology tagging."""
    face_mapping: dict = Field(..., description="Mapping from old face IDs to new face IDs")
    edge_mapping: dict = Field(..., description="Mapping from old edge IDs to new edge IDs")
    vertex_mapping: dict = Field(..., description="Mapping from old vertex IDs to new vertex IDs")


# ============================================================================
# Simulation / FEA (LATER)
# ============================================================================

class BoundaryCondition(BaseModel):
    """Boundary condition for FEA."""
    type: str = Field(..., description="BC type (fixed, pinned, etc.)")
    location: dict = Field(..., description="Location specification")
    params: dict = Field(default_factory=dict, description="BC parameters")


class Load(BaseModel):
    """Load definition for FEA."""
    type: str = Field(..., description="Load type (force, pressure, etc.)")
    location: dict = Field(..., description="Location specification")
    magnitude: list[float] = Field(..., description="Load magnitude [x, y, z] or scalar")


class FeaLinearStaticRequest(BaseModel):
    """Request for linear static FEA."""
    part_ir: dict = Field(..., description="Part IR")
    material: Material = Field(..., description="Material definition")
    boundary_conditions: list[BoundaryCondition] = Field(..., description="Boundary conditions")
    loads: list[Load] = Field(..., description="Loads")


class FeaLinearStaticResponse(BaseModel):
    """Response from linear static FEA."""
    displacement_field: Optional[MeshData] = Field(None, description="Displacement field")
    stress_field: Optional[MeshData] = Field(None, description="Stress field")
    max_von_mises: float = Field(..., description="Maximum von Mises stress")
    max_displacement: float = Field(..., description="Maximum displacement")

