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
      if (onComplete) onComplete(localStorage.getItem('heatshield_lang') || 'English');
    }
  }, [onComplete]);

  const handleFinish = () => {
    localStorage.setItem('heatshield_onboarded', 'true');
    localStorage.setItem('heatshield_lang', language);
    setIsOpen(false);
    if (onComplete) onComplete(language);
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
    maxWidth: '650px',
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
    gap: '12px',
    direction: language === 'العربية' ? 'rtl' : 'ltr'
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
    padding: '32px',
    direction: language === 'العربية' ? 'rtl' : 'ltr',
    textAlign: language === 'العربية' ? 'right' : 'left'
  };

  const titleStyle = {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#e2e8f0',
    marginBottom: '8px'
  };

  const descStyle = {
    fontSize: '0.95rem',
    color: '#94a3b8',
    marginBottom: '24px'
  };

  const btnGridStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px'
  };

  const langBtnStyle = {
    padding: '16px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    backgroundColor: 'transparent',
    color: '#cbd5e1',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '1rem'
  };

  const primaryBtnStyle = {
    width: '100%',
    padding: '14px 16px',
    backgroundColor: '#ea580c',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontWeight: '500',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontSize: '1rem'
  };

  const secondaryBtnStyle = {
    width: '100%',
    padding: '12px 16px',
    backgroundColor: 'transparent',
    color: '#cbd5e1',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    fontWeight: '500',
    cursor: 'pointer',
    fontSize: '1rem'
  };

  const listItemStyle = {
    display: 'flex',
    gap: '16px',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    padding: '16px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    marginBottom: '12px'
  };

  // Translations
  const t = {
    'English': {
      welcome: "Welcome to HeatShield",
      subWelcome: "Autonomous Urban Heat AI Agent",
      step1Title: "1. Choose your language",
      step1Desc: "HeatShield operates natively across multiple languages.",
      step2Title: "2. Set your location",
      step2Desc: "To provide accurate spatial risk assessments, HeatShield needs your location.",
      detecting: "Detecting GPS...",
      useGps: "Use Current GPS Location",
      or: "OR",
      typeCity: "I'll type my city in the chat",
      step3Title: "3. What you can do",
      step3Desc: "You are talking to an autonomous AI agent. Try asking it to:",
      feature1Title: "Track Urban Heat",
      feature1Desc: '"Map the urban heat island effect here."',
      feature2Title: "Find Safe Routes",
      feature2Desc: '"Find nearby cooling spots and draw a walking route."',
      feature3Title: "Calculate WBGT",
      feature3Desc: '"Calculate the WBGT for heavy work."',
      enter: "Enter HeatShield"
    },
    'Français': {
      welcome: "Bienvenue sur HeatShield",
      subWelcome: "Agent IA Autonome de Chaleur Urbaine",
      step2Title: "2. Définissez votre emplacement",
      step2Desc: "Pour fournir des évaluations de risques précises, HeatShield a besoin de votre position.",
      detecting: "Détection GPS...",
      useGps: "Utiliser la position GPS",
      or: "OU",
      typeCity: "Je taperai ma ville dans le chat",
      step3Title: "3. Ce que vous pouvez faire",
      step3Desc: "Vous parlez à un agent IA autonome. Essayez de lui demander :",
      feature1Title: "Suivre la chaleur urbaine",
      feature1Desc: '"Cartographier l\'îlot de chaleur urbain ici."',
      feature2Title: "Trouver des itinéraires sûrs",
      feature2Desc: '"Trouver des lieux frais et tracer un itinéraire."',
      feature3Title: "Calculer le WBGT",
      feature3Desc: '"Calculer le WBGT pour un travail intense."',
      enter: "Entrer dans HeatShield"
    },
    'العربية': {
      welcome: "مرحباً بك في HeatShield",
      subWelcome: "مساعد الذكاء الاصطناعي للحرارة الحضرية",
      step2Title: "2. حدد موقعك",
      step2Desc: "لتقديم تقييمات دقيقة للمخاطر، يحتاج HeatShield إلى معرفة موقعك.",
      detecting: "جاري تحديد الموقع...",
      useGps: "استخدام موقع GPS الحالي",
      or: "أو",
      typeCity: "سأكتب مدينتي في الدردشة",
      step3Title: "3. ماذا يمكنك أن تفعل",
      step3Desc: "أنت تتحدث إلى ذكاء اصطناعي مستقل. جرب أن تطلب منه:",
      feature1Title: "تتبع الحرارة الحضرية",
      feature1Desc: '"ارسم خريطة الجزر الحرارية الحضرية هنا."',
      feature2Title: "إيجاد طرق آمنة",
      feature2Desc: '"ابحث عن أماكن باردة قريبة وارسم طريقاً للمشي."',
      feature3Title: "حساب مؤشر WBGT",
      feature3Desc: '"احسب مؤشر الإجهاد الحراري للعمل الشاق."',
      enter: "دخول HeatShield"
    },
    'Deutsch': {
      welcome: "Willkommen bei HeatShield",
      subWelcome: "Autonomer KI-Agent für städtische Hitze",
      step2Title: "2. Standort festlegen",
      step2Desc: "Für genaue Risikobewertungen benötigt HeatShield Ihren Standort.",
      detecting: "GPS wird ermittelt...",
      useGps: "Aktuellen GPS-Standort verwenden",
      or: "ODER",
      typeCity: "Ich tippe meine Stadt in den Chat",
      step3Title: "3. Was Sie tun können",
      step3Desc: "Sie sprechen mit einem autonomen KI-Agenten. Fragen Sie ihn:",
      feature1Title: "Städtische Hitze verfolgen",
      feature1Desc: '"Kartiere den städtischen Wärmeinseleffekt hier."',
      feature2Title: "Sichere Routen finden",
      feature2Desc: '"Finde kühle Orte und zeichne eine Route."',
      feature3Title: "WBGT berechnen",
      feature3Desc: '"Berechne den WBGT für schwere Arbeit."',
      enter: "HeatShield betreten"
    }
  };

  const currentT = t[language] || t['English'];

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        
        {/* Header */}
        <div style={headerStyle}>
          <div style={iconBoxStyle}>
            <Shield size={28} color="white" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#f8fafc' }}>{currentT.welcome || t['English'].welcome}</h2>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#94a3b8' }}>{currentT.subWelcome || t['English'].subWelcome}</p>
          </div>
        </div>

        {/* Content Body */}
        <div style={contentStyle}>
          
          {step === 1 && (
            <div>
              <h3 style={titleStyle}>{t['English'].step1Title}</h3>
              <p style={descStyle}>{t['English'].step1Desc}</p>
              
              <div style={btnGridStyle}>
                {['English', 'Français', 'Deutsch', 'العربية'].map(lang => (
                  <button
                    key={lang}
                    onClick={() => { setLanguage(lang); setStep(2); }}
                    style={langBtnStyle}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(234, 88, 12, 0.1)'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    {lang} <ArrowRight size={18} />
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <h3 style={titleStyle}>{currentT.step2Title}</h3>
              <p style={descStyle}>{currentT.step2Desc}</p>
              
              <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <button onClick={requestLocation} disabled={isDetecting} style={primaryBtnStyle}>
                    <MapPin size={20} />
                    {isDetecting ? currentT.detecting : currentT.useGps}
                  </button>
                  <div style={{ textAlign: 'center', fontSize: '0.85rem', color: '#64748b' }}>{currentT.or}</div>
                  <button onClick={() => setStep(3)} style={secondaryBtnStyle}>
                    {currentT.typeCity}
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h3 style={titleStyle}>{currentT.step3Title}</h3>
              <p style={descStyle}>{currentT.step3Desc}</p>
              
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={listItemStyle}>
                  <Globe size={24} color="#60a5fa" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '1rem', fontWeight: '500', color: '#e2e8f0' }}>{currentT.feature1Title}</span>
                    <span style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>{currentT.feature1Desc}</span>
                  </div>
                </div>
                <div style={listItemStyle}>
                  <Compass size={24} color="#34d399" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '1rem', fontWeight: '500', color: '#e2e8f0' }}>{currentT.feature2Title}</span>
                    <span style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>{currentT.feature2Desc}</span>
                  </div>
                </div>
                <div style={listItemStyle}>
                  <Shield size={24} color="#fb923c" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <span style={{ display: 'block', fontSize: '1rem', fontWeight: '500', color: '#e2e8f0' }}>{currentT.feature3Title}</span>
                    <span style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>{currentT.feature3Desc}</span>
                  </div>
                </div>
              </div>
              
              <button 
                onClick={handleFinish}
                style={{ ...primaryBtnStyle, marginTop: '24px', background: 'linear-gradient(90deg, #f97316 0%, #dc2626 100%)', padding: '16px', fontSize: '1.1rem' }}
              >
                {currentT.enter}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
