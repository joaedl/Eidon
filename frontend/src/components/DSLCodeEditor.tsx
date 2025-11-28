/**
 * DSL code editor component (Advanced view).
 * Collapsible panel with textarea-based editor for MVP.
 */

import { useState } from 'react';

interface DSLCodeEditorProps {
  dsl: string;
  onDSLChange: (dsl: string) => void;
  onParse: () => void;
}

export function DSLCodeEditor({ dsl, onDSLChange, onParse }: DSLCodeEditorProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isExpanded) {
    return (
      <div style={{ padding: '0.5rem', borderTop: '1px solid #ccc' }}>
        <button
          onClick={() => setIsExpanded(true)}
          style={{
            width: '100%',
            padding: '0.5rem',
            backgroundColor: '#f5f5f5',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.9em',
          }}
        >
          Advanced (Code View) ▼
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column', borderTop: '1px solid #ccc' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h3 style={{ margin: 0 }}>DSL Code</h3>
        <button
          onClick={() => setIsExpanded(false)}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: '#f5f5f5',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.85em',
          }}
        >
          Hide ▲
        </button>
      </div>
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
          marginTop: '0.5rem',
          padding: '0.5rem 1rem',
          backgroundColor: '#4a90e2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Apply Code
      </button>
    </div>
  );
}

