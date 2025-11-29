/**
 * Plane Selection Dialog component.
 * Allows user to select a plane or face for creating a new sketch.
 */

interface PlaneSelectionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (plane: string) => void;
  availablePlanes?: string[];
  availableFaces?: Array<{ id: string; name: string }>;
}

export function PlaneSelectionDialog({
  isOpen,
  onClose,
  onSelect,
  availablePlanes = ['front_plane', 'right_plane', 'top_plane'],
  availableFaces = []
}: PlaneSelectionDialogProps) {
  if (!isOpen) return null;

  const standardPlanes = [
    { value: 'front_plane', label: 'Front Plane (XY)', icon: '⬜' },
    { value: 'right_plane', label: 'Right Plane (YZ)', icon: '⬜' },
    { value: 'top_plane', label: 'Top Plane (XZ)', icon: '⬜' }
  ];

  const handleSelect = (plane: string) => {
    onSelect(plane);
    onClose();
  };

  return (
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
        zIndex: 1000
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '8px',
          minWidth: '400px',
          maxWidth: '600px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0, marginBottom: '1rem' }}>Select Sketch Plane</h2>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '0.9em', color: '#666', marginBottom: '0.5rem' }}>Standard Planes</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {standardPlanes.map((plane) => (
              <button
                key={plane.value}
                onClick={() => handleSelect(plane.value)}
                style={{
                  padding: '0.75rem',
                  textAlign: 'left',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f9f9f9',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e9e9e9';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f9f9f9';
                }}
              >
                <span style={{ fontSize: '1.2em' }}>{plane.icon}</span>
                <span>{plane.label}</span>
              </button>
            ))}
          </div>
        </div>

        {availableFaces.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.9em', color: '#666', marginBottom: '0.5rem' }}>Part Faces</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {availableFaces.map((face) => (
                <button
                  key={face.id}
                  onClick={() => handleSelect(`face:${face.id}`)}
                  style={{
                    padding: '0.75rem',
                    textAlign: 'left',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    backgroundColor: '#f9f9f9',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#e9e9e9';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#f9f9f9';
                  }}
                >
                  {face.name}
                </button>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: '#f0f0f0',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

