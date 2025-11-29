/**
 * Collapsible Panel component - can be collapsed/expanded.
 */

import { useState, ReactNode } from 'react';

interface CollapsiblePanelProps {
  title: string;
  children: ReactNode;
  defaultExpanded?: boolean;
  icon?: string;
  headerStyle?: React.CSSProperties;
}

export function CollapsiblePanel({
  title,
  children,
  defaultExpanded = true,
  icon,
  headerStyle
}: CollapsiblePanelProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', borderBottom: '1px solid #ddd' }}>
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          padding: '0.5rem',
          backgroundColor: '#f0f0f0',
          borderBottom: '1px solid #ddd',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          userSelect: 'none',
          fontWeight: 'bold',
          fontSize: '0.9em',
          ...headerStyle
        }}
      >
        <span>{isExpanded ? '▼' : '▶'}</span>
        {icon && <span>{icon}</span>}
        <span>{title}</span>
      </div>
      {isExpanded && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {children}
        </div>
      )}
    </div>
  );
}

