/**
 * Main application component.
 * Layout: 3D viewer (left), side panels (right), prompt panel (bottom).
 */

import { useState, useEffect } from 'react';
import { Viewer3D } from './components/Viewer3D';
import { ParameterPanel } from './components/ParameterPanel';
import { DSLCodeEditor } from './components/DSLCodeEditor';
import { PromptPanel } from './components/PromptPanel';
import { api } from './api/client';
import type { Part, RebuildResponse } from './types/ir';

// Default DSL model
const DEFAULT_DSL = `part shaft {
  param dia = 20 mm tolerance g6
  param length = 80 mm

  feature base = cylinder(dia_param=dia, length_param=length)
  feature chamfer_end = chamfer(edge="end", size=1)

  chain length_chain {
    terms = [length]
  }
}`;

function App() {
  const [part, setPart] = useState<Part | null>(null);
  const [dsl, setDSL] = useState(DEFAULT_DSL);
  const [mesh, setMesh] = useState<RebuildResponse['mesh'] | null>(null);
  const [paramsEval, setParamsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  const [chainsEval, setChainsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [agentMessage, setAgentMessage] = useState<string>('');

  // Load default model on mount
  useEffect(() => {
    loadModel();
  }, []);

  const loadModel = async () => {
    try {
      setIsLoading(true);
      const parsedPart = await api.parseDSL(dsl);
      setPart(parsedPart);
      await rebuildModel(parsedPart);
    } catch (error) {
      console.error('Failed to load model:', error);
      alert(`Failed to load model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const rebuildModel = async (partToRebuild: Part) => {
    try {
      setIsLoading(true);
      const response = await api.rebuild(partToRebuild);
      setMesh(response.mesh);
      setParamsEval(response.params_eval);
      setChainsEval(response.chains_eval);
    } catch (error) {
      console.error('Failed to rebuild model:', error);
      alert(`Failed to rebuild model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleParseDSL = async () => {
    try {
      setIsLoading(true);
      const parsedPart = await api.parseDSL(dsl);
      setPart(parsedPart);
      await rebuildModel(parsedPart);
    } catch (error) {
      console.error('Failed to parse DSL:', error);
      alert(`Failed to parse DSL: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleParamChange = (paramName: string, value: number) => {
    if (!part) return;
    const updatedPart = {
      ...part,
      params: {
        ...part.params,
        [paramName]: {
          ...part.params[paramName],
          value,
        },
      },
    };
    setPart(updatedPart);
  };

  const handleApplyChanges = async () => {
    if (!part) return;
    await rebuildModel(part);
  };

  const handleAgentCommand = async (prompt: string) => {
    if (!part) return;
    try {
      setIsLoading(true);
      const response = await api.agentCommand(part, prompt);
      setAgentMessage(response.message);
      if (response.success && response.part) {
        setPart(response.part);
        await rebuildModel(response.part);
      }
    } catch (error) {
      console.error('Agent command failed:', error);
      setAgentMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
      }}
    >
      {/* Top bar */}
      <div
        style={{
          padding: '1rem',
          backgroundColor: '#2c3e50',
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h1 style={{ margin: 0 }}>Eidos CAD</h1>
        {isLoading && <div>Loading...</div>}
      </div>

      {/* Main content area */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
        }}
      >
        {/* 3D Viewer (left) */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#1a1a1a',
            position: 'relative',
          }}
        >
          <Viewer3D mesh={mesh} />
        </div>

        {/* Side panels (right) */}
        <div
          style={{
            width: '400px',
            display: 'flex',
            flexDirection: 'column',
            borderLeft: '1px solid #ccc',
            overflow: 'hidden',
          }}
        >
          {/* Parameter Panel */}
          <div
            style={{
              flex: 1,
              borderBottom: '1px solid #ccc',
              overflow: 'auto',
            }}
          >
            <ParameterPanel
              part={part}
              onParamChange={handleParamChange}
              onApply={handleApplyChanges}
              paramsEval={paramsEval}
            />
          </div>

          {/* DSL Editor */}
          <div
            style={{
              flex: 1,
              borderBottom: '1px solid #ccc',
              overflow: 'hidden',
            }}
          >
            <DSLCodeEditor dsl={dsl} onDSLChange={setDSL} onParse={handleParseDSL} />
          </div>
        </div>
      </div>

      {/* Prompt Panel (bottom) */}
      <div
        style={{
          height: '200px',
          borderTop: '1px solid #ccc',
          overflow: 'auto',
        }}
      >
        <PromptPanel
          onSend={handleAgentCommand}
          isLoading={isLoading}
          lastMessage={agentMessage}
        />
      </div>
    </div>
  );
}

export default App;

