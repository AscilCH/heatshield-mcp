import React from 'react';
import { ArrowLeft, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function CheckInView({ contacts, onBack }) {
  return (
    <div className="check-in-view">
      <div className="check-in-header">
        <button className="back-btn" onClick={onBack}><ArrowLeft size={20} /></button>
        <h2>Check on someone</h2>
      </div>
      
      <div className="check-in-content">
        <p className="section-label">People you're watching over</p>
        
        {contacts.map(c => (
          <div key={c.id} className={`person-card ${c.status === 'alert' ? 'alert-state' : 'ok-state'}`}>
            <div className={`person-avatar ${c.status === 'alert' ? 'bg-red' : 'bg-green'}`}>{c.initials}</div>
            <div className="person-info">
              <h3>{c.name}</h3>
              <p>{c.last_update}</p>
            </div>
            {c.status === 'alert' ? (
              <AlertTriangle color="#fca5a5" size={24} />
            ) : (
              <CheckCircle2 color="#4ade80" size={24} />
            )}
          </div>
        ))}

        <div className="how-it-works" style={{ marginTop: '30px' }}>
          <p className="section-label">How check-ins work</p>
          <ol>
            <li><span>1</span> We text them at set times on hot days</li>
            <li><span>2</span> If they don't reply in 2 hours, you're notified</li>
            <li><span>3</span> Still no reply → we can alert a neighbor or local service</li>
          </ol>
        </div>

        <button className="add-person-btn">
          + Add someone
        </button>
      </div>
    </div>
  );
}
