import React, { useState, useEffect } from 'react';
import { Globe, MapPin, Compass, Shield, ArrowRight } from 'lucide-react';

export default function OnboardingModal({ onComplete, setUserLocation }) {
  const [isOpen, setIsOpen] = useState(true);
  const [language, setLanguage] = useState('English');
  const [step, setStep] = useState(1);
  const [isDetecting, setIsDetecting] = useState(false);

  useEffect(() => {
    const hasOnboarded = localStorage.getItem('heatshield_onboarded');
    if (hasOnboarded === 'true') {
      setIsOpen(false);
      if (onComplete) onComplete();
    }
  }, [onComplete]);

  const handleFinish = () => {
    localStorage.setItem('heatshield_onboarded', 'true');
    setIsOpen(false);
    if (onComplete) onComplete();
  };

  const requestLocation = () => {
    setIsDetecting(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          if (setUserLocation) setUserLocation({ lat, lng: lon });
          setIsDetecting(false);
          setStep(3);
        },
        (error) => {
          console.error("Location error:", error);
          setIsDetecting(false);
          alert("Location access denied or unavailable. You can set it manually later in the chat.");
          setStep(3);
        }
      );
    } else {
      setIsDetecting(false);
      alert("Geolocation is not supported by your browser.");
      setStep(3);
    }
  };

  if (!isOpen) return null;

  const overlayStyle = {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    backdropFilter: 'blur(8px)',
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px'
  };

  const modalStyle = {
    backgroundColor: '#1C2025',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    width: '100%',
    maxWidth: '500px',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: 'sans-serif'
  };

  const headerStyle = {
    background: 'linear-gradient(90deg, rgba(249,115,22,0.1) 0%, rgba(220,38,38,0.1) 100%)',
    padding: '24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  };

  const iconBoxStyle = {
    padding: '8px',
    background: 'linear-gradient(135deg, #f97316 0%, #dc2626 100%)',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  const contentStyle = {
    padding: '24px'
  };

  const titleStyle = {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: '8px'
  };

  const descStyle = {
    fontSize: '0.875rem',
    color: '#94a3b8',
    marginBottom: '16px'
  };

  const btnGridStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px'
  };

  const langBtnStyle = {
    padding: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    backgroundColor: 'transparent',
    color: '#cbd5e1',
    cursor: 'pointer',
    textAlign: 'left',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };

  const primaryBtnStyle = {
    width: '100%',
    padding: '12px 16px',
    backgroundColor: '#ea580c',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontWeight: '500',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  };

  const secondaryBtnStyle = {
    width: '100%',
    padding: '8px 16px',
    backgroundColor: 'transparent',
    color: '#cbd5e1',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    fontWeight: '500',
    cursor: 'pointer'
  };

  const listItemStyle = {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    marginBottom: '12px'
  };

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        
        {/* Header */}
        <div style={headerStyle}>
          <div style={iconBoxStyle}>
            <Shield size={24} color="white" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#f8fafc' }}>Welcome to HeatShield</h2>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#94a3b8' }}>Autonomous Urban Heat AI Agent</p>
          </div>
        </div>

        {/* Content Body */}
        <div style={contentStyle}>
          
          {step === 1 && (
            <div>
              <h3 style={titleStyle}>1. Choose your language</h3>
              <p style={descStyle}>HeatShield operates natively across multiple languages.</p>
              
              <div style={btnGridStyle}>
                {['English', 'Français', 'Deutsch', 'العربية'].map(lang => (
                  <button
                    key={lang}
                    onClick={() => { setLanguage(lang); setStep(2); }}
                    style={langBtnStyle}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(234, 88, 12, 0.1)'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    {lang} <ArrowRight size={16} />
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <h3 style={titleStyle}>2. Set your location</h3>
              <p style={descStyle}>To provide accurate spatial risk assessments, HeatShield needs your location.</p>
              
              <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <button onClick={requestLocation} disabled={isDetecting} style={primaryBtnStyle}>
                    <MapPin size={18} />
                    {isDetecting ? "Detecting GPS..." : "Use Current GPS Location"}
                  </button>
                  <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#64748b' }}>OR</div>
                  <button onClick={() => setStep(3)} style={secondaryBtnStyle}>
                    I'll type my city in the chat
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h3 style={titleStyle}>3. What you can do</h3>
              <p style={descStyle}>You are talking to an autonomous AI agent. Try asking it to:</p>
              
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={listItemStyle}>
                  <Globe size={20} color="#60a5fa" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#e2e8f0' }}>Track Urban Heat</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8' }}>"Map the urban heat island effect here."</span>
                  </div>
                </div>
                <div style={listItemStyle}>
                  <Compass size={20} color="#34d399" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#e2e8f0' }}>Find Safe Routes</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8' }}>"Find nearby cooling spots and draw a walking route."</span>
                  </div>
                </div>
                <div style={listItemStyle}>
                  <Shield size={20} color="#fb923c" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#e2e8f0' }}>Calculate WBGT</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8' }}>"Calculate the WBGT for heavy work."</span>
                  </div>
                </div>
              </div>
              
              <button 
                onClick={handleFinish}
                style={{ ...primaryBtnStyle, marginTop: '16px', background: 'linear-gradient(90deg, #f97316 0%, #dc2626 100%)', padding: '14px' }}
              >
                Enter HeatShield
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
