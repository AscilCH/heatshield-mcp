import React, { useState, useEffect } from 'react';
import { ArrowRight, ArrowLeft, Check, Info } from 'lucide-react';
import { SvgShield, SvgPin, SvgRoute, SvgTherm } from '../Icons';
import WorldFlag from 'react-world-flags';
const Flag = WorldFlag.default || WorldFlag;

export default function OnboardingModal({ onComplete, setUserLocation }) {
  const [isOpen, setIsOpen] = useState(true);
  const [language, setLanguage] = useState('English');
  const [step, setStep] = useState(1);
  const [isDetecting, setIsDetecting] = useState(false);
  const [locSetText, setLocSetText] = useState("");
  const [activeCard, setActiveCard] = useState(null);

  useEffect(() => {
    const hasOnboarded = localStorage.getItem('heatshield_onboarded_v2');
    if (hasOnboarded === 'true') {
      setIsOpen(false);
      if (onComplete) onComplete(localStorage.getItem('heatshield_lang') || 'English');
    }
  }, []); // Empty dependency array to run only once on mount

  const handleFinish = () => {
    localStorage.setItem('heatshield_onboarded_v2', 'true');
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
          setLocSetText(t[language]?.locSet || "Location set via GPS");
          setTimeout(() => setStep(3), 1200); // Auto-advance after showing success
        },
        (error) => {
          console.error("Location error:", error);
          setIsDetecting(false);
          alert("Location access denied. You can set it manually in the chat.");
          setStep(3);
        },
        { timeout: 10000 }
      );
    } else {
      setIsDetecting(false);
      alert("Geolocation is not supported by your browser.");
      setStep(3);
    }
  };

  if (!isOpen) return null;

  // Translations
  const t = {
    'English': {
      welcome: "Welcome to HeatShield",
      subWelcome: "Set up takes under a minute",
      step1Eyebrow: "LANGUAGE",
      step1Title: "Choose your language",
      step1Desc: "HeatShield operates natively across multiple languages.",
      step2Eyebrow: "LOCATION",
      step2Title: "Where should I watch?",
      step2Desc: "HeatShield maps heat risk and cooling spots for your area. Your location isn't stored, and you can change it anytime in settings.",
      detecting: "Detecting...",
      useGps: "Use current location",
      typeCity: "I'll type my city in the chat",
      skip: "Skip for now",
      locSet: "Location set via GPS",
      continue: "Continue",
      back: "Back",
      step3Eyebrow: "CAPABILITIES",
      step3Title: "Here's what I can do",
      step3Desc: "Tap any example to see a live preview.",
      feature1Title: "Forecast Weather",
      feature1Desc: '"Will there be a heatwave this weekend?"',
      feature1Prev: "Preview → pulling 7-day Open-Meteo ensemble forecasts for heatwave risk.",
      feature2Title: "Find Cooling Spots",
      feature2Desc: '"Where is the nearest air-conditioned library?"',
      feature2Prev: "Preview → locating nearest cooling centers overlaying satellite land-surface temp data.",
      feature3Title: "Emergency Protocols",
      feature3Desc: '"My friend feels dizzy and hot, what should I do?"',
      feature3Prev: "Preview → retrieving verified local emergency contacts and medical first-aid steps.",
      disclaimer: "Estimates are for guidance only. Always follow official heat warnings from local authorities.",
      enter: "Start using HeatShield",
      skipDash: "Skip to dashboard"
    },
    'Français': {
      welcome: "Bienvenue sur HeatShield",
      subWelcome: "Configuration en moins d'une minute",
      step1Eyebrow: "LANGUE",
      step1Title: "Choisissez votre langue",
      step1Desc: "HeatShield fonctionne nativement dans plusieurs langues.",
      step2Eyebrow: "LOCALISATION",
      step2Title: "Où dois-je surveiller ?",
      step2Desc: "HeatShield cartographie les risques de chaleur et les lieux frais de votre région. Votre position n'est pas stockée.",
      detecting: "Détection...",
      useGps: "Utiliser ma position actuelle",
      typeCity: "Je taperai ma ville dans le chat",
      skip: "Ignorer pour le moment",
      locSet: "Position définie via GPS",
      continue: "Continuer",
      back: "Retour",
      step3Eyebrow: "CAPACITÉS",
      step3Title: "Voici ce que je peux faire",
      step3Desc: "Appuyez sur un exemple pour voir un aperçu en direct.",
      feature1Title: "Prévisions Météo",
      feature1Desc: '"Y aura-t-il une canicule ce week-end ?"',
      feature1Prev: "Aperçu → récupération des prévisions sur 7 jours pour le risque de canicule.",
      feature2Title: "Trouver des Lieux Frais",
      feature2Desc: '"Où se trouve la bibliothèque climatisée la plus proche ?"',
      feature2Prev: "Aperçu → localisation des centres de rafraîchissement sur la carte de température de surface.",
      feature3Title: "Protocoles d'Urgence",
      feature3Desc: '"Mon ami se sent étourdi et a chaud, que dois-je faire ?"',
      feature3Prev: "Aperçu → récupération des contacts d'urgence locaux et des premiers secours.",
      disclaimer: "Les estimations sont fournies à titre indicatif. Suivez toujours les alertes officielles.",
      enter: "Commencer avec HeatShield",
      skipDash: "Passer au tableau de bord"
    },
    'العربية': {
      welcome: "مرحباً بك في HeatShield",
      subWelcome: "الإعداد يستغرق أقل من دقيقة",
      step1Eyebrow: "اللغة",
      step1Title: "اختر لغتك",
      step1Desc: "يعمل HeatShield بشكل أصلي بلغات متعددة.",
      step2Eyebrow: "الموقع",
      step2Title: "أين يجب أن أراقب؟",
      step2Desc: "يقوم HeatShield برسم خريطة لمخاطر الحرارة والأماكن الباردة في منطقتك. لا يتم تخزين موقعك.",
      detecting: "جاري التحديد...",
      useGps: "استخدام موقعي الحالي",
      typeCity: "سأكتب مدينتي في الدردشة",
      skip: "تخطي الآن",
      locSet: "تم تحديد الموقع عبر GPS",
      continue: "متابعة",
      back: "رجوع",
      step3Eyebrow: "القدرات",
      step3Title: "إليك ما يمكنني فعله",
      step3Desc: "انقر على أي مثال لرؤية معاينة حية.",
      feature1Title: "توقعات الطقس",
      feature1Desc: '"أعطني توقعات موجة الحر لمدة 7 أيام هنا."',
      feature1Prev: "معاينة ← جلب توقعات الطقس لمدة 7 أيام لمخاطر موجة الحر.",
      feature2Title: "إيجاد الأماكن الباردة",
      feature2Desc: '"ابحث عن أماكن باردة على خريطة الجزر الحرارية."',
      feature2Prev: "معاينة ← تحديد أقرب مراكز التبريد المتراكبة على بيانات حرارة سطح الأرض.",
      feature3Title: "بروتوكولات الطوارئ",
      feature3Desc: '"أرني أرقام الطوارئ لضربات الشمس."',
      feature3Prev: "معاينة ← استرداد جهات اتصال الطوارئ المحلية وخطوات الإسعافات الأولية.",
      disclaimer: "التقديرات للإرشاد فقط. اتبع دائماً تحذيرات الحرارة الرسمية.",
      enter: "البدء باستخدام HeatShield",
      skipDash: "تخطي إلى لوحة المعلومات"
    },
    'Deutsch': {
      welcome: "Willkommen bei HeatShield",
      subWelcome: "Einrichtung dauert weniger als eine Minute",
      step1Eyebrow: "SPRACHE",
      step1Title: "Wählen Sie Ihre Sprache",
      step1Desc: "HeatShield funktioniert nativ in mehreren Sprachen.",
      step2Eyebrow: "STANDORT",
      step2Title: "Wo soll ich überwachen?",
      step2Desc: "HeatShield kartiert Hitzeverteilungen und kühle Orte in Ihrer Umgebung. Ihr Standort wird nicht gespeichert.",
      detecting: "Ermittle...",
      useGps: "Aktuellen Standort verwenden",
      typeCity: "Ich tippe meine Stadt in den Chat",
      skip: "Überspringen",
      locSet: "Standort über GPS festgelegt",
      continue: "Weiter",
      back: "Zurück",
      step3Eyebrow: "FUNKTIONEN",
      step3Title: "Das kann ich tun",
      step3Desc: "Tippen Sie auf ein Beispiel für eine Live-Vorschau.",
      feature1Title: "Wettervorhersage",
      feature1Desc: '"Gibt es dieses Wochenende eine Hitzewelle?"',
      feature1Prev: "Vorschau → Abruf der 7-Tage-Wettervorhersage für Hitzewellenrisiken.",
      feature2Title: "Kühle Orte finden",
      feature2Desc: '"Wo ist die nächste klimatisierte Bibliothek?"',
      feature2Prev: "Vorschau → Lokalisierung der nächsten Kühlzentren mit Oberflächentemperatur-Overlay.",
      feature3Title: "Notfallprotokolle",
      feature3Desc: '"Mein Freund fühlt sich schwindelig und heiß, was soll ich tun?"',
      feature3Prev: "Vorschau → Abruf lokaler Notfallkontakte und Erste-Hilfe-Schritte.",
      disclaimer: "Schätzungen dienen nur zur Orientierung. Befolgen Sie offizielle Hitzewarnungen.",
      enter: "HeatShield starten",
      skipDash: "Zum Dashboard springen"
    }
  };

  const currentT = t[language] || t['English'];
  const dir = language === 'العربية' ? 'rtl' : 'ltr';
  const progressPercent = step === 1 ? '33%' : step === 2 ? '66%' : '100%';

  const languages = [
    { name: 'English', code: 'GB' },
    { name: 'Français', code: 'FR' },
    { name: 'Deutsch', code: 'DE' },
    { name: 'العربية', code: 'SA' }
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
        
        .hs-onboard-overlay {
          position: fixed; top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(16px);
          z-index: 9999; display: flex; align-items: center; justify-content: center;
          padding: 20px; font-family: 'Manrope', sans-serif; color: #FFFFFF;
        }

        .hs-onboard-modal {
          width: min(680px, 100%);
          background: #0A0A0A;
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 24px;
          padding: 36px 40px 32px;
          box-shadow: 0 40px 100px -20px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.02);
          direction: ${dir};
          text-align: ${language === 'العربية' ? 'right' : 'left'};
        }

        .hs-m-head { display: flex; align-items: center; gap: 14px; margin-bottom: 28px; }
        .hs-m-head .hs-badge {
          width: 44px; height: 44px; border-radius: 12px;
          background: linear-gradient(135deg, #FF6B00, #E60000);
          display: flex; align-items: center; justify-content: center;
          color: #FFFFFF; flex-shrink: 0;
          box-shadow: 0 8px 16px -4px rgba(255, 107, 0, 0.4);
        }
        .hs-m-head .hs-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 18px; color: #FFFFFF; }
        .hs-m-head .hs-sub { font-size: 13.5px; color: #A1A1AA; margin-top: 2px; }

        .hs-progress-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }
        .hs-progress-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #71717A; letter-spacing: 0.08em; font-weight: 500; }
        .hs-progress-track { height: 4px; border-radius: 2px; background: rgba(255, 255, 255, 0.08); flex: 1; margin: 0 16px; overflow: hidden; }
        .hs-progress-fill { height: 100%; width: ${progressPercent}; background: linear-gradient(90deg, #00E5FF 0%, #FFEA00 40%, #FF6B00 70%, #E60000 100%); border-radius: 2px; transition: width .4s cubic-bezier(0.4, 0, 0.2, 1); }

        .hs-eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #FF6B00; letter-spacing: 0.08em; margin: 0 0 10px; font-weight: 500; text-transform: uppercase; }
        .hs-modal-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 28px; margin: 0 0 14px; letter-spacing: -0.02em; color: #FFFFFF; }
        .hs-lede { font-size: 16px; color: #D4D4D8; line-height: 1.6; margin: 0 0 32px; }

        .hs-btn-primary {
          width: 100%; height: 54px; border-radius: 12px; border: none;
          background: linear-gradient(135deg, #FF6B00, #E60000);
          color: #FFFFFF; font-size: 16px; font-weight: 600; cursor: pointer;
          display: flex; align-items: center; justify-content: center; gap: 10px;
          margin-bottom: 14px; transition: all .2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .hs-btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 12px 24px -6px rgba(255,107,0,0.4); }
        .hs-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

        .hs-btn-secondary {
          width: 100%; height: 50px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.16);
          background: rgba(255, 255, 255, 0.05); color: #FAFAFA; font-size: 15px; font-weight: 600;
          cursor: pointer; margin-bottom: 14px; transition: all .2s ease;
        }
        .hs-btn-secondary:hover { border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.08); }

        .hs-loc-chip { display: flex; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #00E5FF; margin: 0 0 20px; justify-content: ${language === 'العربية' ? 'flex-end' : 'flex-start'}; }
        .hs-skip { font-size: 14.5px; color: #A1A1AA; text-decoration: underline; text-underline-offset: 4px; cursor: pointer; text-align: center; margin: 0 auto 24px; display: block; transition: color .2s ease; width: fit-content; }
        .hs-skip:hover { color: #FFFFFF; }
        
        .hs-back-link {
          display: inline-flex; align-items: center; gap: 6px; background: none; border: none; padding: 0;
          color: #A1A1AA; font-size: 14.5px; cursor: pointer; margin-bottom: 24px; font-weight: 500; transition: color .2s ease;
        }
        .hs-back-link:hover { color: #FFFFFF; }

        .hs-cap-card {
          border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px; padding: 20px 24px; margin-bottom: 16px;
          cursor: pointer; display: flex; gap: 20px; align-items: flex-start;
          transition: all .2s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(255, 255, 255, 0.04);
        }
        .hs-cap-card:hover { transform: translateY(-3px); border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.08); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); }
        .hs-cap-card.hs-active { border-color: #FF6B00; background: rgba(255, 107, 0, 0.05); }
        .hs-cap-icon {
          width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center;
          justify-content: center; flex-shrink: 0;
        }
        .hs-cap-icon.hs-heat { background: rgba(255, 107, 0, 0.15); color: #FF6B00; }
        .hs-cap-icon.hs-cool { background: rgba(0, 229, 255, 0.15); color: #00E5FF; }

        @keyframes hs-spin {
          to { transform: rotate(360deg); }
        }
        .hs-spinner {
          animation: hs-spin 1s linear infinite;
        }
        
        .hs-preview {
          margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08);
          font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #00E5FF; line-height: 1.6;
        }
        .hs-disclaimer { font-size: 13px; color: #A1A1AA; line-height: 1.6; margin: 16px 0 24px; text-align: center; }

        .hs-lang-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 28px; }
        .hs-lang-btn {
          padding: 18px 20px; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px;
          background: rgba(255, 255, 255, 0.03); color: #FAFAFA; cursor: pointer;
          display: flex; align-items: center; justify-content: space-between;
          font-size: 14.5px; font-weight: 600; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .hs-lang-btn:hover, .hs-lang-btn.hs-selected { border-color: #FF6B00; background: rgba(255, 107, 0, 0.08); transform: translateY(-2px); box-shadow: 0 8px 16px -8px rgba(255, 107, 0, 0.3); }
      `}</style>

      <div className="hs-onboard-overlay">
        <div className="hs-onboard-modal">
          
          <div className="hs-m-head">
            <div className="hs-badge"><SvgShield size={20} strokeWidth={2.5} /></div>
            <div>
              <div className="hs-title">{currentT.welcome}</div>
              <div className="hs-sub">{currentT.subWelcome}</div>
            </div>
          </div>

          <div className="hs-progress-row">
            <span className="hs-progress-label">STEP 0{step} / 03</span>
            <div className="hs-progress-track"><div className="hs-progress-fill"></div></div>
          </div>

          {step === 1 && (
            <div>
              <p className="hs-eyebrow">{currentT.step1Eyebrow}</p>
              <h1 className="hs-modal-title">{currentT.step1Title}</h1>
              <p className="hs-lede">{currentT.step1Desc}</p>

              <div className="hs-lang-grid">
                {languages.map(lang => (
                  <button 
                    key={lang.name}
                    className={`hs-lang-btn ${language === lang.name ? 'hs-selected' : ''}`}
                    onClick={() => { setLanguage(lang.name); setTimeout(() => setStep(2), 150); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '22px', height: '16px', borderRadius: '3px', overflow: 'hidden', display: 'flex' }}>
                        <Flag code={lang.code} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      </div>
                      {lang.name}
                    </div>
                    {dir === 'ltr' ? <ArrowRight size={16} color="#63666F" /> : <ArrowLeft size={16} color="#63666F" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <button className="hs-back-link" onClick={() => setStep(1)}>
                {dir === 'ltr' ? <ArrowLeft size={14} /> : <ArrowRight size={14} />} {currentT.back}
              </button>
              
              <p className="hs-eyebrow">{currentT.step2Eyebrow}</p>
              <h1 className="hs-modal-title">{currentT.step2Title}</h1>
              <p className="hs-lede">{currentT.step2Desc}</p>

              <button className="hs-btn-primary" onClick={requestLocation} disabled={isDetecting}>
                {isDetecting ? (
                  <>
                    <svg className="hs-spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line>
                      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                      <line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line>
                      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
                    </svg>
                    {currentT.detecting}
                  </>
                ) : (
                  <><SvgPin size={18} /> {currentT.useGps}</>
                )}
              </button>
              <button className="hs-btn-secondary" onClick={() => { setLocSetText(""); setStep(3); }}>
                {currentT.typeCity}
              </button>

              {locSetText && (
                <p className="hs-loc-chip"><Check size={14} /> <span>{locSetText}</span></p>
              )}

              <span className="hs-skip" onClick={() => setStep(3)}>{currentT.skip}</span>

              {locSetText && (
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                  <button className="hs-btn-secondary" style={{ width: 'auto', padding: '0 20px', marginBottom: 0 }} onClick={() => setStep(3)}>
                    {currentT.continue}
                  </button>
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div>
              <button className="hs-back-link" onClick={() => setStep(2)}>
                {dir === 'ltr' ? <ArrowLeft size={14} /> : <ArrowRight size={14} />} {currentT.back}
              </button>

              <p className="hs-eyebrow">{currentT.step3Eyebrow}</p>
              <h1 className="hs-modal-title">{currentT.step3Title}</h1>
              <p className="hs-lede">{currentT.step3Desc}</p>

              {/* Card 1 */}
              <div className={`hs-cap-card ${activeCard === 1 ? 'hs-active' : ''}`} onClick={() => setActiveCard(activeCard === 1 ? null : 1)}>
                <div className="hs-cap-icon hs-heat"><SvgTherm size={22} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 6px', color: '#FFFFFF' }}>{currentT.feature1Title}</p>
                  <p style={{ fontSize: '14.5px', color: '#D4D4D8', margin: 0 }}>{currentT.feature1Desc}</p>
                  {activeCard === 1 && <p className="hs-preview">{currentT.feature1Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={20} color="#D4D4D8" style={{ marginTop: '2px' }} /> : <ArrowLeft size={20} color="#D4D4D8" style={{ marginTop: '2px' }} />}
              </div>

              {/* Card 2 */}
              <div className={`hs-cap-card ${activeCard === 2 ? 'hs-active' : ''}`} onClick={() => setActiveCard(activeCard === 2 ? null : 2)}>
                <div className="hs-cap-icon hs-cool"><SvgRoute size={22} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 6px', color: '#FFFFFF' }}>{currentT.feature2Title}</p>
                  <p style={{ fontSize: '14.5px', color: '#D4D4D8', margin: 0 }}>{currentT.feature2Desc}</p>
                  {activeCard === 2 && <p className="hs-preview">{currentT.feature2Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={20} color="#D4D4D8" style={{ marginTop: '2px' }} /> : <ArrowLeft size={20} color="#D4D4D8" style={{ marginTop: '2px' }} />}
              </div>

              {/* Card 3 */}
              <div className={`hs-cap-card ${activeCard === 3 ? 'hs-active' : ''}`} onClick={() => setActiveCard(activeCard === 3 ? null : 3)}>
                <div className="hs-cap-icon hs-heat"><SvgShield size={22} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 6px', color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {currentT.feature3Title} <Info size={16} color="#A1A1AA" />
                  </p>
                  <p style={{ fontSize: '14.5px', color: '#D4D4D8', margin: 0 }}>{currentT.feature3Desc}</p>
                  {activeCard === 3 && <p className="hs-preview">{currentT.feature3Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={20} color="#D4D4D8" style={{ marginTop: '2px' }} /> : <ArrowLeft size={20} color="#D4D4D8" style={{ marginTop: '2px' }} />}
              </div>

              <p className="hs-disclaimer">{currentT.disclaimer}</p>

              <button className="hs-btn-primary" onClick={handleFinish}>{currentT.enter}</button>
              <span className="hs-skip" style={{ marginBottom: 0 }} onClick={handleFinish}>{currentT.skipDash}</span>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
