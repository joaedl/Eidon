/**
 * Prompt panel component for LLM agent interaction.
 */

import { useState } from 'react';

interface PromptPanelProps {
  onSend: (prompt: string) => void;
  isLoading?: boolean;
  lastMessage?: string;
}

export function PromptPanel({ onSend, isLoading, lastMessage }: PromptPanelProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSend(prompt);
      setPrompt('');
    }
  };

  return (
    <div style={{ padding: '1rem', borderTop: '1px solid #ccc' }}>
      <h3 style={{ marginTop: 0 }}>AI Agent</h3>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter a command for the AI agent..."
        style={{
          width: '100%',
          minHeight: '80px',
          padding: '0.5rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          resize: 'vertical',
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            handleSubmit();
          }
        }}
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
        {isLoading ? 'Sending...' : 'Send to Agent'}
      </button>
      {lastMessage && (
        <div style={{ marginTop: '1rem', padding: '0.5rem', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          <strong>Response:</strong> {lastMessage}
        </div>
      )}
    </div>
  );
}

