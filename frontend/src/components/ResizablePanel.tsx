/**
 * Resizable Panel component with draggable divider.
 * Allows users to resize panels by dragging the divider.
 */

import { useState, useRef, useEffect } from 'react';

interface ResizablePanelProps {
  children: React.ReactNode;
  direction: 'horizontal' | 'vertical';
  minSize?: number;
  maxSize?: number;
  defaultSize?: number;
  onResize?: (size: number) => void;
  className?: string;
}

export function ResizablePanel({
  children,
  direction,
  minSize = 50,
  maxSize = Infinity,
  defaultSize,
  onResize,
  className = ''
}: ResizablePanelProps) {
  const [size, setSize] = useState(defaultSize || (direction === 'horizontal' ? 300 : 200));
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (defaultSize !== undefined && !isResizing) {
      setSize(defaultSize);
    }
  }, [defaultSize, isResizing]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!panelRef.current) return;

      const rect = panelRef.current.getBoundingClientRect();
      let newSize: number;

      if (direction === 'horizontal') {
        newSize = e.clientX - rect.left;
      } else {
        newSize = e.clientY - rect.top;
      }

      newSize = Math.max(minSize, Math.min(maxSize, newSize));
      setSize(newSize);
      onResize?.(newSize);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, direction, minSize, maxSize, onResize]);

  const style: React.CSSProperties = {
    [direction === 'horizontal' ? 'width' : 'height']: `${size}px`,
    position: 'relative',
    display: 'flex',
    flexDirection: direction === 'horizontal' ? 'row' : 'column',
    overflow: 'hidden'
  };

  return (
    <div ref={panelRef} style={style} className={className}>
      {children}
      <div
        onMouseDown={handleMouseDown}
        style={{
          position: 'absolute',
          [direction === 'horizontal' ? 'right' : 'bottom']: 0,
          [direction === 'horizontal' ? 'width' : 'height']: '4px',
          [direction === 'horizontal' ? 'height' : 'width']: '100%',
          cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize',
          backgroundColor: isResizing ? '#4a90e2' : '#ddd',
          zIndex: 10,
          userSelect: 'none'
        }}
      />
    </div>
  );
}

