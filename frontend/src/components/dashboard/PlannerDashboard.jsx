import React from 'react';

export default function PlannerDashboard() {
  return (
    <div className="zero-state-dashboard planner-dashboard" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>City Operations</h2>
        <button style={{ backgroundColor: '#1e293b', color: '#94a3b8', border: '1px solid #334155', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}>
          Export Report ⬇
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
        <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#94a3b8' }}>UHI Severity (Avg)</p>
          <h3 style={{ margin: 0, fontSize: '24px', color: '#fca5a5' }}>+4.2°C</h3>
        </div>
        <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#94a3b8' }}>Vulnerable Pop at Risk</p>
          <h3 style={{ margin: 0, fontSize: '24px', color: '#f8fafc' }}>12,400</h3>
        </div>
      </div>

      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#f8fafc' }}>High Risk Neighborhoods</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left', color: '#cbd5e1' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
            <th style={{ padding: '8px 0' }}>Area</th>
            <th style={{ padding: '8px 0' }}>UHI</th>
            <th style={{ padding: '8px 0' }}>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: '1px solid #334155' }}>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Südstadt</td>
            <td style={{ padding: '12px 0', color: '#fca5a5' }}>+5.1°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#fff' }}>Critical</span></td>
          </tr>
          <tr style={{ borderBottom: '1px solid #334155' }}>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Innenstadt-Ost</td>
            <td style={{ padding: '12px 0', color: '#f59e0b' }}>+3.8°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#f59e0b', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#000' }}>Warning</span></td>
          </tr>
          <tr>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Oststadt</td>
            <td style={{ padding: '12px 0', color: '#4ade80' }}>+1.2°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#22c55e', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#fff' }}>Stable</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
