import React, { useState } from 'react';
import { AlertTriangle, Phone } from 'lucide-react';

export default function SymptomTriageCard({ onSubmit, onEmergency }) {
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);

  const toggleSymptom = (symptom) => {
    setSelectedSymptoms(prev => 
      prev.includes(symptom) 
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    );
  };

  const handleSubmit = () => {
    if (selectedSymptoms.length > 0) {
      onSubmit(selectedSymptoms);
    }
  };

  const handleEmergency = () => {
    onEmergency(selectedSymptoms.length > 0 ? selectedSymptoms : ["Unknown critical symptoms"]);
  };

  return (
    <div className="symptom-triage-card">
      <div className="triage-header">
        <span style={{ fontSize: '24px' }}>🚑</span>
        <h3>Tap what you're feeling</h3>
      </div>
      <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '16px' }}>Select all that apply, we'll tell you what to do next.</p>
      
      <div className="triage-options">
        <button 
          className={`triage-btn normal-triage ${selectedSymptoms.includes("Dizziness or fainting") ? "selected" : ""}`}
          onClick={() => toggleSymptom("Dizziness or fainting")}
        >
          <span style={{ fontSize: '20px' }}>❄️</span> Dizziness or fainting
        </button>
        <button 
          className={`triage-btn normal-triage ${selectedSymptoms.includes("Heavy sweating, cold clammy skin") ? "selected" : ""}`}
          onClick={() => toggleSymptom("Heavy sweating, cold clammy skin")}
        >
          <span style={{ fontSize: '20px' }}>💧</span> Heavy sweating, cold clammy skin
        </button>
        <button 
          className={`triage-btn normal-triage ${selectedSymptoms.includes("Nausea or muscle cramps") ? "selected" : ""}`}
          onClick={() => toggleSymptom("Nausea or muscle cramps")}
        >
          <span style={{ fontSize: '20px' }}>🤒</span> Nausea or muscle cramps
        </button>
        
        <button 
          className={`triage-btn danger-triage ${selectedSymptoms.includes("Hot, dry skin with no sweating") ? "selected" : ""}`}
          onClick={() => toggleSymptom("Hot, dry skin with no sweating")}
        >
          <AlertTriangle size={20} color="#fca5a5" /> Hot, dry skin with no sweating
        </button>
        <button 
          className={`triage-btn danger-triage ${selectedSymptoms.includes("Confusion or slurred speech") ? "selected" : ""}`}
          onClick={() => toggleSymptom("Confusion or slurred speech")}
        >
          <AlertTriangle size={20} color="#fca5a5" /> Confusion or slurred speech
        </button>
      </div>

      <div className="triage-emergency-alert">
        <Phone size={20} color="#fca5a5" />
        <p>Confused, unconscious, or very high fever? Call emergency services now, don't wait for this checklist.</p>
      </div>
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <button 
          className="triage-call-btn" 
          style={{ flex: 1, backgroundColor: '#3b82f6', color: 'white' }}
          onClick={handleSubmit}
          disabled={selectedSymptoms.length === 0}
        >
          Get advice
        </button>
        <button className="triage-call-btn" style={{ flex: 1 }} onClick={handleEmergency}>
          Call emergency services
        </button>
      </div>
    </div>
  );
}
