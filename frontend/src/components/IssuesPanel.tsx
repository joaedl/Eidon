/**
 * Issues Panel component.
 * Displays validation issues grouped by severity.
 */

import type { ValidationIssue } from '../types/ir';

interface IssuesPanelProps {
  issues: ValidationIssue[];
  onIssueClick?: (issue: ValidationIssue) => void;
}

export function IssuesPanel({ issues, onIssueClick }: IssuesPanelProps) {
  // Group issues by severity
  const errors = issues.filter(i => i.severity === 'error');
  const warnings = issues.filter(i => i.severity === 'warning');
  const infos = issues.filter(i => i.severity === 'info');

  const getSeverityColor = (severity: ValidationIssue['severity']) => {
    switch (severity) {
      case 'error': return '#d32f2f';
      case 'warning': return '#ed6c02';
      case 'info': return '#1976d2';
      default: return '#666';
    }
  };

  const getSeverityIcon = (severity: ValidationIssue['severity']) => {
    switch (severity) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '•';
    }
  };

  const renderIssue = (issue: ValidationIssue) => (
    <div
      key={`${issue.code}-${issue.message}`}
      onClick={() => onIssueClick?.(issue)}
      style={{
        padding: '0.5rem',
        marginBottom: '0.5rem',
        borderLeft: `3px solid ${getSeverityColor(issue.severity)}`,
        backgroundColor: '#f5f5f5',
        borderRadius: '4px',
        cursor: onIssueClick ? 'pointer' : 'default',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>{getSeverityIcon(issue.severity)}</span>
        <span style={{ fontWeight: 'bold', color: getSeverityColor(issue.severity) }}>
          [{issue.severity.toUpperCase()}]
        </span>
        <span style={{ fontSize: '0.85em', color: '#666' }}>{issue.code}</span>
      </div>
      <div style={{ marginTop: '0.25rem', fontSize: '0.9em' }}>{issue.message}</div>
      {(issue.related_params.length > 0 || issue.related_features.length > 0 || issue.related_chains.length > 0) && (
        <div style={{ marginTop: '0.25rem', fontSize: '0.8em', color: '#666' }}>
          {issue.related_params.length > 0 && `Params: ${issue.related_params.join(', ')}`}
          {issue.related_features.length > 0 && ` Features: ${issue.related_features.join(', ')}`}
          {issue.related_chains.length > 0 && ` Chains: ${issue.related_chains.join(', ')}`}
        </div>
      )}
    </div>
  );

  return (
    <div style={{ padding: '1rem', height: '100%', overflow: 'auto' }}>
      <h2 style={{ marginTop: 0 }}>Validation Issues</h2>
      
      {issues.length === 0 ? (
        <div style={{ color: '#4caf50', padding: '1rem', textAlign: 'center' }}>
          ✓ No issues found
        </div>
      ) : (
        <>
          {errors.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ color: '#d32f2f', marginBottom: '0.5rem' }}>Errors ({errors.length})</h3>
              {errors.map(renderIssue)}
            </div>
          )}
          
          {warnings.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ color: '#ed6c02', marginBottom: '0.5rem' }}>Warnings ({warnings.length})</h3>
              {warnings.map(renderIssue)}
            </div>
          )}
          
          {infos.length > 0 && (
            <div>
              <h3 style={{ color: '#1976d2', marginBottom: '0.5rem' }}>Info ({infos.length})</h3>
              {infos.map(renderIssue)}
            </div>
          )}
        </>
      )}
    </div>
  );
}

