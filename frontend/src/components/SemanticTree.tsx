/**
 * Semantic Tree component.
 * Shows the hierarchical structure of the part: parameters, features, chains.
 */

import { useState } from 'react';
import type { Part } from '../types/ir';

interface SemanticTreeProps {
  part: Part | null;
  selectedItem: { type: 'param' | 'feature' | 'chain'; name: string } | null;
  onSelect: (type: 'param' | 'feature' | 'chain', name: string) => void;
}

export function SemanticTree({ part, selectedItem, onSelect }: SemanticTreeProps) {
  const [expanded, setExpanded] = useState({
    params: true,
    features: true,
    chains: true,
  });

  if (!part) {
    return (
      <div style={{ padding: '1rem' }}>
        <p>No part loaded</p>
      </div>
    );
  }

  const toggleSection = (section: 'params' | 'features' | 'chains') => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const itemStyle = (type: 'param' | 'feature' | 'chain', name: string) => ({
    padding: '0.25rem 0.5rem',
    cursor: 'pointer',
    backgroundColor: selectedItem?.type === type && selectedItem?.name === name ? '#e3f2fd' : 'transparent',
    borderRadius: '4px',
    fontSize: '0.9em',
  });

  return (
    <div style={{ padding: '1rem', height: '100%', overflow: 'auto' }}>
      <h2 style={{ marginTop: 0 }}>Part Structure</h2>
      
      {/* Part name */}
      <div style={{ fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.1em' }}>
        {part.name}
      </div>

      {/* Parameters section */}
      <div>
        <div
          onClick={() => toggleSection('params')}
          style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '0.5rem', userSelect: 'none' }}
        >
          {expanded.params ? '▼' : '▶'} Parameters
        </div>
        {expanded.params && (
          <div style={{ marginLeft: '1rem', marginBottom: '1rem' }}>
            {Object.values(part.params).map((param) => (
              <div
                key={param.name}
                onClick={() => onSelect('param', param.name)}
                style={itemStyle('param', param.name)}
              >
                {param.name} = {param.value} {param.unit}
                {param.tolerance_class && ` (${param.tolerance_class})`}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Features section */}
      <div>
        <div
          onClick={() => toggleSection('features')}
          style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '0.5rem', userSelect: 'none' }}
        >
          {expanded.features ? '▼' : '▶'} Features
        </div>
        {expanded.features && (
          <div style={{ marginLeft: '1rem', marginBottom: '1rem' }}>
            {part.features.map((feature) => (
              <div
                key={feature.name}
                onClick={() => onSelect('feature', feature.name)}
                style={itemStyle('feature', feature.name)}
              >
                {feature.name} <span style={{ color: '#666', fontSize: '0.85em' }}>({feature.type})</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Chains section */}
      <div>
        <div
          onClick={() => toggleSection('chains')}
          style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '0.5rem', userSelect: 'none' }}
        >
          {expanded.chains ? '▼' : '▶'} Chains
        </div>
        {expanded.chains && (
          <div style={{ marginLeft: '1rem' }}>
            {part.chains.map((chain) => (
              <div
                key={chain.name}
                onClick={() => onSelect('chain', chain.name)}
                style={itemStyle('chain', chain.name)}
              >
                {chain.name}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

