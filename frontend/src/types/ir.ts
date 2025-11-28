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

export interface Feature {
  type: "cylinder" | "hole" | "chamfer" | "joint_interface" | "link_body" | "pocket" | "fillet";
  name: string;
  params: Record<string, string | number>;
  critical?: boolean;
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
}

