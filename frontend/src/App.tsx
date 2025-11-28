/**
 * Main application component.
 * Semantic-centric layout: 3D viewer (left), semantic tree + parameters + issues (right), code + prompt (bottom).
 */

import { useState, useEffect } from 'react';
import { Viewer3D } from './components/Viewer3D';
import { SemanticTree } from './components/SemanticTree';
import { ParameterPanel } from './components/ParameterPanel';
import { IssuesPanel } from './components/IssuesPanel';
import { DSLCodeEditor } from './components/DSLCodeEditor';
import { PromptPanel } from './components/PromptPanel';
import { QuickActionsToolbar } from './components/QuickActionsToolbar';
import { api } from './api/client';
import type { Part, RebuildResponse, ValidationIssue } from './types/ir';

function App() {
  const [part, setPart] = useState<Part | null>(null);
  const [dsl, setDSL] = useState('');
  const [mesh, setMesh] = useState<RebuildResponse['mesh'] | null>(null);
  const [paramsEval, setParamsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  // @ts-ignore - chainsEval is set but not currently displayed in UI - kept for future use
  const [chainsEval, setChainsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentMessage, setAgentMessage] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<{ type: 'param' | 'feature' | 'chain'; name: string } | null>(null);
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [showNewPartDialog, setShowNewPartDialog] = useState(false);
  const [availableTemplates, setAvailableTemplates] = useState<string[]>([]);

  // Load templates on mount
  useEffect(() => {
    api.listTemplates().then(result => {
      setAvailableTemplates(result.templates);
    }).catch(console.error);
  }, []);

  // Show new part dialog if no part is loaded
  useEffect(() => {
    if (!part && !isLoading) {
      setShowNewPartDialog(true);
    }
  }, [part, isLoading]);

  const loadModelFromDSL = async (dslText: string) => {
    try {
      setIsLoading(true);
      const parsedPart = await api.parseDSL(dslText);
      setPart(parsedPart);
      setDSL(dslText);
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
      setIssues(response.issues || []);
      // Note: rebuildModel doesn't return the part, it uses the part passed in
    } catch (error) {
      console.error('Failed to rebuild model:', error);
      alert(`Failed to rebuild model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleParseDSL = async () => {
    await loadModelFromDSL(dsl);
  };

  const handleParamChange = (paramName: string, value: number) => {
    if (!part) return;
    // Store local change, will be applied via operations
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

  const handleToleranceChange = (paramName: string, toleranceClass: string | null) => {
    if (!part) return;
    const updatedPart = {
      ...part,
      params: {
        ...part.params,
        [paramName]: {
          ...part.params[paramName],
          tolerance_class: toleranceClass,
        },
      },
    };
    setPart(updatedPart);
  };

  const handleApplyChanges = async () => {
    if (!part) return;
    
    try {
      setIsLoading(true);
      
      // Build operations from current part state vs original
      // For MVP, we'll just rebuild with the updated part
      // In a full implementation, we'd track original state and build operations
      // Operations are built in handleParamChange and passed to handleApplyChanges
      
      // For now, just rebuild with updated part
      // TODO: Build proper operations by comparing with original state
      await rebuildModel(part);
    } catch (error) {
      console.error('Failed to apply changes:', error);
      alert(`Failed to apply changes: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyOperations = async (operations: Array<{ type: string; [key: string]: any }>) => {
    if (!part) return;
    
    try {
      setIsLoading(true);
      const response = await api.applyOperations(part, operations);
      setPart(response.part);
      setMesh(response.mesh);
      setParamsEval(response.params_eval);
      setChainsEval(response.chains_eval);
      setIssues(response.issues || []);
    } catch (error) {
      console.error('Failed to apply operations:', error);
      alert(`Failed to apply operations: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportSTL = async () => {
    if (!part) return;
    
    try {
      setIsLoading(true);
      const blob = await api.exportSTL(part);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${part.name}.stl`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export STL:', error);
      alert(`Failed to export STL: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportSTEP = async () => {
    if (!part) return;
    
    try {
      setIsLoading(true);
      const blob = await api.exportSTEP(part);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${part.name}.step`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export STEP:', error);
      alert(`Failed to export STEP: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAgentCommand = async (mode: 'create' | 'edit' | 'explain', prompt: string, scopeToSelection: boolean) => {
    try {
      setIsLoading(true);
      
      // Build scope
      const scope: { selected_feature_ids?: string[]; selected_param_names?: string[]; selected_chain_names?: string[] } = {};
      if (scopeToSelection && selectedFeatureId) {
        scope.selected_feature_ids = [selectedFeatureId];
      }
      
      const response = await api.agentCommand(mode, prompt, part, scope);
      setAgentMessage(response.message);
      
      if (mode === 'explain') {
        // Explain mode: just show message, don't modify part
        // Message is already set above
      } else if (response.success && response.part) {
        // Create or Edit mode: update part and rebuild
        setPart(response.part);
        await rebuildModel(response.part);
      } else {
        // Error case
        setAgentMessage(response.message || 'Agent command failed');
      }
    } catch (error) {
      console.error('Agent command failed:', error);
      setAgentMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNewPart = async (template: string) => {
    try {
      setIsLoading(true);
      const result = await api.createNewPart(template);
      setPart(result.part);
      setDSL(result.dsl);
      await rebuildModel(result.part);
      setShowNewPartDialog(false);
    } catch (error) {
      console.error('Failed to create new part:', error);
      alert(`Failed to create new part: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleIssueClick = (issue: ValidationIssue) => {
    // Focus on related items
    if (issue.related_params.length > 0) {
      setSelectedItem({ type: 'param', name: issue.related_params[0] });
    } else if (issue.related_features.length > 0) {
      setSelectedItem({ type: 'feature', name: issue.related_features[0] });
    } else if (issue.related_chains.length > 0) {
      setSelectedItem({ type: 'chain', name: issue.related_chains[0] });
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
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {isLoading && <div>Loading...</div>}
          <button
            onClick={() => setShowNewPartDialog(true)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#4a90e2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            New Part
          </button>
          {part && (
            <>
              <button
                onClick={handleExportSTL}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Export STL
              </button>
              <button
                onClick={handleExportSTEP}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Export STEP
              </button>
            </>
          )}
        </div>
      </div>

      {/* New Part Dialog */}
      {showNewPartDialog && (
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
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '2rem',
              borderRadius: '8px',
              minWidth: '400px',
            }}
          >
            <h2 style={{ marginTop: 0 }}>Create New Part</h2>
            <p>Select a template:</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {availableTemplates.map(template => (
                <button
                  key={template}
                  onClick={() => handleCreateNewPart(template)}
                  style={{
                    padding: '0.75rem',
                    backgroundColor: '#4a90e2',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  {template.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowNewPartDialog(false)}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#ccc',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

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
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <QuickActionsToolbar
            part={part}
            selectedFeatureId={selectedFeatureId}
            onApplyOperations={handleApplyOperations}
          />
          <div style={{ flex: 1, position: 'relative' }}>
            <Viewer3D 
              mesh={mesh} 
              selectedFeatureId={selectedFeatureId}
              onFeatureSelect={(featureId) => {
                setSelectedFeatureId(featureId);
                if (featureId) {
                  setSelectedItem({ type: 'feature', name: featureId });
                }
              }}
            />
          </div>
        </div>

        {/* Side panels (right) */}
        <div
          style={{
            width: '450px',
            display: 'flex',
            flexDirection: 'column',
            borderLeft: '1px solid #ccc',
            overflow: 'hidden',
          }}
        >
          {/* Semantic Tree */}
          <div
            style={{
              height: '200px',
              borderBottom: '1px solid #ccc',
              overflow: 'auto',
            }}
          >
            <SemanticTree
              part={part}
              selectedItem={selectedItem}
              onSelect={(type, name) => {
                setSelectedItem({ type, name });
                if (type === 'feature') {
                  setSelectedFeatureId(name);
                } else if (type === 'param') {
                  // Scroll to param in parameter panel (handled by highlightedParam prop)
                  setSelectedFeatureId(null);
                } else {
                  setSelectedFeatureId(null);
                }
              }}
            />
          </div>

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
              onToleranceChange={handleToleranceChange}
              onApply={handleApplyChanges}
              paramsEval={paramsEval}
              highlightedParam={selectedItem?.type === 'param' ? selectedItem.name : null}
            />
          </div>

          {/* Issues Panel */}
          <div
            style={{
              height: '200px',
              borderBottom: '1px solid #ccc',
              overflow: 'auto',
            }}
          >
            <IssuesPanel issues={issues} onIssueClick={handleIssueClick} />
          </div>
        </div>
      </div>

      {/* Bottom panel: Code & Prompt */}
      <div
        style={{
          height: '250px',
          borderTop: '1px solid #ccc',
          display: 'flex',
          overflow: 'hidden',
        }}
      >
        {/* DSL Code Editor (collapsible) */}
        <div
          style={{
            width: '50%',
            borderRight: '1px solid #ccc',
            overflow: 'auto',
          }}
        >
          <DSLCodeEditor dsl={dsl} onDSLChange={setDSL} onParse={handleParseDSL} />
        </div>

        {/* Prompt Panel */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
          }}
        >
          <PromptPanel
            onSend={handleAgentCommand}
            isLoading={isLoading}
            lastMessage={agentMessage}
            hasPart={part !== null}
            hasSelection={selectedFeatureId !== null}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
