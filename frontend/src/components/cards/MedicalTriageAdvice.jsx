import React from 'react';

export default function MedicalTriageAdvice({ medicalTriageAdvice, onEmergencyCall }) {
  if (!medicalTriageAdvice) return null;

  return (
    <div className="msg-emergency">
      <div className="emergency-head">
        <span>🚨</span> {medicalTriageAdvice.title}
      </div>
      <div style={{ padding: '4px 0', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.5' }}>
        {medicalTriageAdvice.steps.split('\n').filter(l => l.trim().length > 0).map((line, i) => (
          <p key={i} style={{ marginBottom: '8px' }}>
            {line.startsWith('-') || line.startsWith('•') ? <span style={{ marginLeft: '10px' }}>{line}</span> : <strong>{line}</strong>}
          </p>
        ))}
      </div>
      {medicalTriageAdvice.requires_emergency && (
        <button className="emergency-call-btn" onClick={onEmergencyCall}>
          📞 CALL EMERGENCY SERVICES
        </button>
      )}
    </div>
  );
}
