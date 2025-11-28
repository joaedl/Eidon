/**
 * Parameter panel component.
 * Displays and allows editing of part parameters.
 */

import { useState } from 'react';
import type { Part } from '../types/ir';

interface ParameterPanelProps {
  part: Part | null;
  onParamChange: (paramName: string, value: number) => void;
  onToleranceChange: (paramName: string, toleranceClass: string | null) => void;
  onApply: () => void;
  paramsEval?: Record<string, { nominal: number; min: number; max: number }>;
  highlightedParam?: string | null;
}

const TOLERANCE_CLASSES = ['', 'g6', 'H7', 'g7', 'H8'];

export function ParameterPanel({ 
  part, 
  onParamChange, 
  onToleranceChange,
  onApply, 
  paramsEval,
  highlightedParam 
}: ParameterPanelProps) {
  const [localValues, setLocalValues] = useState<Record<string, number>>({});
  const [localTolerances, setLocalTolerances] = useState<Record<string, string | null>>({});

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

  const handleToleranceChange = (paramName: string, toleranceClass: string) => {
    const value = toleranceClass === '' ? null : toleranceClass;
    setLocalTolerances(prev => ({ ...prev, [paramName]: value }));
    onToleranceChange(paramName, value);
  };

  return (
    <div style={{ padding: '1rem', height: '100%', overflow: 'auto' }}>
      <h2 style={{ marginTop: 0 }}>Parameters</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {Object.values(part.params).map((param) => {
          const currentValue = localValues[param.name] ?? param.value;
          const currentTolerance = localTolerances[param.name] ?? param.tolerance_class ?? '';
          const evalData = paramsEval?.[param.name];
          const isHighlighted = highlightedParam === param.name;

          return (
            <div 
              key={param.name} 
              style={{ 
                border: `2px solid ${isHighlighted ? '#4a90e2' : '#ccc'}`, 
                padding: '0.75rem', 
                borderRadius: '4px',
                backgroundColor: isHighlighted ? '#e3f2fd' : 'white',
              }}
            >
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
              <div style={{ marginBottom: '0.5rem' }}>
                <label>
                  Tolerance:
                  <select
                    value={currentTolerance}
                    onChange={(e) => handleToleranceChange(param.name, e.target.value)}
                    style={{ marginLeft: '0.5rem', padding: '0.25rem' }}
                  >
                    {TOLERANCE_CLASSES.map(tc => (
                      <option key={tc} value={tc}>{tc || '(none)'}</option>
                    ))}
                  </select>
                </label>
              </div>
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

