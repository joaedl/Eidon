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
  type: "cylinder" | "hole" | "chamfer";
  name: string;
  params: Record<string, string | number>;
}

export interface Chain {
  name: string;
  terms: string[];
  target_value?: number | null;
  target_tolerance?: number | null;
}

export interface Part {
  name: string;
  params: Record<string, Param>;
  features: Feature[];
  chains: Chain[];
}

export interface MeshData {
  vertices: number[][];
  faces: number[][];
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
}

