/**
 * Extrude Dialog component.
 * Allows user to create an extrude feature from a sketch.
 */

import { useState } from 'react';

interface ExtrudeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onExtrude: (sketchName: string, distance: number, operation: 'join' | 'cut') => void;
  availableSketches: Array<{ name: string; plane: string }>;
}

export function ExtrudeDialog({
  isOpen,
  onClose,
  onExtrude,
  availableSketches
}: ExtrudeDialogProps) {
  if (!isOpen) return null;

  const [selectedSketch, setSelectedSketch] = useState('');
  const [distance, setDistance] = useState('10');
  const [operation, setOperation] = useState<'join' | 'cut'>('join');

  const handleSubmit = () => {
    if (!selectedSketch || !distance) {
      alert('Please select a sketch and enter a distance');
      return;
    }
    const dist = parseFloat(distance);
    if (isNaN(dist) || dist <= 0) {
      alert('Please enter a valid positive distance');
      return;
    }
    onExtrude(selectedSketch, dist, operation);
    onClose();
    // Reset form
    setSelectedSketch('');
    setDistance('10');
    setOperation('join');
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '8px',
          minWidth: '400px',
          maxWidth: '600px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0, marginBottom: '1rem' }}>Extrude Sketch</h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Select Sketch:
          </label>
          <select
            value={selectedSketch}
            onChange={(e) => setSelectedSketch(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          >
            <option value="">-- Select a sketch --</option>
            {availableSketches.map((sketch) => (
              <option key={sketch.name} value={sketch.name}>
                {sketch.name} ({sketch.plane})
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Distance (mm):
          </label>
          <input
            type="number"
            value={distance}
            onChange={(e) => setDistance(e.target.value)}
            min="0"
            step="0.1"
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Operation:
          </label>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                value="join"
                checked={operation === 'join'}
                onChange={(e) => setOperation(e.target.value as 'join' | 'cut')}
              />
              Join (Add material)
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                value="cut"
                checked={operation === 'cut'}
                onChange={(e) => setOperation(e.target.value as 'join' | 'cut')}
              />
              Cut (Remove material)
            </label>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: '#f0f0f0',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedSketch || !distance}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: selectedSketch && distance ? '#4a90e2' : '#ccc',
              color: 'white',
              cursor: selectedSketch && distance ? 'pointer' : 'not-allowed'
            }}
          >
            Create Extrude
          </button>
        </div>
      </div>
    </div>
  );
}

