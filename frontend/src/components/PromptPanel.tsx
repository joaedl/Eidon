/**
 * Prompt panel component for LLM agent interaction.
 */

import { useState } from 'react';

type AgentMode = 'create' | 'edit' | 'explain';

interface PromptPanelProps {
  onSend: (mode: AgentMode, prompt: string, scopeToSelection: boolean) => void;
  isLoading?: boolean;
  lastMessage?: string;
  hasPart?: boolean;
  hasSelection?: boolean;
}

export function PromptPanel({ 
  onSend, 
  isLoading, 
  lastMessage, 
  hasPart = false,
  hasSelection = false 
}: PromptPanelProps) {
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState<AgentMode>(hasPart ? 'edit' : 'create');
  const [scopeToSelection, setScopeToSelection] = useState(false);

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSend(mode, prompt, scopeToSelection);
      setPrompt('');
    }
  };

  return (
    <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginTop: 0 }}>AI Agent</h3>
      
      {/* Mode selector */}
      <div style={{ marginBottom: '0.5rem' }}>
        <label style={{ marginRight: '1rem', fontSize: '0.9em' }}>
          Mode:
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as AgentMode)}
            style={{ marginLeft: '0.5rem', padding: '0.25rem' }}
            disabled={isLoading}
          >
            <option value="create" disabled={hasPart}>Create new part</option>
            <option value="edit" disabled={!hasPart}>Edit model</option>
            <option value="explain" disabled={!hasPart}>Explain</option>
          </select>
        </label>
        
        {mode === 'edit' && hasSelection && (
          <label style={{ fontSize: '0.9em' }}>
            <input
              type="checkbox"
              checked={scopeToSelection}
              onChange={(e) => setScopeToSelection(e.target.checked)}
              disabled={isLoading}
              style={{ marginRight: '0.25rem' }}
            />
            Apply only to selected feature(s)
          </label>
        )}
      </div>

      {/* Prompt input */}
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder={
          mode === 'create' 
            ? "Describe the part you want to create, e.g., 'Create a shaft with diameter 20mm and length 80mm'"
            : mode === 'edit'
            ? "Describe what to change, e.g., 'Increase diameter to 22mm'"
            : "Ask a question, e.g., 'Why is there a tolerance issue?'"
        }
        style={{
          flex: 1,
          padding: '0.5rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          resize: 'none',
          fontFamily: 'inherit',
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            handleSubmit();
          }
        }}
        disabled={isLoading}
      />
      
      <button
        onClick={handleSubmit}
        disabled={isLoading || !prompt.trim()}
        style={{
          marginTop: '0.5rem',
          padding: '0.5rem 1rem',
          backgroundColor: isLoading ? '#ccc' : '#4a90e2',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: isLoading ? 'not-allowed' : 'pointer',
        }}
      >
        {isLoading ? 'Processing...' : 'Send'}
      </button>
      
      {lastMessage && (
        <div style={{ 
          marginTop: '1rem', 
          padding: '0.75rem', 
          backgroundColor: '#f0f0f0', 
          borderRadius: '4px',
          fontSize: '0.9em',
          maxHeight: '200px',
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
        }}>
          <strong>Response:</strong>
          <div style={{ marginTop: '0.5rem' }}>{lastMessage}</div>
        </div>
      )}
    </div>
  );
}

