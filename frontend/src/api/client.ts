/**
 * API client for communicating with the backend.
 */

import type { Part, RebuildResponse } from '../types/ir';

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
   * Send command to agent (stubbed).
   */
  async agentCommand(part: Part, prompt: string): Promise<{ part: Part; message: string; success: boolean }> {
    return fetchJSON('/agent/command', {
      method: 'POST',
      body: JSON.stringify({ part, prompt }),
    });
  },
};

