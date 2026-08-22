import React from 'react';
import { SvgTherm, SvgRoute, SvgShield, SvgActivity } from '../Icons';

export default function CitizenDashboard({ 
  currentWeather, 
  riskLevel, 
  getRiskColorClass, 
  morningWindow, 
  middayWindow, 
  eveningWindow, 
  onQuickAction, 
  onOpenCheckIn 
}) {
  return (
    <div className="zero-state-dashboard citizen-dashboard">
      {/* Hero Alert Banner */}
      <div className={`hero-alert-banner ${getRiskColorClass(riskLevel)}`}>
        <div className="alert-top">
          <span className="location-text">{currentWeather ? 'Right now near you' : 'Location required'}</span>
          <SvgTherm size={28} color={currentWeather ? (riskLevel === 'LOW' ? 'var(--risk-cool)' : 'var(--risk-extreme)') : "var(--text-secondary)"} />
        </div>
        <h2>{currentWeather ? `${currentWeather.heat_risk_level} heat — ${Math.round(currentWeather.feels_like_celsius)}°C` : 'Analyzing conditions...'}</h2>
        <p>{currentWeather ? (riskLevel === 'EXTREME' || riskLevel === 'HIGH' ? 'Avoid going outside during peak hours. Drink water.' : 'Conditions are relatively safe. Stay hydrated.') : 'Please enter your location to get safety alerts.'}</p>
      </div>
      
      {/* 2x2 Action Grid */}
      <div className="action-grid">
        <button className={`action-btn ${currentWeather ? 'btn-red' : 'btn-gray'}`} onClick={() => onQuickAction("I don't feel well. Please ask me for my symptoms to triage heat exhaustion vs heat stroke.")}>
          <SvgShield size={28} />
          <span>I don't feel well</span>
        </button>
        <button className="action-btn btn-gray" onClick={() => onQuickAction("Find a cool place nearby and give me a safe walking route to it.")}>
          <SvgRoute size={28} />
          <span>Find cool place nearby</span>
        </button>
        <button className="action-btn btn-gray" onClick={onOpenCheckIn}>
          <SvgActivity size={28} />
          <span>Check on someone</span>
        </button>
        <button className="action-btn btn-gray" onClick={() => onQuickAction("Is it safe to work outside right now?")}>
          <SvgTherm size={28} />
          <span>Safe to work outside?</span>
        </button>
      </div>

      {/* Timeline */}
      <div className="safe-windows-section">
        <h4>Today's safe windows</h4>
        <div className="safe-windows-row">
          <div className={`time-block ${morningWindow.class}`}>
            <span className="time">{morningWindow.title} {currentWeather ? `(${morningWindow.time})` : ''}</span>
            <span className="status">{morningWindow.status}</span>
          </div>
          <div className={`time-block ${middayWindow.class}`}>
            <span className="time">{middayWindow.title} {currentWeather ? `(${middayWindow.time})` : ''}</span>
            <span className="status">{middayWindow.status}</span>
          </div>
          <div className={`time-block ${eveningWindow.class}`}>
            <span className="time">{eveningWindow.title} {currentWeather ? `(${eveningWindow.time})` : ''}</span>
            <span className="status">{eveningWindow.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
