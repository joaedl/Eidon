/**
 * Sketch Editor component for 2D sketch editing.
 * 
 * Enhanced with:
 * - Snap to point (grid, endpoints, intersections)
 * - Improved grid (major/minor lines)
 * - Construction lines
 * - UI for dimensions and constraints
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Sketch, SketchEntity, SketchConstraint, SketchDimension } from '../types/ir';

interface SketchEditorProps {
  sketch: Sketch;
  onSketchChange?: (sketch: Sketch) => void;
  onEntitySelect?: (entityId: string | null) => void;
  selectedEntityId?: string | null;
  onPrompt?: (prompt: string) => void;
  isLoading?: boolean;
  lastMessage?: string;
}

const GRID_SIZE = 10; // Minor grid size
const MAJOR_GRID_SIZE = 50; // Major grid size
const SNAP_DISTANCE = 5; // Pixels for snapping

export function SketchEditor({
  sketch,
  onSketchChange,
  onEntitySelect,
  selectedEntityId,
  onPrompt,
  isLoading = false,
  lastMessage
}: SketchEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<'select' | 'line' | 'rectangle' | 'circle' | 'construction_line'>('select');
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<[number, number] | null>(null);
  const [previewPoint, setPreviewPoint] = useState<[number, number] | null>(null);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1.0);
  const [promptText, setPromptText] = useState('');
  const [selectedEdge, setSelectedEdge] = useState<{ entityId: string; edgeIndex: number } | null>(null);
  const [snapEnabled, setSnapEnabled] = useState(true);
  const [showDimensionDialog, setShowDimensionDialog] = useState(false);
  const [showConstraintDialog, setShowConstraintDialog] = useState(false);
  const [dimensionType, setDimensionType] = useState<'length' | 'diameter'>('length');
  const [dimensionValue, setDimensionValue] = useState('');
  const [constraintType, setConstraintType] = useState<'horizontal' | 'vertical' | 'coincident'>('horizontal');

  // Get all snap points (entity endpoints/centers first, then grid intersections)
  const getSnapPoints = useCallback((): { points: Array<[number, number]>; isEntityPoint: (point: [number, number]) => boolean } => {
    const entityPoints: Array<[number, number]> = [];
    const gridPoints: Array<[number, number]> = [];
    const entityPointSet = new Set<string>();
    
    // Entity endpoints and centers (prioritized)
    sketch.entities.forEach(entity => {
      if (entity.type === 'line' || entity.type === 'construction_line') {
        if (entity.start && entity.end) {
          const startKey = `${entity.start[0]},${entity.start[1]}`;
          const endKey = `${entity.end[0]},${entity.end[1]}`;
          if (!entityPointSet.has(startKey)) {
            entityPoints.push(entity.start);
            entityPointSet.add(startKey);
          }
          if (!entityPointSet.has(endKey)) {
            entityPoints.push(entity.end);
            entityPointSet.add(endKey);
          }
        }
      } else if (entity.type === 'circle' && entity.center) {
        const centerKey = `${entity.center[0]},${entity.center[1]}`;
        if (!entityPointSet.has(centerKey)) {
          entityPoints.push(entity.center);
          entityPointSet.add(centerKey);
        }
      } else if (entity.type === 'rectangle' && entity.corner1 && entity.corner2) {
        // All four corners of rectangle
        const [x1, y1] = entity.corner1;
        const [x2, y2] = entity.corner2;
        const corners: Array<[number, number]> = [
          [x1, y1],
          [x2, y2],
          [x1, y2],
          [x2, y1]
        ];
        corners.forEach(corner => {
          const key = `${corner[0]},${corner[1]}`;
          if (!entityPointSet.has(key)) {
            entityPoints.push(corner);
            entityPointSet.add(key);
          }
        });
      }
    });
    
    // Grid snap points (secondary, only if snap enabled)
    if (snapEnabled) {
      const canvas = canvasRef.current;
      if (canvas) {
        const worldBounds = getWorldBounds();
        const gridStartX = Math.floor(worldBounds.minX / GRID_SIZE) * GRID_SIZE;
        const gridEndX = Math.ceil(worldBounds.maxX / GRID_SIZE) * GRID_SIZE;
        const gridStartY = Math.floor(worldBounds.minY / GRID_SIZE) * GRID_SIZE;
        const gridEndY = Math.ceil(worldBounds.maxY / GRID_SIZE) * GRID_SIZE;
        
        for (let x = gridStartX; x <= gridEndX; x += GRID_SIZE) {
          for (let y = gridStartY; y <= gridEndY; y += GRID_SIZE) {
            const key = `${x},${y}`;
            // Only add grid point if it's not already an entity point
            if (!entityPointSet.has(key)) {
              gridPoints.push([x, y]);
            }
          }
        }
      }
    }
    
    // Combine: entity points first (higher priority), then grid points
    const allPoints = [...entityPoints, ...gridPoints];
    
    const isEntityPoint = (point: [number, number]): boolean => {
      const key = `${point[0]},${point[1]}`;
      return entityPointSet.has(key);
    };
    
    return { points: allPoints, isEntityPoint };
  }, [sketch.entities, snapEnabled]);

  // Snap a point to the nearest snap point, returns [snappedPoint, isEntityPoint]
  const snapPoint = useCallback((point: [number, number]): [[number, number], boolean] => {
    if (!snapEnabled) return [point, false];
    
    const { points: snapPoints, isEntityPoint } = getSnapPoints();
    if (snapPoints.length === 0) return [point, false];
    
    let minDist = Infinity;
    let snappedPoint = point;
    let snappedIsEntityPoint = false;
    
    const [px, py] = point;
    const snapThreshold = SNAP_DISTANCE / zoom;
    
    // First check entity points (higher priority)
    for (const [sx, sy] of snapPoints) {
      const dist = Math.sqrt(Math.pow(px - sx, 2) + Math.pow(py - sy, 2));
      if (dist < snapThreshold && dist < minDist) {
        const isEntity = isEntityPoint([sx, sy]);
        // Prefer entity points over grid points
        if (isEntity || !snappedIsEntityPoint) {
          minDist = dist;
          snappedPoint = [sx, sy];
          snappedIsEntityPoint = isEntity;
        }
      }
    }
    
    return [snappedPoint, snappedIsEntityPoint];
  }, [snapEnabled, getSnapPoints, zoom]);

  const getWorldBounds = (): { minX: number; maxX: number; minY: number; maxY: number } => {
    const canvas = canvasRef.current;
    if (!canvas) return { minX: -100, maxX: 100, minY: -100, maxY: 100 };
    
    const width = canvas.width / zoom;
    const height = canvas.height / zoom;
    return {
      minX: -width / 2 - viewOffset.x / zoom,
      maxX: width / 2 - viewOffset.x / zoom,
      minY: -height / 2 - viewOffset.y / zoom,
      maxY: height / 2 - viewOffset.y / zoom
    };
  };

  // Canvas setup and rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Transform for view offset and zoom
    ctx.save();
    ctx.translate(canvas.width / 2 + viewOffset.x, canvas.height / 2 + viewOffset.y);
    ctx.scale(zoom, zoom);

    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height);

    // Draw origin
    drawOrigin(ctx);

    // Draw construction lines first (dashed, lighter)
    sketch.entities
      .filter(e => e.type === 'construction_line' || (e as any).isConstruction)
      .forEach(entity => {
        drawEntity(ctx, entity, false, true);
      });

    // Draw regular entities
    sketch.entities
      .filter(e => e.type !== 'construction_line' && !(e as any).isConstruction)
      .forEach(entity => {
        const isSelected = entity.id === selectedEntityId;
        drawEntity(ctx, entity, isSelected, false, selectedEdge);
      });

    // Draw constraints (as small glyphs)
    sketch.constraints.forEach(constraint => {
      drawConstraint(ctx, constraint, sketch.entities);
    });

    // Draw dimensions
    sketch.dimensions.forEach(dimension => {
      drawDimension(ctx, dimension, sketch.entities);
    });

    // Draw preview (if drawing)
    if (isDrawing && startPoint && previewPoint) {
      drawPreview(ctx, tool, startPoint, previewPoint);
    }

    // Draw snap indicator
    if (snapEnabled && previewPoint) {
      const [snapped, isEntityPoint] = snapPoint(previewPoint);
      if (snapped[0] !== previewPoint[0] || snapped[1] !== previewPoint[1]) {
        drawSnapIndicator(ctx, snapped, isEntityPoint);
      }
    }

    ctx.restore();
  }, [sketch, selectedEntityId, viewOffset, zoom, isDrawing, startPoint, previewPoint, tool, snapEnabled, snapPoint]);

  const drawGrid = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    const bounds = getWorldBounds();
    
    // Minor grid lines
    ctx.strokeStyle = '#e8e8e8';
    ctx.lineWidth = 0.5 / zoom;
    
    for (let x = Math.floor(bounds.minX / GRID_SIZE) * GRID_SIZE; x <= bounds.maxX; x += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(x, bounds.minY);
      ctx.lineTo(x, bounds.maxY);
      ctx.stroke();
    }
    
    for (let y = Math.floor(bounds.minY / GRID_SIZE) * GRID_SIZE; y <= bounds.maxY; y += GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(bounds.minX, y);
      ctx.lineTo(bounds.maxX, y);
      ctx.stroke();
    }
    
    // Major grid lines
    ctx.strokeStyle = '#d0d0d0';
    ctx.lineWidth = 1 / zoom;
    
    for (let x = Math.floor(bounds.minX / MAJOR_GRID_SIZE) * MAJOR_GRID_SIZE; x <= bounds.maxX; x += MAJOR_GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(x, bounds.minY);
      ctx.lineTo(x, bounds.maxY);
      ctx.stroke();
    }
    
    for (let y = Math.floor(bounds.minY / MAJOR_GRID_SIZE) * MAJOR_GRID_SIZE; y <= bounds.maxY; y += MAJOR_GRID_SIZE) {
      ctx.beginPath();
      ctx.moveTo(bounds.minX, y);
      ctx.lineTo(bounds.maxX, y);
      ctx.stroke();
    }
  };

  const drawOrigin = (ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2 / zoom;
    ctx.beginPath();
    ctx.moveTo(-20, 0);
    ctx.lineTo(20, 0);
    ctx.moveTo(0, -20);
    ctx.lineTo(0, 20);
    ctx.stroke();
    
    // Origin circle
    ctx.fillStyle = '#666';
    ctx.beginPath();
    ctx.arc(0, 0, 3 / zoom, 0, 2 * Math.PI);
    ctx.fill();
  };

  const drawEntity = (ctx: CanvasRenderingContext2D, entity: SketchEntity, isSelected: boolean, isConstruction: boolean, selectedEdge: { entityId: string; edgeIndex: number } | null = null) => {
    const strokeColor = isConstruction ? '#999' : (isSelected ? '#ff4444' : '#333');
    const lineWidth = isConstruction ? 1 : (isSelected ? 3 : 2);
    const linePattern = isConstruction ? [5, 5] : [];
    
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = lineWidth / zoom;
    ctx.setLineDash(linePattern);

    if (entity.type === 'line' || entity.type === 'construction_line') {
      if (entity.start && entity.end) {
        ctx.beginPath();
        ctx.moveTo(entity.start[0], -entity.start[1]);
        ctx.lineTo(entity.end[0], -entity.end[1]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw endpoints
        if (!isConstruction) {
          ctx.fillStyle = isSelected ? '#ff4444' : '#333';
          ctx.beginPath();
          ctx.arc(entity.start[0], -entity.start[1], 3 / zoom, 0, 2 * Math.PI);
          ctx.fill();
          ctx.beginPath();
          ctx.arc(entity.end[0], -entity.end[1], 3 / zoom, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
    } else if (entity.type === 'circle' && entity.center && entity.radius) {
      ctx.beginPath();
      ctx.arc(entity.center[0], -entity.center[1], entity.radius, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.setLineDash([]);
      if (isSelected && !isConstruction) {
        ctx.fill();
      }
    } else if (entity.type === 'rectangle' && entity.corner1 && entity.corner2) {
      const [x1, y1] = entity.corner1;
      const [x2, y2] = entity.corner2;
      const minX = Math.min(x1, x2);
      const maxX = Math.max(x1, x2);
      const minY = Math.min(y1, y2);
      const maxY = Math.max(y1, y2);
      
      // Draw rectangle outline
      ctx.beginPath();
      ctx.rect(
        minX,
        -maxY,
        Math.abs(x2 - x1),
        Math.abs(y2 - y1)
      );
      ctx.stroke();
      ctx.setLineDash([]);
      if (isSelected && !isConstruction) {
        ctx.fill();
      }
      
      // Draw edges with highlighting for selected edge
      if (isSelected && selectedEdge && selectedEdge.entityId === entity.id && !isConstruction) {
        const edges: Array<{ start: [number, number]; end: [number, number] }> = [
          { start: [minX, minY], end: [maxX, minY] }, // bottom
          { start: [maxX, minY], end: [maxX, maxY] }, // right
          { start: [maxX, maxY], end: [minX, maxY] }, // top
          { start: [minX, maxY], end: [minX, minY] }  // left
        ];
        
        edges.forEach((edge, index) => {
          if (index === selectedEdge.edgeIndex) {
            // Highlight selected edge
            ctx.strokeStyle = '#ff6600';
            ctx.lineWidth = (lineWidth + 2) / zoom;
            ctx.beginPath();
            ctx.moveTo(edge.start[0], -edge.start[1]);
            ctx.lineTo(edge.end[0], -edge.end[1]);
            ctx.stroke();
            ctx.strokeStyle = strokeColor; // Reset
            ctx.lineWidth = lineWidth / zoom;
          }
        });
      }
      
      // Draw corner points
      if (!isConstruction) {
        ctx.fillStyle = isSelected ? '#ff4444' : '#333';
        const corners: Array<[number, number]> = [
          [x1, y1],
          [x2, y2],
          [x1, y2],
          [x2, y1]
        ];
        corners.forEach(([cx, cy]) => {
          ctx.beginPath();
          ctx.arc(cx, -cy, 3 / zoom, 0, 2 * Math.PI);
          ctx.fill();
        });
      }
    }
  };

  const drawPreview = (ctx: CanvasRenderingContext2D, toolType: string, start: [number, number], end: [number, number]) => {
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1 / zoom;
    ctx.setLineDash([3, 3]);
    
    if (toolType === 'line' || toolType === 'construction_line') {
      ctx.beginPath();
      ctx.moveTo(start[0], -start[1]);
      ctx.lineTo(end[0], -end[1]);
      ctx.stroke();
    } else if (toolType === 'rectangle') {
      ctx.beginPath();
      ctx.rect(
        Math.min(start[0], end[0]),
        -Math.max(start[1], end[1]),
        Math.abs(end[0] - start[0]),
        Math.abs(end[1] - start[1])
      );
      ctx.stroke();
    } else if (toolType === 'circle') {
      const radius = Math.sqrt(Math.pow(end[0] - start[0], 2) + Math.pow(end[1] - start[1], 2));
      ctx.beginPath();
      ctx.arc(start[0], -start[1], radius, 0, 2 * Math.PI);
      ctx.stroke();
    }
    
    ctx.setLineDash([]);
  };

  const drawSnapIndicator = (ctx: CanvasRenderingContext2D, point: [number, number], isEntityPoint: boolean) => {
    // Different colors for entity points vs grid points
    const color = isEntityPoint ? '#ff6600' : '#00aaff'; // Orange for entity points, blue for grid
    ctx.strokeStyle = color;
    ctx.lineWidth = 2 / zoom;
    ctx.fillStyle = color;
    
    if (isEntityPoint) {
      // For entity points: draw a filled circle (more prominent)
      ctx.beginPath();
      ctx.arc(point[0], -point[1], 5 / zoom, 0, 2 * Math.PI);
      ctx.fill();
      // Outer ring
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5 / zoom;
      ctx.beginPath();
      ctx.arc(point[0], -point[1], 7 / zoom, 0, 2 * Math.PI);
      ctx.stroke();
    } else {
      // For grid points: draw crosshair (less prominent)
      const size = 6 / zoom;
      ctx.beginPath();
      ctx.moveTo(point[0] - size, -point[1]);
      ctx.lineTo(point[0] + size, -point[1]);
      ctx.moveTo(point[0], -point[1] - size);
      ctx.lineTo(point[0], -point[1] + size);
      ctx.stroke();
      
      // Small circle
      ctx.beginPath();
      ctx.arc(point[0], -point[1], 3 / zoom, 0, 2 * Math.PI);
      ctx.stroke();
    }
  };

  const drawConstraint = (ctx: CanvasRenderingContext2D, constraint: SketchConstraint, entities: SketchEntity[]) => {
    const constraintEntities = entities.filter(e => constraint.entity_ids.includes(e.id));
    if (constraintEntities.length === 0) return;

    ctx.fillStyle = '#00aaff';
    ctx.font = `${12 / zoom}px Arial`;

    const entity = constraintEntities[0];
    let x = 0, y = 0;

    if (entity.type === 'line' && entity.start) {
      x = entity.start[0];
      y = -entity.start[1];
    } else if (entity.type === 'circle' && entity.center) {
      x = entity.center[0];
      y = -entity.center[1];
    }

    const abbrev: Record<string, string> = {
      horizontal: 'H',
      vertical: 'V',
      coincident: 'C'
    };

    ctx.fillText(abbrev[constraint.type] || constraint.type[0].toUpperCase(), x + 5 / zoom, y - 5 / zoom);
  };

  const drawDimension = (ctx: CanvasRenderingContext2D, dimension: SketchDimension, entities: SketchEntity[]) => {
    const entity = entities.find(e => dimension.entity_ids.includes(e.id));
    if (!entity) return;

    ctx.strokeStyle = '#00aa00';
    ctx.lineWidth = 1 / zoom;
    ctx.fillStyle = '#00aa00';
    ctx.font = `${10 / zoom}px Arial`;

    if (dimension.type === 'length' && entity.type === 'line' && entity.start && entity.end) {
      const midX = (entity.start[0] + entity.end[0]) / 2;
      const midY = (-entity.start[1] + -entity.end[1]) / 2;
      const angle = Math.atan2(
        entity.end[1] - entity.start[1],
        entity.end[0] - entity.start[0]
      );

      const offset = 20 / zoom;
      const perpAngle = angle + Math.PI / 2;
      const dimX = midX + Math.cos(perpAngle) * offset;
      const dimY = midY + Math.sin(perpAngle) * offset;

      ctx.beginPath();
      ctx.moveTo(midX, midY);
      ctx.lineTo(dimX, dimY);
      ctx.stroke();

      ctx.fillText(
        `${dimension.value} ${dimension.unit}`,
        dimX + 5 / zoom,
        dimY
      );
    } else if (dimension.type === 'diameter' && entity.type === 'circle' && entity.center && entity.radius) {
      const cx = entity.center[0];
      const cy = -entity.center[1];
      const r = entity.radius;
      
      ctx.beginPath();
      ctx.moveTo(cx - r - 20 / zoom, cy);
      ctx.lineTo(cx + r + 20 / zoom, cy);
      ctx.stroke();
      
      ctx.fillText(
        `⌀${dimension.value} ${dimension.unit}`,
        cx,
        cy - 10 / zoom
      );
    }
  };

  const screenToWorld = (screenX: number, screenY: number): [number, number] => {
    const canvas = canvasRef.current;
    if (!canvas) return [0, 0];

    const rect = canvas.getBoundingClientRect();
    const x = (screenX - rect.left - canvas.width / 2 - viewOffset.x) / zoom;
    const y = (-(screenY - rect.top - canvas.height / 2 - viewOffset.y)) / zoom;
    return [x, y];
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    let [x, y] = screenToWorld(e.clientX, e.clientY);
    const [[snappedX, snappedY], _] = snapPoint([x, y]);
    x = snappedX;
    y = snappedY;

    if (tool === 'select') {
      let clickedEntity: SketchEntity | null = null;
      let clickedEdge: { entityId: string; edgeIndex: number } | null = null;
      let minDist = Infinity;
      const selectionThreshold = 8 / zoom; // Increased threshold for easier selection
      
      for (const entity of sketch.entities) {
        if (entity.type === 'line' || entity.type === 'construction_line') {
          if (entity.start && entity.end) {
            const dist = pointToLineDistance([x, y], entity.start, entity.end);
            if (dist < selectionThreshold && dist < minDist) {
              minDist = dist;
              clickedEntity = entity;
              clickedEdge = null; // Line itself is the edge
            }
          }
        } else if (entity.type === 'circle' && entity.center && entity.radius) {
          const dist = Math.sqrt(
            Math.pow(x - entity.center[0], 2) + Math.pow(y - (-entity.center[1]), 2)
          );
          const edgeDist = Math.abs(dist - entity.radius);
          if (edgeDist < selectionThreshold && edgeDist < minDist) {
            minDist = edgeDist;
            clickedEntity = entity;
            clickedEdge = null; // Circle doesn't have separate edges
          }
        } else if (entity.type === 'rectangle' && entity.corner1 && entity.corner2) {
          const [x1, y1] = entity.corner1;
          const [x2, y2] = entity.corner2;
          const minX = Math.min(x1, x2);
          const maxX = Math.max(x1, x2);
          const minY = Math.min(y1, y2);
          const maxY = Math.max(y1, y2);
          
          // Check which edge is closest
          const edges: Array<{ start: [number, number]; end: [number, number]; index: number }> = [
            { start: [minX, minY], end: [maxX, minY], index: 0 }, // bottom
            { start: [maxX, minY], end: [maxX, maxY], index: 1 }, // right
            { start: [maxX, maxY], end: [minX, maxY], index: 2 }, // top
            { start: [minX, maxY], end: [minX, minY], index: 3 }  // left
          ];
          
          let closestEdgeDist = Infinity;
          let closestEdgeIndex = -1;
          
          for (const edge of edges) {
            const dist = pointToLineDistance([x, y], edge.start, edge.end);
            if (dist < selectionThreshold && dist < closestEdgeDist) {
              closestEdgeDist = dist;
              closestEdgeIndex = edge.index;
            }
          }
          
          if (closestEdgeIndex >= 0) {
            clickedEntity = entity;
            clickedEdge = { entityId: entity.id, edgeIndex: closestEdgeIndex };
            break; // Rectangle edge selection takes priority
          }
        }
      }
      
      if (clickedEntity) {
        onEntitySelect?.(clickedEntity.id);
        setSelectedEdge(clickedEdge);
      } else {
        onEntitySelect?.(null);
        setSelectedEdge(null);
      }
    } else {
      setIsDrawing(true);
      setStartPoint([x, y]);
      setPreviewPoint([x, y]);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPoint) return;
    
    let [x, y] = screenToWorld(e.clientX, e.clientY);
    const [[snappedX, snappedY], _] = snapPoint([x, y]);
    setPreviewPoint([snappedX, snappedY]);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPoint) {
      setIsDrawing(false);
      return;
    }

    let [endX, endY] = screenToWorld(e.clientX, e.clientY);
    const [[snappedEndX, snappedEndY], _] = snapPoint([endX, endY]);
    endX = snappedEndX;
    endY = snappedEndY;
    const [startX, startY] = startPoint;

    const newEntity: SketchEntity = {
      id: `${tool}_${Date.now()}`,
      type: tool === 'line' ? 'line' : tool === 'construction_line' ? 'line' : tool === 'rectangle' ? 'rectangle' : 'circle',
    };

    if (tool === 'line' || tool === 'construction_line') {
      newEntity.start = [startX, -startY];
      newEntity.end = [endX, -endY];
      if (tool === 'construction_line') {
        (newEntity as any).isConstruction = true;
      }
    } else if (tool === 'rectangle') {
      newEntity.corner1 = [startX, -startY];
      newEntity.corner2 = [endX, -endY];
    } else if (tool === 'circle') {
      const radius = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
      newEntity.center = [startX, -startY];
      newEntity.radius = radius;
    }

    const updatedSketch: Sketch = {
      ...sketch,
      entities: [...sketch.entities, newEntity]
    };

    onSketchChange?.(updatedSketch);
    setIsDrawing(false);
    setStartPoint(null);
    setPreviewPoint(null);
  };

  const handleAddDimension = () => {
    if (!selectedEntityId) {
      alert('Please select an entity or edge first');
      return;
    }
    
    // Determine available dimension types based on selected entity
    const entity = sketch.entities.find(e => e.id === selectedEntityId);
    if (!entity) return;
    
    // For rectangles, we need to create a line entity for the selected edge
    // For circles, only diameter makes sense
    // For lines, only length makes sense
    if (entity.type === 'circle') {
      setDimensionType('diameter');
    } else {
      setDimensionType('length');
    }
    
    setShowDimensionDialog(true);
  };

  const handleDimensionSubmit = () => {
    if (!selectedEntityId || !dimensionValue) return;
    
    const value = parseFloat(dimensionValue);
    if (isNaN(value) || value <= 0) {
      alert('Please enter a valid positive number');
      return;
    }

    const entity = sketch.entities.find(e => e.id === selectedEntityId);
    if (!entity) return;

    // For rectangles, we need to create a line entity for the selected edge
    let dimensionEntityId = selectedEntityId;
    
    if (entity.type === 'rectangle' && selectedEdge) {
      // Create a line entity representing the selected edge
      const [x1, y1] = entity.corner1!;
      const [x2, y2] = entity.corner2!;
      const minX = Math.min(x1, x2);
      const maxX = Math.max(x1, x2);
      const minY = Math.min(y1, y2);
      const maxY = Math.max(y1, y2);
      
      const edges: Array<{ start: [number, number]; end: [number, number] }> = [
        { start: [minX, minY], end: [maxX, minY] }, // bottom
        { start: [maxX, minY], end: [maxX, maxY] }, // right
        { start: [maxX, maxY], end: [minX, maxY] }, // top
        { start: [minX, maxY], end: [minX, minY] }  // left
      ];
      
      const edge = edges[selectedEdge.edgeIndex];
      const edgeLineId = `edge_${selectedEntityId}_${selectedEdge.edgeIndex}`;
      
      // Check if edge line already exists
      let edgeLine = sketch.entities.find(e => e.id === edgeLineId);
      if (!edgeLine) {
        // Create a line entity for this edge
        edgeLine = {
          id: edgeLineId,
          type: 'line',
          start: edge.start,
          end: edge.end
        };
        
        // Add the edge line to the sketch
        const updatedSketchWithEdge: Sketch = {
          ...sketch,
          entities: [...sketch.entities, edgeLine]
        };
        
        // Create dimension for the edge line
        const newDimension: SketchDimension = {
          id: `dim_${Date.now()}`,
          type: 'length',
          entity_ids: [edgeLineId],
          value: value,
          unit: 'mm'
        };
        
        const finalSketch: Sketch = {
          ...updatedSketchWithEdge,
          dimensions: [...updatedSketchWithEdge.dimensions, newDimension]
        };
        
        onSketchChange?.(finalSketch);
      } else {
        // Edge line exists, just add dimension
        const newDimension: SketchDimension = {
          id: `dim_${Date.now()}`,
          type: 'length',
          entity_ids: [edgeLineId],
          value: value,
          unit: 'mm'
        };
        
        const updatedSketch: Sketch = {
          ...sketch,
          dimensions: [...sketch.dimensions, newDimension]
        };
        
        onSketchChange?.(updatedSketch);
      }
    } else {
      // For lines and circles, dimension the entity directly
      const newDimension: SketchDimension = {
        id: `dim_${Date.now()}`,
        type: dimensionType,
        entity_ids: [dimensionEntityId],
        value: value,
        unit: 'mm'
      };

      const updatedSketch: Sketch = {
        ...sketch,
        dimensions: [...sketch.dimensions, newDimension]
      };

      onSketchChange?.(updatedSketch);
    }

    setShowDimensionDialog(false);
    setDimensionValue('');
  };

  const handleAddConstraint = () => {
    if (!selectedEntityId) {
      alert('Please select an entity first');
      return;
    }
    setShowConstraintDialog(true);
  };

  const handleConstraintSubmit = () => {
    if (!selectedEntityId) return;

    const entityIds = constraintType === 'coincident' 
      ? [selectedEntityId] // For coincident, user will need to select second entity
      : [selectedEntityId];

    const newConstraint: SketchConstraint = {
      id: `constraint_${Date.now()}`,
      type: constraintType,
      entity_ids: entityIds,
      params: {}
    };

    const updatedSketch: Sketch = {
      ...sketch,
      constraints: [...sketch.constraints, newConstraint]
    };

    onSketchChange?.(updatedSketch);
    setShowConstraintDialog(false);
  };

  const handlePromptSubmit = () => {
    if (promptText.trim() && onPrompt) {
      onPrompt(promptText);
      setPromptText('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ padding: '0.5rem', borderBottom: '1px solid #ccc', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setTool('select')}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: tool === 'select' ? '#4a90e2' : '#f0f0f0',
            color: tool === 'select' ? 'white' : 'black',
            border: '1px solid #ccc',
            cursor: 'pointer'
          }}
        >
          Select
        </button>
        <button
          onClick={() => setTool('line')}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: tool === 'line' ? '#4a90e2' : '#f0f0f0',
            color: tool === 'line' ? 'white' : 'black',
            border: '1px solid #ccc',
            cursor: 'pointer'
          }}
        >
          Line
        </button>
        <button
          onClick={() => setTool('construction_line')}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: tool === 'construction_line' ? '#4a90e2' : '#f0f0f0',
            color: tool === 'construction_line' ? 'white' : 'black',
            border: '1px solid #ccc',
            cursor: 'pointer'
          }}
        >
          Construction
        </button>
        <button
          onClick={() => setTool('rectangle')}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: tool === 'rectangle' ? '#4a90e2' : '#f0f0f0',
            color: tool === 'rectangle' ? 'white' : 'black',
            border: '1px solid #ccc',
            cursor: 'pointer'
          }}
        >
          Rectangle
        </button>
        <button
          onClick={() => setTool('circle')}
          style={{
            padding: '0.25rem 0.5rem',
            backgroundColor: tool === 'circle' ? '#4a90e2' : '#f0f0f0',
            color: tool === 'circle' ? 'white' : 'black',
            border: '1px solid #ccc',
            cursor: 'pointer'
          }}
        >
          Circle
        </button>
        
        <div style={{ marginLeft: '1rem', paddingLeft: '1rem', borderLeft: '1px solid #ccc', display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleAddConstraint}
            disabled={!selectedEntityId}
            style={{
              padding: '0.25rem 0.5rem',
              backgroundColor: selectedEntityId ? '#f0f0f0' : '#e0e0e0',
              color: selectedEntityId ? 'black' : '#999',
              border: '1px solid #ccc',
              cursor: selectedEntityId ? 'pointer' : 'not-allowed'
            }}
          >
            Add Constraint
          </button>
          <button
            onClick={handleAddDimension}
            disabled={!selectedEntityId}
            style={{
              padding: '0.25rem 0.5rem',
              backgroundColor: selectedEntityId ? '#f0f0f0' : '#e0e0e0',
              color: selectedEntityId ? 'black' : '#999',
              border: '1px solid #ccc',
              cursor: selectedEntityId ? 'pointer' : 'not-allowed'
            }}
            title={selectedEntityId ? (selectedEdge ? 'Add dimension to selected edge' : 'Add dimension to selected entity') : 'Select an entity or edge first'}
          >
            Add Dimension
          </button>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontSize: '0.9em', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <input
              type="checkbox"
              checked={snapEnabled}
              onChange={(e) => setSnapEnabled(e.target.checked)}
            />
            Snap
          </label>
          <button
            onClick={() => setZoom(zoom * 1.2)}
            style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', cursor: 'pointer' }}
          >
            +
          </button>
          <span>{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom(zoom / 1.2)}
            style={{ padding: '0.25rem 0.5rem', border: '1px solid #ccc', cursor: 'pointer' }}
          >
            -
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{
            width: '100%',
            height: '100%',
            cursor: tool === 'select' ? 'default' : 'crosshair'
          }}
        />
      </div>

      {/* Dimension Dialog */}
      {showDimensionDialog && (() => {
        const entity = sketch.entities.find(e => e.id === selectedEntityId);
        const availableTypes: Array<'length' | 'diameter'> = 
          entity?.type === 'circle' ? ['diameter'] : ['length'];
        const canChooseType = availableTypes.length > 1;
        
        return (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'white',
            padding: '1rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
            zIndex: 1000
          }}>
            <h3 style={{ marginTop: 0 }}>Add Dimension</h3>
            {selectedEdge && (
              <p style={{ fontSize: '0.9em', color: '#666', marginTop: 0 }}>
                Dimensioning edge {selectedEdge.edgeIndex + 1} of rectangle
              </p>
            )}
            {canChooseType && (
              <div style={{ marginBottom: '0.5rem' }}>
                <label>
                  Type:
                  <select
                    value={dimensionType}
                    onChange={(e) => setDimensionType(e.target.value as 'length' | 'diameter')}
                    style={{ marginLeft: '0.5rem', padding: '0.25rem' }}
                  >
                    {availableTypes.map(type => (
                      <option key={type} value={type}>
                        {type === 'length' ? 'Length' : 'Diameter'}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}
            {!canChooseType && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.9em', color: '#666' }}>
                Type: {dimensionType === 'length' ? 'Length' : 'Diameter'} (auto-selected)
              </div>
            )}
            <div style={{ marginBottom: '0.5rem' }}>
              <label>
                Value (mm):
                <input
                  type="number"
                  value={dimensionValue}
                  onChange={(e) => setDimensionValue(e.target.value)}
                  style={{ marginLeft: '0.5rem', padding: '0.25rem', width: '100px' }}
                  min="0"
                  step="0.1"
                />
              </label>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowDimensionDialog(false)}>Cancel</button>
              <button onClick={handleDimensionSubmit}>Add</button>
            </div>
          </div>
        );
      })()}

      {/* Constraint Dialog */}
      {showConstraintDialog && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'white',
          padding: '1rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
          zIndex: 1000
        }}>
          <h3 style={{ marginTop: 0 }}>Add Constraint</h3>
          <div style={{ marginBottom: '0.5rem' }}>
            <label>
              Type:
              <select
                value={constraintType}
                onChange={(e) => setConstraintType(e.target.value as 'horizontal' | 'vertical' | 'coincident')}
                style={{ marginLeft: '0.5rem', padding: '0.25rem' }}
              >
                <option value="horizontal">Horizontal</option>
                <option value="vertical">Vertical</option>
                <option value="coincident">Coincident</option>
              </select>
            </label>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button onClick={() => setShowConstraintDialog(false)}>Cancel</button>
            <button onClick={handleConstraintSubmit}>Add</button>
          </div>
        </div>
      )}

      {/* Prompt bar */}
      {onPrompt && (
        <div style={{ padding: '0.5rem', borderTop: '1px solid #ccc', display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                handlePromptSubmit();
              }
            }}
            placeholder="Ask AI to modify sketch (e.g., 'Draw a rectangle 50 by 30mm')"
            style={{ flex: 1, padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
            disabled={isLoading}
          />
          <button
            onClick={handlePromptSubmit}
            disabled={isLoading || !promptText.trim()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: isLoading ? '#ccc' : '#4a90e2',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? 'Processing...' : 'Ask AI'}
          </button>
        </div>
      )}

      {/* Message display */}
      {lastMessage && (
        <div style={{
          padding: '0.5rem',
          backgroundColor: '#f0f0f0',
          borderTop: '1px solid #ccc',
          fontSize: '0.9em',
          maxHeight: '100px',
          overflow: 'auto'
        }}>
          <strong>Response:</strong> {lastMessage}
        </div>
      )}
    </div>
  );
}

// Helper function for point-to-line distance
function pointToLineDistance(
  point: [number, number],
  lineStart: [number, number],
  lineEnd: [number, number]
): number {
  const [px, py] = point;
  const [x1, y1] = lineStart;
  const [x2, y2] = lineEnd;

  const A = px - x1;
  const B = py - y1;
  const C = x2 - x1;
  const D = y2 - y1;

  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  let param = -1;
  if (lenSq !== 0) param = dot / lenSq;

  let xx, yy;

  if (param < 0) {
    xx = x1;
    yy = y1;
  } else if (param > 1) {
    xx = x2;
    yy = y2;
  } else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  const dx = px - xx;
  const dy = py - yy;
  return Math.sqrt(dx * dx + dy * dy);
}

