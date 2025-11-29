/**
 * Top Menu Bar component - SolidWorks-style toolbar.
 * Contains CAD tools and operations.
 */

interface TopMenuBarProps {
  onNewPart?: () => void;
  onSave?: () => void;
  onExportSTL?: () => void;
  onExportSTEP?: () => void;
  onViewDrawing?: () => void;
  onSketchMode?: () => void;
  onExtrude?: () => void;
  onCut?: () => void;
  // MVP: Chamfer and Fillet disabled
  hasPart?: boolean;
  isSketchMode?: boolean;
}

export function TopMenuBar({
  onNewPart,
  onSave,
  onExportSTL,
  onExportSTEP,
  onViewDrawing,
  onSketchMode,
  onExtrude,
  onCut,
  // MVP: Chamfer and Fillet disabled
  hasPart = false,
  isSketchMode = false
}: TopMenuBarProps) {
  const buttonStyle = {
    padding: '0.5rem 1rem',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9em',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
  };

  const disabledStyle = {
    ...buttonStyle,
    backgroundColor: '#e0e0e0',
    color: '#999',
    cursor: 'not-allowed'
  };

  return (
    <div style={{
      backgroundColor: '#f8f8f8',
      borderBottom: '2px solid #ddd',
      padding: '0.5rem 1rem',
      display: 'flex',
      gap: '0.5rem',
      alignItems: 'center',
      flexWrap: 'wrap'
    }}>
      {/* File operations */}
      <div style={{ display: 'flex', gap: '0.5rem', paddingRight: '1rem', borderRight: '1px solid #ddd' }}>
        <button onClick={onNewPart} style={buttonStyle}>
          📄 New
        </button>
        <button onClick={onSave} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          💾 Save
        </button>
      </div>

      {/* Sketch tools */}
      <div style={{ display: 'flex', gap: '0.5rem', paddingRight: '1rem', borderRight: '1px solid #ddd' }}>
        <button 
          onClick={onSketchMode} 
          style={hasPart ? (isSketchMode ? { ...buttonStyle, backgroundColor: '#4a90e2', color: 'white' } : buttonStyle) : disabledStyle}
          disabled={!hasPart}
        >
          ✏️ Sketch
        </button>
      </div>

      {/* Feature tools */}
      <div style={{ display: 'flex', gap: '0.5rem', paddingRight: '1rem', borderRight: '1px solid #ddd' }}>
        <button onClick={onExtrude} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          ⬆️ Extrude
        </button>
        <button onClick={onCut} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          ➖ Cut
        </button>
        {/* MVP: Chamfer and Fillet disabled */}
      </div>

      {/* Export */}
      <div style={{ display: 'flex', gap: '0.5rem', marginLeft: 'auto' }}>
        <button onClick={onViewDrawing} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          📐 Drawing
        </button>
        <button onClick={onExportSTL} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          📦 STL
        </button>
        <button onClick={onExportSTEP} style={hasPart ? buttonStyle : disabledStyle} disabled={!hasPart}>
          📦 STEP
        </button>
      </div>
    </div>
  );
}

