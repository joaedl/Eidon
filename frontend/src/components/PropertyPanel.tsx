/**
 * Property Panel component - SolidWorks-style property panel on the right.
 * Shows properties of selected entity (feature, sketch, parameter, etc.)
 */

import type { Part, Feature, Sketch, Param } from '../types/ir';

interface PropertyPanelProps {
  part: Part | null;
  selectedFeature: Feature | null;
  selectedSketch: Sketch | null;
  selectedParam: Param | null;
  onParamChange?: (name: string, value: number) => void;
  onToleranceChange?: (name: string, tolerance: string | null) => void;
  onApply?: () => void;
}

export function PropertyPanel({
  part,
  selectedFeature,
  selectedSketch,
  selectedParam,
  onParamChange,
  onToleranceChange,
  onApply
}: PropertyPanelProps) {
  if (!part) {
    return (
      <div style={{ padding: '1rem', color: '#666' }}>
        <p>No part loaded</p>
      </div>
    );
  }

  if (selectedParam) {
  return (
    <div style={{ height: '100%', overflow: 'auto', backgroundColor: '#fff' }}>
      {/* Title shown in CollapsiblePanel */}
        <div style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Name
            </label>
            <input
              type="text"
              value={selectedParam.name}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Value
            </label>
            <input
              type="number"
              value={selectedParam.value}
              onChange={(e) => onParamChange?.(selectedParam.name, parseFloat(e.target.value) || 0)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Unit
            </label>
            <input
              type="text"
              value={selectedParam.unit}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                backgroundColor: '#f5f5f5'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Tolerance Class
            </label>
            <select
              value={selectedParam.tolerance_class || ''}
              onChange={(e) => onToleranceChange?.(selectedParam.name, e.target.value || null)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            >
              <option value="">None</option>
              <option value="g6">g6</option>
              <option value="H7">H7</option>
              <option value="f7">f7</option>
              <option value="h7">h7</option>
            </select>
          </div>
          {onApply && (
            <button
              onClick={onApply}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: '#4a90e2',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Apply Changes
            </button>
          )}
        </div>
      </div>
    );
  }

  if (selectedSketch) {
    return (
      <div style={{ height: '100%', overflow: 'auto', backgroundColor: '#fff' }}>
        {/* Title shown in CollapsiblePanel */}
        <div style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Name
            </label>
            <input
              type="text"
              value={selectedSketch.name}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Plane
            </label>
            <input
              type="text"
              value={selectedSketch.plane}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Statistics</div>
            <div style={{ fontSize: '0.9em', color: '#666' }}>
              <div>Entities: {selectedSketch.entities.length}</div>
              <div>Constraints: {selectedSketch.constraints.length}</div>
              <div>Dimensions: {selectedSketch.dimensions.length}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (selectedFeature) {
    return (
      <div style={{ height: '100%', overflow: 'auto', backgroundColor: '#fff' }}>
        {/* Title shown in CollapsiblePanel */}
        <div style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Name
            </label>
            <input
              type="text"
              value={selectedFeature.name}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Type
            </label>
            <input
              type="text"
              value={selectedFeature.type}
              readOnly
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Parameters
            </label>
            <div style={{ fontSize: '0.9em' }}>
              {Object.entries(selectedFeature.params).map(([key, value]) => (
                <div key={key} style={{ padding: '0.25rem', borderBottom: '1px solid #eee' }}>
                  <strong>{key}:</strong> {String(value)}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', color: '#666', textAlign: 'center' }}>
      <p>Select an entity to view properties</p>
    </div>
  );
}

