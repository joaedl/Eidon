/**
 * Cursor Agent Panel - AI assistant panel like Cursor IDE.
 * Supports agent/ask/plan modes for both sketch and 3D modes.
 */

import { useState } from 'react';

type AgentMode = 'agent' | 'ask' | 'plan';

interface CursorAgentPanelProps {
  onSend: (mode: AgentMode, prompt: string) => void;
  isLoading?: boolean;
  lastMessage?: string;
  mode?: 'sketch' | '3d';
}

export function CursorAgentPanel({
  onSend,
  isLoading = false,
  lastMessage = '',
  mode = '3d'
}: CursorAgentPanelProps) {
  const [currentMode, setCurrentMode] = useState<AgentMode>('agent');
  const [prompt, setPrompt] = useState('');

  const handleSubmit = () => {
    if (prompt.trim() && !isLoading) {
      onSend(currentMode, prompt);
      setPrompt('');
    }
  };

  const modeDescriptions = {
    agent: mode === 'sketch' 
      ? 'AI will modify the sketch (add entities, constraints, dimensions)'
      : 'AI will modify the model (add features, change parameters)',
    ask: 'Ask questions about the model without making changes',
    plan: 'Get a step-by-step plan for achieving a goal'
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#1e1e1e',
      color: '#d4d4d4',
      borderLeft: '1px solid #3e3e3e'
    }}>
      {/* Header - title shown in CollapsiblePanel */}

      {/* Mode selector */}
      <div style={{
        padding: '0.5rem',
        borderBottom: '1px solid #3e3e3e',
        display: 'flex',
        gap: '0.25rem',
        backgroundColor: '#2d2d2d'
      }}>
        {(['agent', 'ask', 'plan'] as AgentMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setCurrentMode(m)}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '0.5rem',
              backgroundColor: currentMode === m ? '#0e639c' : '#3e3e3e',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.85em',
              textTransform: 'capitalize',
              opacity: isLoading ? 0.6 : 1
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Mode description */}
      <div style={{
        padding: '0.5rem 0.75rem',
        fontSize: '0.8em',
        color: '#858585',
        backgroundColor: '#252526',
        borderBottom: '1px solid #3e3e3e'
      }}>
        {modeDescriptions[currentMode]}
      </div>

      {/* Chat history */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        {lastMessage && (
          <div style={{
            padding: '0.75rem',
            backgroundColor: '#2d2d2d',
            borderRadius: '4px',
            fontSize: '0.9em',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.5'
          }}>
            {lastMessage}
          </div>
        )}
        {!lastMessage && !isLoading && (
          <div style={{
            color: '#858585',
            fontSize: '0.85em',
            textAlign: 'center',
            padding: '2rem'
          }}>
            Start a conversation with the AI agent
          </div>
        )}
        {isLoading && (
          <div style={{
            color: '#858585',
            fontSize: '0.85em',
            textAlign: 'center',
            padding: '1rem'
          }}>
            Thinking...
          </div>
        )}
      </div>

      {/* Input area */}
      <div style={{
        padding: '0.75rem',
        borderTop: '1px solid #3e3e3e',
        backgroundColor: '#252526'
      }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                handleSubmit();
              }
            }}
            placeholder={
              currentMode === 'agent'
                ? mode === 'sketch'
                  ? 'Modify sketch (e.g., "Draw a rectangle 50x30mm")'
                  : 'Modify model (e.g., "Increase diameter to 25mm")'
                : currentMode === 'ask'
                ? 'Ask a question (e.g., "Why is there a tolerance issue?")'
                : 'Describe a goal (e.g., "Create a robot leg segment")'
            }
            style={{
              flex: 1,
              padding: '0.75rem',
              backgroundColor: '#1e1e1e',
              color: '#d4d4d4',
              border: '1px solid #3e3e3e',
              borderRadius: '4px',
              resize: 'none',
              fontFamily: 'inherit',
              fontSize: '0.9em',
              minHeight: '60px',
              maxHeight: '120px'
            }}
            disabled={isLoading}
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !prompt.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: isLoading || !prompt.trim() ? '#3e3e3e' : '#0e639c',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading || !prompt.trim() ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              alignSelf: 'flex-end'
            }}
          >
            Send
          </button>
        </div>
        <div style={{
          fontSize: '0.75em',
          color: '#858585',
          marginTop: '0.5rem',
          textAlign: 'center'
        }}>
          Ctrl+Enter to send
        </div>
      </div>
    </div>
  );
}

