/**
 * Feature Tree component - SolidWorks-style feature tree on the left.
 * Shows hierarchical structure of the part with features, sketches, etc.
 */

import { useState } from 'react';
import type { Part } from '../types/ir';

interface FeatureTreeProps {
  part: Part | null;
  selectedFeatureId: string | null;
  selectedSketchName: string | null;
  onFeatureSelect: (featureId: string | null) => void;
  onSketchSelect: (sketchName: string | null) => void;
  onFeatureRightClick?: (featureId: string, event: React.MouseEvent) => void;
}

export function FeatureTree({
  part,
  selectedFeatureId,
  selectedSketchName,
  onFeatureSelect,
  onSketchSelect,
  onFeatureRightClick
}: FeatureTreeProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    'root': true,
    'sketches': true,
    'features': true,
    'bodies': true
  });

  if (!part) {
    return (
      <div style={{ padding: '1rem', color: '#666' }}>
        <p>No part loaded</p>
      </div>
    );
  }

  const toggleExpanded = (key: string) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const getFeatureIcon = (type: string) => {
    const icons: Record<string, string> = {
      'sketch': '✏️',
      'extrude': '⬆️',
      'cut': '➖',
      'cylinder': '🔵',
      'box': '📦',
      'hole': '🕳️',
      'chamfer': '🔺',
      'fillet': '⭕',
      'pocket': '📥',
      'joint_interface': '🔗',
      'link_body': '🔗'
    };
    return icons[type] || '📐';
  };

  const itemStyle = (isSelected: boolean) => ({
    padding: '0.25rem 0.5rem',
    cursor: 'pointer',
    backgroundColor: isSelected ? '#e3f2fd' : 'transparent',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.9em',
    userSelect: 'none' as const
  });

  const indentStyle = (level: number) => ({
    marginLeft: `${level * 1.5}rem`
  });

  return (
    <div style={{ 
      height: '100%', 
      overflow: 'auto',
      backgroundColor: '#fafafa'
    }}>
      {/* Part name (root) - shown in CollapsiblePanel title, so we don't duplicate */}

      {/* Sketches section */}
      <div>
        <div
          onClick={() => toggleExpanded('sketches')}
          style={{
            padding: '0.25rem 0.5rem',
            cursor: 'pointer',
            backgroundColor: '#f5f5f5',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85em',
            fontWeight: 'bold'
          }}
        >
          {expanded['sketches'] ? '▼' : '▶'} Sketches
        </div>
        {expanded['sketches'] && (
          <div>
            {part.features.filter(f => f.type === 'sketch').map((feature) => (
              <div
                key={feature.name}
                onClick={() => {
                  onFeatureSelect(feature.name);
                  onSketchSelect(feature.name);
                }}
                onContextMenu={(e) => {
                  e.preventDefault();
                  onFeatureRightClick?.(feature.name, e);
                }}
                style={{
                  ...itemStyle(selectedFeatureId === feature.name),
                  ...indentStyle(1)
                }}
              >
                {getFeatureIcon('sketch')} {feature.name}
              </div>
            ))}
            {part.sketches?.map((sketch) => (
              <div
                key={sketch.name}
                onClick={() => {
                  onSketchSelect(sketch.name);
                }}
                style={{
                  ...itemStyle(selectedSketchName === sketch.name),
                  ...indentStyle(1)
                }}
              >
                {getFeatureIcon('sketch')} {sketch.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Features section */}
      <div>
        <div
          onClick={() => toggleExpanded('features')}
          style={{
            padding: '0.25rem 0.5rem',
            cursor: 'pointer',
            backgroundColor: '#f5f5f5',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85em',
            fontWeight: 'bold'
          }}
        >
          {expanded['features'] ? '▼' : '▶'} Features
        </div>
        {expanded['features'] && (
          <div>
            {part.features.filter(f => f.type !== 'sketch').map((feature) => (
              <div
                key={feature.name}
                onClick={() => {
                  onFeatureSelect(feature.name);
                  onSketchSelect(null);
                }}
                onContextMenu={(e) => {
                  e.preventDefault();
                  onFeatureRightClick?.(feature.name, e);
                }}
                style={{
                  ...itemStyle(selectedFeatureId === feature.name),
                  ...indentStyle(1)
                }}
              >
                {getFeatureIcon(feature.type)} {feature.name}
                {feature.type === 'extrude' && feature.params.sketch && (
                  <span style={{ fontSize: '0.8em', color: '#666', marginLeft: '0.5rem' }}>
                    (from {String(feature.params.sketch)})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Parameters section (collapsed by default) */}
      <div>
        <div
          onClick={() => toggleExpanded('params')}
          style={{
            padding: '0.25rem 0.5rem',
            cursor: 'pointer',
            backgroundColor: '#f5f5f5',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85em',
            fontWeight: 'bold'
          }}
        >
          {expanded['params'] ? '▼' : '▶'} Parameters
        </div>
        {expanded['params'] && (
          <div>
            {Object.values(part.params).map((param) => (
              <div
                key={param.name}
                style={{
                  ...itemStyle(false),
                  ...indentStyle(1),
                  color: '#666',
                  fontSize: '0.85em'
                }}
              >
                📏 {param.name} = {param.value} {param.unit}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

