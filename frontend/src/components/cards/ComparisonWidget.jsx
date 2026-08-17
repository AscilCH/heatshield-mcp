import React from 'react';

const ComparisonWidget = ({ data, onClose }) => {
  if (!data || !data.data || !Array.isArray(data.data) || data.data.length === 0) return null;

  const rows = data.data;
  const keys = Object.keys(rows[0]).filter(k => k !== 'location');

  const formatHeader = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="forecast-card comparison-widget" style={{ padding: '20px', background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px', backdropFilter: 'blur(12px)', color: 'white', overflowX: 'auto', marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#38bdf8' }}>Comparative Matrix</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}>✕</button>
      </div>
      
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <th style={{ padding: '8px', color: '#94a3b8', whiteSpace: 'nowrap' }}>Location</th>
            {keys.map(k => (
              <th key={k} style={{ padding: '8px', color: '#94a3b8', whiteSpace: 'nowrap' }}>{formatHeader(k)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <td style={{ padding: '8px', fontWeight: 'bold' }}>{row.location}</td>
              {keys.map(k => {
                let val = String(row[k]);
                // Highlight extreme risk
                let color = 'inherit';
                if (val.toUpperCase().includes('EXTREME') || val.toUpperCase().includes('ACTIVE')) color = '#ef4444';
                return (
                  <td key={k} style={{ padding: '8px', color: color }}>{val}</td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ComparisonWidget;
