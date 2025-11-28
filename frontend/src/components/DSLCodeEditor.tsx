/**
 * DSL code editor component.
 * Simple textarea-based editor for MVP (can be upgraded to Monaco later).
 */

interface DSLCodeEditorProps {
  dsl: string;
  onDSLChange: (dsl: string) => void;
  onParse: () => void;
}

export function DSLCodeEditor({ dsl, onDSLChange, onParse }: DSLCodeEditorProps) {
  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ marginTop: 0 }}>DSL Code</h2>
      <textarea
        value={dsl}
        onChange={(e) => onDSLChange(e.target.value)}
        style={{
          flex: 1,
          fontFamily: 'monospace',
          fontSize: '14px',
          padding: '0.5rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          resize: 'none',
        }}
        spellCheck={false}
      />
      <button
        onClick={onParse}
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
        Parse & Rebuild
      </button>
    </div>
  );
}

