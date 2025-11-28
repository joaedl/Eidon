/**
 * Quick Actions Toolbar component.
 * Provides buttons for common geometric operations (chamfer, fillet, pocket, link body).
 */

import { useState } from 'react';
import type { Part } from '../types/ir';

interface QuickActionsToolbarProps {
  part: Part | null;
  selectedFeatureId: string | null;
  onApplyOperations: (operations: Array<{ type: string; [key: string]: any }>) => void;
}

export function QuickActionsToolbar({ part, selectedFeatureId, onApplyOperations }: QuickActionsToolbarProps) {
  const [showChamferDialog, setShowChamferDialog] = useState(false);
  const [showFilletDialog, setShowFilletDialog] = useState(false);
  const [showPocketDialog, setShowPocketDialog] = useState(false);
  const [showLinkBodyDialog, setShowLinkBodyDialog] = useState(false);

  const handleChamfer = (size: number) => {
    if (!selectedFeatureId) return;
    
    const operations = [{
      type: "AddFeature",
      feature: {
        name: `chamfer_${selectedFeatureId}_${Date.now()}`,
        type: "chamfer",
        params: {
          size,
          target_feature: selectedFeatureId,
        }
      }
    }];
    
    onApplyOperations(operations);
    setShowChamferDialog(false);
  };

  const handleFillet = (radius: number) => {
    if (!selectedFeatureId) return;
    
    const operations = [{
      type: "AddFeature",
      feature: {
        name: `fillet_${selectedFeatureId}_${Date.now()}`,
        type: "fillet",
        params: {
          radius,
          target_feature: selectedFeatureId,
        }
      }
    }];
    
    onApplyOperations(operations);
    setShowFilletDialog(false);
  };

  const handlePocket = (depth: number, width: number, height: number, fillet: number) => {
    if (!selectedFeatureId) return;
    
    const operations = [{
      type: "AddFeature",
      feature: {
        name: `pocket_${selectedFeatureId}_${Date.now()}`,
        type: "pocket",
        params: {
          host: selectedFeatureId,
          depth,
          width,
          height,
          fillet: fillet || 0,
        }
      }
    }];
    
    onApplyOperations(operations);
    setShowPocketDialog(false);
  };

  const handleLinkBody = (sectionType: string, width: number, height: number, thickness: number) => {
    if (!part) return;
    
    // Find interfaces
    const interfaces = part.features.filter(f => f.type === "joint_interface");
    if (interfaces.length < 2) {
      alert("Need at least 2 joint interfaces to create a link body");
      return;
    }
    
    const operations = [{
      type: "AddFeature",
      feature: {
        name: `link_body_${Date.now()}`,
        type: "link_body",
        params: {
          section_type: sectionType,
          width,
          height,
          thickness,
          from: interfaces[0].name,
          to: interfaces[1].name,
        }
      }
    }];
    
    onApplyOperations(operations);
    setShowLinkBodyDialog(false);
  };

  const hasInterfaces = part?.features.some(f => f.type === "joint_interface") ?? false;

  return (
    <div style={{ 
      padding: '0.5rem', 
      backgroundColor: '#f5f5f5', 
      borderBottom: '1px solid #ccc',
      display: 'flex',
      gap: '0.5rem',
      flexWrap: 'wrap',
    }}>
      <button
        onClick={() => setShowChamferDialog(true)}
        disabled={!selectedFeatureId}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: selectedFeatureId ? '#4a90e2' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedFeatureId ? 'pointer' : 'not-allowed',
          fontSize: '0.9em',
        }}
        title={selectedFeatureId ? "Chamfer edges" : "Select a feature first"}
      >
        Chamfer
      </button>

      <button
        onClick={() => setShowFilletDialog(true)}
        disabled={!selectedFeatureId}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: selectedFeatureId ? '#4a90e2' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedFeatureId ? 'pointer' : 'not-allowed',
          fontSize: '0.9em',
        }}
        title={selectedFeatureId ? "Round edges" : "Select a feature first"}
      >
        Fillet
      </button>

      <button
        onClick={() => setShowPocketDialog(true)}
        disabled={!selectedFeatureId}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: selectedFeatureId ? '#4a90e2' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: selectedFeatureId ? 'pointer' : 'not-allowed',
          fontSize: '0.9em',
        }}
        title={selectedFeatureId ? "Add pocket" : "Select a feature first"}
      >
        Pocket
      </button>

      <button
        onClick={() => setShowLinkBodyDialog(true)}
        disabled={!hasInterfaces}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: hasInterfaces ? '#4a90e2' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: hasInterfaces ? 'pointer' : 'not-allowed',
          fontSize: '0.9em',
        }}
        title={hasInterfaces ? "Create link body" : "Need 2+ joint interfaces"}
      >
        Link Body
      </button>

      {/* Dialogs */}
      {showChamferDialog && (
        <ChamferDialog
          onApply={handleChamfer}
          onCancel={() => setShowChamferDialog(false)}
        />
      )}

      {showFilletDialog && (
        <FilletDialog
          onApply={handleFillet}
          onCancel={() => setShowFilletDialog(false)}
        />
      )}

      {showPocketDialog && (
        <PocketDialog
          onApply={handlePocket}
          onCancel={() => setShowPocketDialog(false)}
        />
      )}

      {showLinkBodyDialog && (
        <LinkBodyDialog
          onApply={handleLinkBody}
          onCancel={() => setShowLinkBodyDialog(false)}
        />
      )}
    </div>
  );
}

// Dialog components
function ChamferDialog({ onApply, onCancel }: { onApply: (size: number) => void; onCancel: () => void }) {
  const [size, setSize] = useState('1.0');

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 1000,
    }}>
      <h3 style={{ marginTop: 0 }}>Chamfer Edges</h3>
      <label>
        Size (mm):
        <input
          type="number"
          value={size}
          onChange={(e) => setSize(e.target.value)}
          style={{ marginLeft: '0.5rem', width: '100px' }}
        />
      </label>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => onApply(parseFloat(size))} style={{ padding: '0.5rem 1rem', backgroundColor: '#4a90e2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Apply
        </button>
        <button onClick={onCancel} style={{ padding: '0.5rem 1rem', backgroundColor: '#ccc', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function FilletDialog({ onApply, onCancel }: { onApply: (radius: number) => void; onCancel: () => void }) {
  const [radius, setRadius] = useState('2.0');

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 1000,
    }}>
      <h3 style={{ marginTop: 0 }}>Round Edges (Fillet)</h3>
      <label>
        Radius (mm):
        <input
          type="number"
          value={radius}
          onChange={(e) => setRadius(e.target.value)}
          style={{ marginLeft: '0.5rem', width: '100px' }}
        />
      </label>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => onApply(parseFloat(radius))} style={{ padding: '0.5rem 1rem', backgroundColor: '#4a90e2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Apply
        </button>
        <button onClick={onCancel} style={{ padding: '0.5rem 1rem', backgroundColor: '#ccc', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function PocketDialog({ onApply, onCancel }: { onApply: (depth: number, width: number, height: number, fillet: number) => void; onCancel: () => void }) {
  const [depth, setDepth] = useState('10');
  const [width, setWidth] = useState('30');
  const [height, setHeight] = useState('80');
  const [fillet, setFillet] = useState('0');

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 1000,
    }}>
      <h3 style={{ marginTop: 0 }}>Add Pocket</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label>
          Depth (mm):
          <input type="number" value={depth} onChange={(e) => setDepth(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
        <label>
          Width (mm):
          <input type="number" value={width} onChange={(e) => setWidth(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
        <label>
          Height (mm):
          <input type="number" value={height} onChange={(e) => setHeight(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
        <label>
          Fillet radius (mm):
          <input type="number" value={fillet} onChange={(e) => setFillet(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
      </div>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => onApply(parseFloat(depth), parseFloat(width), parseFloat(height), parseFloat(fillet))} style={{ padding: '0.5rem 1rem', backgroundColor: '#4a90e2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Apply
        </button>
        <button onClick={onCancel} style={{ padding: '0.5rem 1rem', backgroundColor: '#ccc', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

function LinkBodyDialog({ onApply, onCancel }: { onApply: (sectionType: string, width: number, height: number, thickness: number) => void; onCancel: () => void }) {
  const [sectionType, setSectionType] = useState('rect');
  const [width, setWidth] = useState('40');
  const [height, setHeight] = useState('60');
  const [thickness, setThickness] = useState('4');

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      backgroundColor: 'white',
      padding: '1.5rem',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 1000,
    }}>
      <h3 style={{ marginTop: 0 }}>Create Link Body</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label>
          Section type:
          <select value={sectionType} onChange={(e) => setSectionType(e.target.value)} style={{ marginLeft: '0.5rem' }}>
            <option value="rect">Rectangular</option>
            <option value="tube">Tubular</option>
          </select>
        </label>
        <label>
          Width (mm):
          <input type="number" value={width} onChange={(e) => setWidth(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
        <label>
          Height (mm):
          <input type="number" value={height} onChange={(e) => setHeight(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
        <label>
          Thickness (mm):
          <input type="number" value={thickness} onChange={(e) => setThickness(e.target.value)} style={{ marginLeft: '0.5rem', width: '100px' }} />
        </label>
      </div>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button onClick={() => onApply(sectionType, parseFloat(width), parseFloat(height), parseFloat(thickness))} style={{ padding: '0.5rem 1rem', backgroundColor: '#4a90e2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Apply
        </button>
        <button onClick={onCancel} style={{ padding: '0.5rem 1rem', backgroundColor: '#ccc', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

