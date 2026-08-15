import React from 'react';

export default function AlertBanner({ alert, onClose }) {
  if (!alert) return null;
  
  return (
    <div className={`global-alert-banner ${alert.severity?.toLowerCase()}`}>
      <div className="alert-content">
        <span className="alert-icon">⚠️</span>
        <div className="alert-text">
          <strong>EMERGENCY PUSH NOTIFICATION</strong>
          <p>{alert.message}</p>
        </div>
      </div>
      <button className="close-btn" onClick={onClose}>✕</button>
    </div>
  );
}
