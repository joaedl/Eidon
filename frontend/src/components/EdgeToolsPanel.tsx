/**
 * Edge Tools Panel - FreeCAD-style edge/face/feature tools.
 * Similar to FreeCAD's edge tools panel on the right.
 */

interface EdgeToolsPanelProps {
  onFillet?: () => void;
  onChamfer?: () => void;
  onDatumPoint?: () => void;
  onDatumLine?: () => void;
  onDatumPlane?: () => void;
  onLocalCS?: () => void;
  hasSelection?: boolean;
}

export function EdgeToolsPanel({
  onFillet,
  onChamfer,
  onDatumPoint,
  onDatumLine,
  onDatumPlane,
  onLocalCS,
  hasSelection = false
}: EdgeToolsPanelProps) {
  const toolStyle = {
    padding: '0.75rem',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: hasSelection ? 'pointer' : 'not-allowed',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    width: '100%',
    textAlign: 'left' as const,
    fontSize: '0.9em',
    opacity: hasSelection ? 1 : 0.5,
    borderBottom: '1px solid #eee'
  };

  return (
    <div style={{
      width: '100%',
      backgroundColor: '#fafafa'
    }}>
      {/* Title shown in CollapsiblePanel */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <button
          onClick={onFillet}
          disabled={!hasSelection}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em' }}>⭕</span>
          <span>Fillet</span>
        </button>
        <button
          onClick={onChamfer}
          disabled={!hasSelection}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em' }}>🔺</span>
          <span>Chamfer</span>
        </button>
        <div style={{ padding: '0.5rem', fontSize: '0.85em', color: '#666', borderTop: '1px solid #ddd', borderBottom: '1px solid #ddd', backgroundColor: '#f5f5f5' }}>
          Datum Elements
        </div>
        <button
          onClick={onDatumPoint}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em', color: '#ff0000' }}>●</span>
          <span>Create a datum point</span>
        </button>
        <button
          onClick={onDatumLine}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em', color: '#ff0000' }}>━</span>
          <span>Create a datum line</span>
        </button>
        <button
          onClick={onDatumPlane}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em', color: '#ff0000' }}>◆</span>
          <span>Create a datum plane</span>
        </button>
        <button
          onClick={onLocalCS}
          style={toolStyle}
        >
          <span style={{ fontSize: '1.2em', color: '#ff0000' }}>L</span>
          <span>Create a local coordinate system</span>
        </button>
      </div>
    </div>
  );
}

