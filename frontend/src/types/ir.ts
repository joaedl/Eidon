/**
 * TypeScript types for IR (Intermediate Representation).
 * These mirror the backend Pydantic models.
 */

export interface Param {
  name: string;
  value: number;
  unit: string;
  tolerance_class?: string | null;
}

// Sketch models
// MVP: Only line, circle, and rectangle supported (no arc)
export interface SketchEntity {
  id: string;
  type: 'line' | 'circle' | 'rectangle';
  start?: [number, number];
  end?: [number, number];
  center?: [number, number];
  radius?: number;
  corner1?: [number, number];
  corner2?: [number, number];
  isConstruction?: boolean; // For construction lines (dashed, non-geometry)
}

// MVP: Only horizontal, vertical, and coincident supported
export interface SketchConstraint {
  id: string;
  type: 'horizontal' | 'vertical' | 'coincident';
  entity_ids: string[];
  params?: Record<string, any>;
}

// MVP: Only length and diameter supported
export interface SketchDimension {
  id: string;
  type: 'length' | 'diameter';
  entity_ids: string[];
  value: number;
  unit: string;
}

export interface Sketch {
  name: string;
  plane: string;
  entities: SketchEntity[];
  constraints: SketchConstraint[];
  dimensions: SketchDimension[];
}

// MVP: Only sketch and extrude supported
export interface Feature {
  type: "sketch" | "extrude";
  name: string;
  params: Record<string, string | number | any>;
  critical?: boolean;
  sketch?: Sketch;
}

export interface Chain {
  name: string;
  terms: string[];
  target_value?: number | null;
  target_tolerance?: number | null;
}

export interface Constraint {
  name: string;
  type: "coincident" | "parallel" | "perpendicular" | "distance" | "angle" | "reference";
  entities: string[];
  params: Record<string, number | string>;
}

export interface ValidationIssue {
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
  related_params: string[];
  related_features: string[];
  related_chains: string[];
}

export interface Part {
  name: string;
  params: Record<string, Param>;
  features: Feature[];
  chains: Chain[];
  constraints?: Constraint[];
  sketches?: Sketch[];
}

export interface MeshData {
  vertices: number[][];
  faces: number[][];
  featureId?: string;
  faceToFeature?: (string | null)[];
}

export interface ParamEvaluation {
  nominal: number;
  min: number;
  max: number;
}

export interface ChainEvaluation {
  nominal: number;
  min: number;
  max: number;
}

export interface RebuildResponse {
  mesh: MeshData;
  params_eval: Record<string, ParamEvaluation>;
  chains_eval: Record<string, ChainEvaluation>;
  issues: ValidationIssue[];
}

export interface ApplyOperationsResponse extends RebuildResponse {
  part: Part;
  dsl?: string;
}

