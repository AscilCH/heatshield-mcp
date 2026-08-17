import React from 'react';
import { X, MapPin } from 'lucide-react';

const ComparisonWidget = ({ data, onClose }) => {
  if (!data || !data.data || !Array.isArray(data.data) || data.data.length === 0) return null;

  const rows = data.data;
  const keys = Object.keys(rows[0]).filter(k => k !== 'location');

  const formatHeader = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getBadgeStyle = (val) => {
    const v = String(val).toUpperCase();
    if (v.includes('EXTREME')) return { bg: 'rgba(239, 68, 68, 0.15)', text: '#fca5a5', border: 'rgba(239, 68, 68, 0.3)' };
    if (v.includes('HIGH')) return { bg: 'rgba(249, 115, 22, 0.15)', text: '#fdba74', border: 'rgba(249, 115, 22, 0.3)' };
    if (v.includes('MODERATE')) return { bg: 'rgba(234, 179, 8, 0.15)', text: '#fde047', border: 'rgba(234, 179, 8, 0.3)' };
    if (v.includes('LOW')) return { bg: 'rgba(34, 197, 94, 0.15)', text: '#86efac', border: 'rgba(34, 197, 94, 0.3)' };
    if (v.includes('ACTIVE')) return { bg: 'rgba(239, 68, 68, 0.2)', text: '#fca5a5', border: 'rgba(239, 68, 68, 0.4)' };
    return null;
  };

  const formatValue = (key, val) => {
    const badgeStyle = getBadgeStyle(val);
    if (badgeStyle) {
      return (
        <span style={{
          backgroundColor: badgeStyle.bg,
          color: badgeStyle.text,
          border: `1px solid ${badgeStyle.border}`,
          padding: '4px 10px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: '600',
          letterSpacing: '0.05em'
        }}>
          {String(val).toUpperCase()}
        </span>
      );
    }
    
    // Add a degree symbol if it's temperature
    if (key.toLowerCase().includes('temperature') && !String(val).includes('°')) {
      return <span style={{ fontWeight: '500', color: '#e2e8f0' }}>{val}°</span>;
    }
    
    return <span style={{ color: '#cbd5e1' }}>{val}</span>;
  };

  return (
    <div style={{
      padding: '24px',
      background: 'rgba(15, 23, 42, 0.85)',
      border: '1px solid rgba(148, 163, 184, 0.15)',
      borderRadius: '20px',
      backdropFilter: 'blur(20px)',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.05) inset',
      color: 'white',
      marginBottom: '24px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Custom scrollbar styles */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255,255,255,0.02);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.15);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255,255,255,0.25);
        }
        .comparison-row {
          transition: background-color 0.2s ease;
        }
        .comparison-row:hover {
          background-color: rgba(255,255,255,0.03);
        }
      `}</style>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(56, 189, 248, 0.15)', padding: '8px', borderRadius: '10px', color: '#38bdf8' }}>
            <MapPin size={18} />
          </div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#f8fafc', letterSpacing: '-0.01em' }}>Comparative Matrix</h3>
        </div>
        <button onClick={onClose} style={{ 
          background: 'rgba(255,255,255,0.05)', 
          border: '1px solid rgba(255,255,255,0.1)', 
          color: '#94a3b8', 
          cursor: 'pointer', 
          width: '32px', 
          height: '32px', 
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#fff'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = '#94a3b8'; }}
        >
          <X size={16} />
        </button>
      </div>
      
      <div className="custom-scrollbar" style={{ overflowX: 'auto', paddingBottom: '8px', margin: '0 -24px', padding: '0 24px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left', minWidth: '600px' }}>
          <thead>
            <tr>
              <th style={{ padding: '16px', color: '#64748b', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>Location</th>
              {keys.map(k => (
                <th key={k} style={{ padding: '16px', color: '#64748b', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>{formatHeader(k)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="comparison-row" style={{ borderBottom: i === rows.length - 1 ? 'none' : '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '16px', fontWeight: '500', color: '#f8fafc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#38bdf8' }}></div>
                    {row.location}
                  </div>
                </td>
                {keys.map(k => (
                  <td key={k} style={{ padding: '16px' }}>
                    {formatValue(k, row[k])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComparisonWidget;
