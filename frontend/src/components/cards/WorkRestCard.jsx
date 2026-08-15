import React from 'react';
import { Droplets, Info } from 'lucide-react';

export default function WorkRestCard({ workRestGuidance }) {
  if (!workRestGuidance) return null;

  return (
    <div className="msg-ai">
      <div className="message-content" style={{ background: 'transparent', padding: 0, border: 'none' }}>
        <div className="work-rest-card" style={{ 
          background: workRestGuidance.halt_operations ? 'rgba(255, 90, 60, 0.15)' : 'var(--bg-panel-raised)', 
          padding: '20px', 
          borderRadius: '12px', 
          border: workRestGuidance.halt_operations ? '1px solid var(--risk-extreme)' : '1px solid var(--line)', 
          marginTop: '10px' 
        }}>
          <div className="wrc-header" style={{ marginBottom: '15px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
              <h3 style={{ margin: '0', fontSize: '18px', lineHeight: '1.2' }}>
                Workload Safety{workRestGuidance.halt_operations ? ': Unsafe' : ''}
              </h3>
              <span style={{ 
                display: 'inline-block', whiteSpace: 'nowrap', flexShrink: 0,
                padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold',
                background: workRestGuidance.halt_operations ? 'var(--text-primary)' : (workRestGuidance.rest_minutes === 0 ? 'var(--risk-cool)' : 'var(--risk-caution)'),
                color: 'var(--bg-panel)'
              }}>
                {workRestGuidance.halt_operations ? 'HALT OPERATIONS' : (workRestGuidance.rest_minutes === 0 ? 'CONTINUOUS WORK' : 'SCHEDULE REQUIRED')}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '12px', gap: '8px' }}>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>Calculated via Wet Bulb Globe Temp (WBGT)</p>
              <p style={{ margin: 0, fontSize: '16px', fontWeight: 'bold', whiteSpace: 'nowrap', flexShrink: 0 }}>
                {typeof workRestGuidance.wbgt_celsius === 'number' ? workRestGuidance.wbgt_celsius.toFixed(1) : workRestGuidance.wbgt_celsius}°C WBGT
              </p>
            </div>
          </div>

          <div className="wrc-progress-container" style={{ display: 'flex', height: '30px', borderRadius: '8px', overflow: 'hidden', marginBottom: '15px' }}>
            {workRestGuidance.halt_operations ? (
               <div style={{ flex: 1, background: 'var(--risk-extreme)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>STOP WORK IMMEDIATELY</div>
            ) : (
               <>
                 <div className="progress-stripes" style={{ flex: workRestGuidance.work_minutes, minWidth: 0, background: 'var(--risk-cool)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 'bold', fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                   WORK {workRestGuidance.work_minutes}M
                 </div>
                 {workRestGuidance.rest_minutes > 0 && (
                   <div style={{ flex: workRestGuidance.rest_minutes, minWidth: 0, background: 'var(--risk-extreme)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                     REST {workRestGuidance.rest_minutes}M
                   </div>
                 )}
               </>
            )}
          </div>

          <div className="wrc-footer" style={{ borderTop: '1px solid var(--line)', paddingTop: '15px', marginTop: '5px', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Droplets size={16} color="var(--risk-natural)" />
              <strong>Hydration:</strong> {workRestGuidance.hydration_rule}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '12px' }}>
              <Info size={16} /> Based on official NIOSH thresholds for unacclimatized workers.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
