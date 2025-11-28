/**
 * API client for communicating with the backend.
 */

import type { Part, RebuildResponse, ApplyOperationsResponse } from '../types/ir';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  /**
   * Parse DSL text into Part IR.
   */
  async parseDSL(dsl: string): Promise<Part> {
    return fetchJSON<Part>('/models/from-dsl', {
      method: 'POST',
      body: JSON.stringify({ dsl }),
    });
  },

  /**
   * Rebuild geometry and analysis from Part IR.
   */
  async rebuild(part: Part): Promise<RebuildResponse> {
    return fetchJSON<RebuildResponse>('/models/rebuild', {
      method: 'POST',
      body: JSON.stringify({ part }),
    });
  },

  /**
   * Analyze chains in a part.
   */
  async analyzeChains(part: Part): Promise<Record<string, { nominal: number; min: number; max: number }>> {
    return fetchJSON('/analysis/chains', {
      method: 'POST',
      body: JSON.stringify({ part }),
    });
  },

  /**
   * Send command to agent.
   */
  async agentCommand(
    mode: 'create' | 'edit' | 'explain',
    prompt: string,
    part: Part | null,
    scope: { selected_feature_ids?: string[]; selected_param_names?: string[]; selected_chain_names?: string[] } = {}
  ): Promise<{ part: Part | null; operations: Array<{ type: string; [key: string]: any }>; message: string; success: boolean }> {
    return fetchJSON('/agent/command', {
      method: 'POST',
      body: JSON.stringify({ 
        mode,
        prompt,
        part: part || null,
        scope,
      }),
    });
  },

  /**
   * Apply operations to a part.
   */
  async applyOperations(part: Part, operations: Array<{ type: string; [key: string]: any }>): Promise<ApplyOperationsResponse> {
    return fetchJSON<ApplyOperationsResponse>('/models/apply-operations', {
      method: 'POST',
      body: JSON.stringify({ part, operations }),
    });
  },

  /**
   * Create a new part from a template.
   */
  async createNewPart(template: string): Promise<{ dsl: string; part: Part }> {
    return fetchJSON('/models/new', {
      method: 'POST',
      body: JSON.stringify({ template }),
    });
  },

  /**
   * List available templates.
   */
  async listTemplates(): Promise<{ templates: string[] }> {
    return fetchJSON('/models/templates');
  },

  /**
   * Export part to STL.
   */
  async exportSTL(part: Part): Promise<Blob> {
    const response = await fetch(`${API_BASE}/export/stl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ part }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  },

  /**
   * Export part to STEP.
   */
  async exportSTEP(part: Part): Promise<Blob> {
    const response = await fetch(`${API_BASE}/export/step`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ part }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  },
};

