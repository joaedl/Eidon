/**
 * Main application component.
 * Semantic-centric layout: 3D viewer (left), semantic tree + parameters + issues (right), code + prompt (bottom).
 */

import { useState, useEffect } from 'react';
import { Viewer3D } from './components/Viewer3D';
import { FeatureTree } from './components/FeatureTree';
import { PropertyPanel } from './components/PropertyPanel';
import { TopMenuBar } from './components/TopMenuBar';
import { CursorAgentPanel } from './components/CursorAgentPanel';
import { IssuesPanel } from './components/IssuesPanel';
import { SketchEditor } from './components/SketchEditor';
import { PlaneSelectionDialog } from './components/PlaneSelectionDialog';
import { ExtrudeDialog } from './components/ExtrudeDialog';
import { DSLCodeEditor } from './components/DSLCodeEditor';
// MVP: EdgeToolsPanel disabled
import { ResizablePanel } from './components/ResizablePanel';
import { CollapsiblePanel } from './components/CollapsiblePanel';
import { api } from './api/client';
import type { Part, RebuildResponse, ValidationIssue, Sketch } from './types/ir';

function App() {
  const [part, setPart] = useState<Part | null>(null);
  const [dsl, setDSL] = useState('');
  const [mesh, setMesh] = useState<RebuildResponse['mesh'] | null>(null);
  // @ts-ignore - paramsEval used in PropertyPanel via selectedParam (future enhancement)
  const [paramsEval, setParamsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  // @ts-ignore - chainsEval is set but not currently displayed in UI - kept for future use
  const [chainsEval, setChainsEval] = useState<Record<string, { nominal: number; min: number; max: number }>>({});
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentMessage, setAgentMessage] = useState<string>('');
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [selectedSketchName, setSelectedSketchName] = useState<string | null>(null);
  const [selectedParamName, setSelectedParamName] = useState<string | null>(null);
  // MVP: Templates disabled - no dialog needed
  const [sketchMode, setSketchMode] = useState<{ sketch: Sketch; featureName: string } | null>(null);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [drawingSvg, setDrawingSvg] = useState<string | null>(null);
  const [showPlaneDialog, setShowPlaneDialog] = useState(false);
  const [showExtrudeDialog, setShowExtrudeDialog] = useState(false);
  const [showDSLCode, setShowDSLCode] = useState(false);
  
  // Panel sizes (for resizable panels)
  const [leftPanelWidth, setLeftPanelWidth] = useState(280);
  const [rightPanelWidth, setRightPanelWidth] = useState(350);
  const [propertiesPanelHeight, setPropertiesPanelHeight] = useState(300);
  // MVP: EdgeToolsPanel disabled
  // All panel size setters are used in ResizablePanel onResize callbacks

  // MVP: Auto-create empty part on mount if none exists
  useEffect(() => {
    if (!part && !isLoading) {
      handleCreateNewPart();
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

  // @ts-ignore - handleParseDSL will be used when DSL code editor is expanded
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

  // @ts-ignore - handleApplyOperations will be used in TopMenuBar tools (extrude, cut, etc.)
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
      if (response.dsl) {
        setDSL(response.dsl);
      }
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

  const handleAgentCommand = async (_mode: 'create' | 'edit' | 'explain', prompt: string, _scopeToSelection: boolean) => {
    try {
      setIsLoading(true);
      
      // Build selection context
      const selection: { selected_feature_ids?: string[]; selected_text_range?: { start: number; end: number } } = {};
      if (_scopeToSelection && selectedFeatureId) {
        selection.selected_feature_ids = [selectedFeatureId];
      }
      // TODO: Add text range selection from DSL editor
      
      // Use new intent-based API (auto-detects intent)
      const response = await api.agentCommand(prompt, part, selection, true);
      setAgentMessage(response.message);
      
      // Handle based on detected intent
      if (response.intent === 'chat_model') {
        // Pure chat - just show message, no changes
        // Message is already set above
      } else if (response.intent === 'edit_dsl') {
        // DSL or parameter edits - update part and DSL
        if (response.success && response.part) {
          setPart(response.part);
          if (response.dsl) {
            setDSL(response.dsl);
          }
          // Update validation issues
          if (response.validation_issues) {
            setIssues(response.validation_issues as ValidationIssue[]);
          }
          await rebuildModel(response.part);
        }
      } else if (response.intent === 'generate_script') {
        // Script generation - show code in message or separate panel
        if (response.script_code) {
          setAgentMessage(`${response.message}\n\n--- Generated Code ---\n\n${response.script_code}`);
        }
      } else {
        // Fallback or legacy mode
        if (response.success && response.part) {
          setPart(response.part);
          if (response.dsl) {
            setDSL(response.dsl);
          }
          await rebuildModel(response.part);
        }
      }
    } catch (error) {
      console.error('Agent command failed:', error);
      setAgentMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // MVP: Create empty part (templates disabled)
  const handleCreateNewPart = async () => {
    try {
      setIsLoading(true);
      // Template parameter ignored - backend always returns empty DSL
      const result = await api.createNewPart('new_part');
      setPart(result.part);
      setDSL(result.dsl);
      await rebuildModel(result.part);
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
      setSelectedParamName(issue.related_params[0]);
      setSelectedFeatureId(null);
      setSelectedSketchName(null);
    } else if (issue.related_features.length > 0) {
      setSelectedFeatureId(issue.related_features[0]);
      setSelectedParamName(null);
      setSelectedSketchName(null);
    }
  };

  // Get selected entities for property panel
  const selectedFeature = part && selectedFeatureId
    ? part.features.find(f => f.name === selectedFeatureId) || null
    : null;
  
  const selectedSketch = part && selectedSketchName
    ? (part.features.find(f => f.type === 'sketch' && f.name === selectedSketchName)?.sketch ||
       part.sketches?.find(s => s.name === selectedSketchName) ||
       null)
    : null;
  
  const selectedParam = part && selectedParamName
    ? part.params[selectedParamName] || null
    : null;

  const handleAgentSend = async (agentMode: 'agent' | 'ask' | 'plan', prompt: string) => {
    // Map Cursor modes to our agent modes
    const mode = agentMode === 'ask' ? 'explain' : agentMode === 'plan' ? 'explain' : 'edit';
    await handleAgentCommand(mode, prompt, false);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#f5f5f5'
      }}
    >
      {/* Top Menu Bar */}
      <TopMenuBar
        onNewPart={handleCreateNewPart}
        onSave={() => {/* TODO: Implement save */}}
        onExportSTL={handleExportSTL}
        onExportSTEP={handleExportSTEP}
        onViewDrawing={async () => {
          if (!part) return;
          try {
            setIsLoading(true);
            const svgText = await api.exportDrawing(part);
            setDrawingSvg(svgText);
            setSketchMode(null); // Exit sketch mode if active
          } catch (error) {
            console.error('Failed to export drawing:', error);
            alert(`Failed to export drawing: ${error instanceof Error ? error.message : 'Unknown error'}`);
          } finally {
            setIsLoading(false);
          }
        }}
        onSketchMode={async () => {
          if (!part) return;
          
          // Find first sketch or create new
          let sketchFeature = part.features.find(f => f.type === 'sketch' && f.sketch);
          
          if (sketchFeature && sketchFeature.sketch) {
            // Open existing sketch
            setSketchMode({ sketch: sketchFeature.sketch, featureName: sketchFeature.name });
            setDrawingSvg(null); // Exit drawing view if active
          } else {
            // Show plane selection dialog
            setShowPlaneDialog(true);
          }
        }}
        onExtrude={() => {
          if (part) {
            const sketches = part.features
              .filter(f => f.type === 'sketch' && f.sketch)
              .map(f => ({ name: f.name, plane: f.sketch?.plane || 'unknown' }));
            if (sketches.length > 0) {
              setShowExtrudeDialog(true);
            } else {
              alert('No sketches available. Please create a sketch first.');
            }
          }
        }}
        onCut={() => {/* TODO: Implement cut dialog */}}
        // MVP: Chamfer and Fillet disabled
        hasPart={!!part}
        isSketchMode={!!sketchMode}
      />

      {/* Plane Selection Dialog */}
      <PlaneSelectionDialog
        isOpen={showPlaneDialog}
        onClose={() => setShowPlaneDialog(false)}
        onSelect={async (plane) => {
          setShowPlaneDialog(false);
          // Create new empty sketch with selected plane
          try {
            setIsLoading(true);
            
            // Create a new sketch feature with empty sketch
            const newSketchName = `sketch_${Date.now()}`;
            const newSketch: Sketch = {
              name: newSketchName,
              plane: plane,
              entities: [],
              constraints: [],
              dimensions: []
            };
              
              const newSketchFeature = {
                type: 'sketch' as const,
                name: newSketchName,
                params: { plane: plane },
                sketch: newSketch,
                critical: false
              };
              
              // Add sketch feature to part
              const updatedPart = {
                ...part,
                features: [...part.features, newSketchFeature]
              };
              
              // Update DSL to include the new sketch
              let currentDSL = dsl.trim();
              if (!currentDSL || !currentDSL.includes('part')) {
                currentDSL = `part ${part.name || 'new_part'} {\n}`;
              }
              
              const sketchDSL = `  feature ${newSketchName} = sketch(on_plane="${plane}") {\n  }`;
              
              // Insert sketch before closing brace
              const dslLines = currentDSL.split('\n');
              const lastBraceIndex = dslLines.length - 1;
              const updatedDSL = [
                ...dslLines.slice(0, lastBraceIndex),
                sketchDSL,
                dslLines[lastBraceIndex]
              ].join('\n');
              
              // Parse the updated DSL to ensure it's valid
              let finalPart = updatedPart;
              try {
                const parsedPart = await api.parseDSL(updatedDSL);
                finalPart = parsedPart;
                setPart(parsedPart);
                setDSL(updatedDSL);
                
                // Find the newly created sketch feature
                const createdSketchFeature = parsedPart.features.find(f => f.type === 'sketch' && f.name === newSketchName);
                if (createdSketchFeature && createdSketchFeature.sketch) {
                  setSketchMode({ sketch: createdSketchFeature.sketch, featureName: newSketchName });
                } else {
                  // Fallback to the sketch we created
                  setSketchMode({ sketch: newSketch, featureName: newSketchName });
                }
              } catch (parseError) {
                // If parsing fails, use the manually constructed part
                console.warn('DSL parsing failed, using manually constructed part:', parseError);
                setPart(updatedPart);
                setDSL(updatedDSL);
                setSketchMode({ sketch: newSketch, featureName: newSketchName });
              }
              
              setDrawingSvg(null);
              
              // Rebuild model (though empty sketch won't generate geometry)
              await rebuildModel(finalPart);
            } catch (error) {
              console.error('Failed to create sketch:', error);
              alert(`Failed to create sketch: ${error instanceof Error ? error.message : 'Unknown error'}`);
            } finally {
              setIsLoading(false);
            }
          }}
      />

      {/* Extrude Dialog */}
      <ExtrudeDialog
        isOpen={showExtrudeDialog}
        onClose={() => setShowExtrudeDialog(false)}
        onExtrude={async (sketchName, distance, operation) => {
          if (!part) return;
          try {
            setIsLoading(true);
            
            // Create extrude feature
            const extrudeName = `extrude_${sketchName}_${Date.now()}`;
            const extrudeFeature = {
              type: 'extrude' as const,
              name: extrudeName,
              params: {
                sketch: sketchName,
                distance: distance,
                operation: operation
              },
              critical: false
            };
            
            // Add to part
            const updatedPart = {
              ...part,
              features: [...part.features, extrudeFeature]
            };
            
            // Update DSL
            let currentDSL = dsl.trim();
            if (!currentDSL || !currentDSL.includes('part')) {
              currentDSL = `part ${part.name || 'new_part'} {\n}`;
            }
            
            const extrudeDSL = `  feature ${extrudeName} = extrude(sketch="${sketchName}", distance=${distance} mm, operation="${operation}")`;
            
            const dslLines = currentDSL.split('\n');
            const lastBraceIndex = dslLines.length - 1;
            const updatedDSL = [
              ...dslLines.slice(0, lastBraceIndex),
              extrudeDSL,
              dslLines[lastBraceIndex]
            ].join('\n');
            
            // Parse and rebuild
            try {
              const parsedPart = await api.parseDSL(updatedDSL);
              setPart(parsedPart);
              setDSL(updatedDSL);
              await rebuildModel(parsedPart);
            } catch (parseError) {
              console.warn('DSL parsing failed, using manually constructed part:', parseError);
              setPart(updatedPart);
              setDSL(updatedDSL);
              await rebuildModel(updatedPart);
            }
          } catch (error) {
            console.error('Failed to create extrude:', error);
            alert(`Failed to create extrude: ${error instanceof Error ? error.message : 'Unknown error'}`);
          } finally {
            setIsLoading(false);
          }
        }}
        availableSketches={part ? part.features
          .filter(f => f.type === 'sketch' && f.sketch)
          .map(f => ({ name: f.name, plane: f.sketch?.plane || 'unknown' })) : []}
      />

      {/* MVP: Templates disabled - no dialog */}

      {/* Main content area - FreeCAD-style layout with resizable panels */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
        }}
      >
        {/* Left: Feature Tree + Properties (resizable) */}
        <ResizablePanel
          direction="horizontal"
          defaultSize={leftPanelWidth}
          minSize={150}
          maxSize={600}
          onResize={setLeftPanelWidth}
        >
          <div
            style={{
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: '#fafafa',
              borderRight: '1px solid #ddd'
            }}
          >
            {/* Feature Tree (top, collapsible) */}
            <CollapsiblePanel
              title={part?.name || 'No Part'}
              defaultExpanded={true}
              icon="📦"
            >
              <FeatureTree
                part={part}
                selectedFeatureId={selectedFeatureId}
                selectedSketchName={selectedSketchName}
                onFeatureSelect={(featureId) => {
                  setSelectedFeatureId(featureId);
                  setSelectedSketchName(null);
                  setSelectedParamName(null);
                  if (featureId && part) {
                    const feature = part.features.find(f => f.name === featureId);
                    if (feature?.type === 'sketch' && feature.sketch) {
                      setSketchMode({ sketch: feature.sketch, featureName: featureId });
                    } else {
                      setSketchMode(null);
                    }
                  }
                }}
                onSketchSelect={(sketchName) => {
                  setSelectedSketchName(sketchName);
                  setSelectedFeatureId(null);
                  setSelectedParamName(null);
                  if (sketchName && part) {
                    const sketchFeature = part.features.find(f => f.type === 'sketch' && f.name === sketchName);
                    if (sketchFeature?.sketch) {
                      setSketchMode({ sketch: sketchFeature.sketch, featureName: sketchName });
                    }
                  }
                }}
                onFeatureRightClick={(_featureId, _event) => {
                  // TODO: Show context menu
                }}
              />
            </CollapsiblePanel>

            {/* Properties Panel (bottom, resizable) */}
            <ResizablePanel
              direction="vertical"
              defaultSize={propertiesPanelHeight}
              minSize={100}
              maxSize={800}
              onResize={setPropertiesPanelHeight}
            >
              <CollapsiblePanel
                title="Properties"
                defaultExpanded={true}
                icon="⚙️"
              >
                <PropertyPanel
                  part={part}
                  selectedFeature={selectedFeature}
                  selectedSketch={selectedSketch}
                  selectedParam={selectedParam}
                  onParamChange={(name, value) => {
                    setSelectedParamName(name);
                    handleParamChange(name, value);
                  }}
                  onToleranceChange={(name, tolerance) => {
                    handleToleranceChange(name, tolerance);
                  }}
                  onApply={handleApplyChanges}
                />
              </CollapsiblePanel>
            </ResizablePanel>
          </div>
        </ResizablePanel>

        {/* Center: 3D Viewport, Sketch Editor, or Drawing View */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: sketchMode || drawingSvg ? '#fff' : '#1a1a1a',
            position: 'relative'
          }}
        >
          {drawingSvg ? (
            <div style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              overflow: 'auto'
            }}>
              <div
                dangerouslySetInnerHTML={{ __html: drawingSvg }}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%'
                }}
              />
            </div>
          ) : sketchMode ? (
            <>
              <div style={{
                padding: '0.5rem',
                borderBottom: '1px solid #ccc',
                backgroundColor: '#f0f0f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <h3 style={{ margin: 0, fontSize: '1em' }}>Sketch: {sketchMode.sketch.name}</h3>
                <button
                  onClick={() => {
                    setSketchMode(null);
                    setSelectedSketchName(null);
                  }}
                  style={{
                    padding: '0.25rem 0.75rem',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.9em'
                  }}
                >
                  Close
                </button>
              </div>
              <SketchEditor
                sketch={sketchMode.sketch}
                onSketchChange={async (updatedSketch) => {
                  if (part) {
                    const updatedPart = { ...part };
                    const featureIndex = updatedPart.features.findIndex(
                      f => f.type === 'sketch' && f.name === sketchMode.featureName
                    );
                    if (featureIndex >= 0) {
                      updatedPart.features[featureIndex] = {
                        ...updatedPart.features[featureIndex],
                        sketch: updatedSketch
                      };
                    }
                    setPart(updatedPart);
                    setSketchMode({ sketch: updatedSketch, featureName: sketchMode.featureName });
                    await rebuildModel(updatedPart);
                  }
                }}
                onEntitySelect={setSelectedEntityId}
                selectedEntityId={selectedEntityId}
                onPrompt={async (prompt) => {
                  if (part && sketchMode) {
                    try {
                      setIsLoading(true);
                      const response = await api.agentCommand(
                        prompt,
                        part,
                        {
                          sketch_name: sketchMode.featureName,
                          sketch: sketchMode.sketch,
                          selected_entity_ids: selectedEntityId ? [selectedEntityId] : []
                        },
                        true
                      );
                      
                      if (response.intent === 'edit_sketch' && response.success && response.sketch) {
                        setSketchMode({ sketch: response.sketch, featureName: sketchMode.featureName });
                        setAgentMessage(response.message);
                        if (response.part) {
                          setPart(response.part);
                          if (response.dsl) setDSL(response.dsl);
                          await rebuildModel(response.part);
                        }
                      } else {
                        setAgentMessage(response.message || 'Sketch edit failed');
                      }
                    } catch (error) {
                      console.error('Sketch edit failed:', error);
                      setAgentMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    } finally {
                      setIsLoading(false);
                    }
                  }
                }}
                isLoading={isLoading}
                lastMessage={agentMessage}
              />
            </>
          ) : (
            <Viewer3D 
              mesh={mesh} 
              selectedFeatureId={selectedFeatureId}
              onFeatureSelect={(featureId) => {
                setSelectedFeatureId(featureId);
                setSelectedSketchName(null);
                setSelectedParamName(null);
              }}
            />
          )}
        </div>

        {/* Right: Edge Tools + Issues + AI Agent (resizable) */}
        <ResizablePanel
          direction="horizontal"
          defaultSize={rightPanelWidth}
          minSize={200}
          maxSize={600}
          onResize={setRightPanelWidth}
        >
          <div
            style={{
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              borderLeft: '1px solid #ddd',
              backgroundColor: '#fff'
            }}
          >
            {/* MVP: Edge Tools Panel disabled */}

            {/* Issues Panel (middle, collapsible) */}
            <CollapsiblePanel
              title="Issues"
              defaultExpanded={true}
              icon="⚠️"
            >
              <IssuesPanel
                issues={issues}
                onIssueClick={handleIssueClick}
              />
            </CollapsiblePanel>

            {/* AI Agent Panel (bottom, collapsible) - Cursor style */}
            <CollapsiblePanel
              title="AI Agent"
              defaultExpanded={true}
              icon="🤖"
            >
              <CursorAgentPanel
                onSend={handleAgentSend}
                isLoading={isLoading}
                lastMessage={agentMessage}
                mode={sketchMode ? 'sketch' : '3d'}
              />
            </CollapsiblePanel>
          </div>
        </ResizablePanel>

        {/* DSL Code Editor Panel (bottom, collapsible) */}
        <CollapsiblePanel
          title="DSL Code"
          defaultExpanded={false}
          icon="📝"
        >
          <div style={{ padding: '1rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h3 style={{ margin: 0, fontSize: '1em' }}>Part DSL Code</h3>
            </div>
            <textarea
              value={dsl}
              onChange={(e) => setDSL(e.target.value)}
              style={{
                flex: 1,
                fontFamily: 'monospace',
                fontSize: '14px',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                resize: 'none',
                minHeight: '200px'
              }}
              spellCheck={false}
              placeholder="DSL code will appear here..."
            />
            <button
              onClick={handleParseDSL}
              style={{
                marginTop: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#4a90e2',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Apply Code
            </button>
          </div>
        </CollapsiblePanel>
      </div>
    </div>
  );
}

export default App;
