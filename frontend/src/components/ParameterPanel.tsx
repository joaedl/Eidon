/**
 * Parameter panel component.
 * Displays and allows editing of part parameters.
 */

import { useState } from 'react';
import type { Part, Param } from '../types/ir';

interface ParameterPanelProps {
  part: Part | null;
  onParamChange: (paramName: string, value: number) => void;
  onApply: () => void;
  paramsEval?: Record<string, { nominal: number; min: number; max: number }>;
}

export function ParameterPanel({ part, onParamChange, onApply, paramsEval }: ParameterPanelProps) {
  const [localValues, setLocalValues] = useState<Record<string, number>>({});

  if (!part) {
    return (
      <div style={{ padding: '1rem' }}>
        <p>No part loaded</p>
      </div>
    );
  }

  const handleValueChange = (paramName: string, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setLocalValues(prev => ({ ...prev, [paramName]: numValue }));
      onParamChange(paramName, numValue);
    }
  };

  return (
    <div style={{ padding: '1rem', height: '100%', overflow: 'auto' }}>
      <h2 style={{ marginTop: 0 }}>Parameters</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {Object.values(part.params).map((param) => {
          const currentValue = localValues[param.name] ?? param.value;
          const evalData = paramsEval?.[param.name];

          return (
            <div key={param.name} style={{ border: '1px solid #ccc', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{param.name}</div>
              <div style={{ marginBottom: '0.5rem' }}>
                <label>
                  Value:
                  <input
                    type="number"
                    value={currentValue}
                    onChange={(e) => handleValueChange(param.name, e.target.value)}
                    style={{ marginLeft: '0.5rem', width: '100px' }}
                  />
                  <span style={{ marginLeft: '0.5rem' }}>{param.unit}</span>
                </label>
              </div>
              {param.tolerance_class && (
                <div style={{ fontSize: '0.9em', color: '#666' }}>
                  Tolerance: {param.tolerance_class}
                </div>
              )}
              {evalData && (
                <div style={{ fontSize: '0.85em', color: '#888', marginTop: '0.5rem' }}>
                  <div>Nominal: {evalData.nominal.toFixed(3)}</div>
                  <div>Min: {evalData.min.toFixed(3)}</div>
                  <div>Max: {evalData.max.toFixed(3)}</div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <button
        onClick={onApply}
        style={{
          marginTop: '1rem',
          padding: '0.5rem 1rem',
          backgroundColor: '#4a90e2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Apply Changes
      </button>
    </div>
  );
}

