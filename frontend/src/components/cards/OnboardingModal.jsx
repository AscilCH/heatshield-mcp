import React, { useState, useEffect } from 'react';
import { Shield, MapPin, ArrowRight, ArrowLeft, Check, Info, CloudSun, Map, PhoneCall } from 'lucide-react';
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
          setLocSetText(t[language]?.locSet || "Location set via GPS");
        },
        (error) => {
          console.error("Location error:", error);
          setIsDetecting(false);
          alert("Location access denied. You can set it manually in the chat.");
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
      feature1Desc: '"Give me the 7-day heatwave forecast here."',
      feature1Prev: "Preview → pulling 7-day Open-Meteo ensemble forecasts for heatwave risk.",
      feature2Title: "Find Cooling Spots",
      feature2Desc: '"Find cool spots wrapped on the UHI map."',
      feature2Prev: "Preview → locating nearest cooling centers overlaying satellite land-surface temp data.",
      feature3Title: "Emergency Protocols",
      feature3Desc: '"Show me emergency numbers for heatstroke."',
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
      feature1Desc: '"Donne-moi les prévisions de canicule sur 7 jours."',
      feature1Prev: "Aperçu → récupération des prévisions sur 7 jours pour le risque de canicule.",
      feature2Title: "Trouver des Lieux Frais",
      feature2Desc: '"Trouve des lieux frais superposés sur la carte UHI."',
      feature2Prev: "Aperçu → localisation des centres de rafraîchissement sur la carte de température de surface.",
      feature3Title: "Protocoles d'Urgence",
      feature3Desc: '"Montre-moi les numéros d\'urgence pour les coups de chaleur."',
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
      feature1Desc: '"Gib mir die 7-Tage-Hitzewellen-Vorhersage."',
      feature1Prev: "Vorschau → Abruf der 7-Tage-Wettervorhersage für Hitzewellenrisiken.",
      feature2Title: "Kühle Orte finden",
      feature2Desc: '"Finde kühle Orte auf der UHI-Karte."',
      feature2Prev: "Vorschau → Lokalisierung der nächsten Kühlzentren mit Oberflächentemperatur-Overlay.",
      feature3Title: "Notfallprotokolle",
      feature3Desc: '"Zeige mir Notfallnummern für Hitzeschläge."',
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
          background: rgba(6, 7, 9, 0.76); backdrop-filter: blur(8px);
          z-index: 9999; display: flex; align-items: center; justify-content: center;
          padding: 20px; font-family: 'Manrope', sans-serif; color: #F2F1EC;
        }

        .hs-onboard-modal {
          width: min(490px, 100%);
          background: #15171C;
          border: 1px solid #282B33;
          border-radius: 20px;
          padding: 30px 32px 26px;
          box-shadow: 0 30px 70px rgba(0,0,0,0.5);
          direction: ${dir};
          text-align: ${language === 'العربية' ? 'right' : 'left'};
        }

        .hs-m-head { display: flex; align-items: center; gap: 12px; margin-bottom: 22px; }
        .hs-m-head .hs-badge {
          width: 40px; height: 40px; border-radius: 11px;
          background: linear-gradient(135deg, #E8590C, #D6293B);
          display: flex; align-items: center; justify-content: center;
          color: #FFF6EE; flex-shrink: 0;
        }
        .hs-m-head .hs-title { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 16px; }
        .hs-m-head .hs-sub { font-size: 12.5px; color: #989BA6; margin-top: 1px; }

        .hs-progress-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }
        .hs-progress-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #63666F; letter-spacing: 0.04em; }
        .hs-progress-track { height: 3px; border-radius: 2px; background: #282B33; flex: 1; margin: 0 14px; overflow: hidden; }
        .hs-progress-fill { height: 100%; width: ${progressPercent}; background: linear-gradient(90deg, #2DD4BF 0%, #F5A623 45%, #E8590C 72%, #D6293B 100%); border-radius: 2px; transition: width .35s ease; }

        .hs-eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #E8590C; letter-spacing: 0.05em; margin: 0 0 8px; }
        .hs-modal-title { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 23px; margin: 0 0 8px; letter-spacing: -0.01em; }
        .hs-lede { font-size: 14px; color: #989BA6; line-height: 1.6; margin: 0 0 22px; }

        .hs-btn-primary {
          width: 100%; height: 46px; border-radius: 12px; border: none;
          background: linear-gradient(135deg, #E8590C, #D6293B);
          color: #FFF6EE; font-size: 14px; font-weight: 600; cursor: pointer;
          display: flex; align-items: center; justify-content: center; gap: 9px;
          margin-bottom: 10px; transition: transform .15s ease, box-shadow .15s ease;
        }
        .hs-btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(232,89,12,0.28); }
        .hs-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

        .hs-btn-secondary {
          width: 100%; height: 44px; border-radius: 12px; border: 1px solid #282B33;
          background: transparent; color: #F2F1EC; font-size: 13.5px; font-weight: 500;
          cursor: pointer; margin-bottom: 10px; transition: border-color .15s ease, background .15s ease;
        }
        .hs-btn-secondary:hover { border-color: #3A3E48; background: #1C1F26; }

        .hs-loc-chip { display: flex; align-items: center; gap: 7px; font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #2DD4BF; margin: 0 0 14px; justify-content: ${language === 'العربية' ? 'flex-end' : 'flex-start'}; }
        .hs-skip { font-size: 12.5px; color: #63666F; text-decoration: underline; text-underline-offset: 2px; cursor: pointer; text-align: center; margin: 0 0 20px; display: block; }
        .hs-skip:hover { color: #989BA6; }
        
        .hs-back-link {
          display: inline-flex; align-items: center; gap: 6px; background: none; border: none;
          color: #63666F; font-size: 12.5px; cursor: pointer; padding: 0; margin-bottom: 16px;
        }
        .hs-back-link:hover { color: #989BA6; }

        .hs-cap-card {
          border: 1px solid #282B33; border-radius: 14px; padding: 14px 15px; margin-bottom: 9px;
          cursor: pointer; display: flex; gap: 12px; align-items: flex-start;
          transition: transform .15s ease, border-color .15s ease;
          background: transparent;
        }
        .hs-cap-card:hover { transform: translateY(-1px); }
        .hs-cap-card.hs-active { border-color: #3A3E48; background: #1C1F26; }
        .hs-cap-icon {
          width: 32px; height: 32px; border-radius: 9px; display: flex; align-items: center;
          justify-content: center; flex-shrink: 0;
        }
        .hs-cap-icon.hs-heat { background: #2B1608; color: #E8590C; }
        .hs-cap-icon.hs-cool { background: #123A36; color: #2DD4BF; }
        
        .hs-preview {
          margin-top: 10px; padding-top: 10px; border-top: 1px solid #282B33;
          font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; color: #2DD4BF; line-height: 1.6;
        }
        .hs-disclaimer { font-size: 11px; color: #63666F; line-height: 1.6; margin: 6px 0 18px; }

        .hs-lang-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
        .hs-lang-btn {
          padding: 14px; border: 1px solid #282B33; border-radius: 12px;
          background: #1C1F26; color: #F2F1EC; cursor: pointer;
          display: flex; align-items: center; justify-content: space-between;
          font-size: 13.5px; font-weight: 500; transition: all 0.2s ease;
        }
        .hs-lang-btn:hover, .hs-lang-btn.hs-selected { border-color: #E8590C; background: rgba(232,89,12,0.1); }
      `}</style>

      <div className="hs-onboard-overlay">
        <div className="hs-onboard-modal">
          
          <div className="hs-m-head">
            <div className="hs-badge"><Shield size={20} strokeWidth={2.5} /></div>
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
                <MapPin size={17} /> {isDetecting ? currentT.detecting : currentT.useGps}
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
                <div className="hs-cap-icon hs-heat"><CloudSun size={16} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '13.5px', fontWeight: '600', margin: '0 0 2px' }}>{currentT.feature1Title}</p>
                  <p style={{ fontSize: '12.5px', color: '#989BA6', margin: 0 }}>{currentT.feature1Desc}</p>
                  {activeCard === 1 && <p className="hs-preview">{currentT.feature1Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={15} color="#63666F" style={{ marginTop: '2px' }} /> : <ArrowLeft size={15} color="#63666F" style={{ marginTop: '2px' }} />}
              </div>

              {/* Card 2 */}
              <div className={`hs-cap-card ${activeCard === 2 ? 'hs-active' : ''}`} onClick={() => setActiveCard(activeCard === 2 ? null : 2)}>
                <div className="hs-cap-icon hs-cool"><Map size={16} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '13.5px', fontWeight: '600', margin: '0 0 2px' }}>{currentT.feature2Title}</p>
                  <p style={{ fontSize: '12.5px', color: '#989BA6', margin: 0 }}>{currentT.feature2Desc}</p>
                  {activeCard === 2 && <p className="hs-preview">{currentT.feature2Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={15} color="#63666F" style={{ marginTop: '2px' }} /> : <ArrowLeft size={15} color="#63666F" style={{ marginTop: '2px' }} />}
              </div>

              {/* Card 3 */}
              <div className={`hs-cap-card ${activeCard === 3 ? 'hs-active' : ''}`} onClick={() => setActiveCard(activeCard === 3 ? null : 3)}>
                <div className="hs-cap-icon hs-heat"><PhoneCall size={16} /></div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '13.5px', fontWeight: '600', margin: '0 0 2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {currentT.feature3Title} <Info size={13} color="#63666F" />
                  </p>
                  <p style={{ fontSize: '12.5px', color: '#989BA6', margin: 0 }}>{currentT.feature3Desc}</p>
                  {activeCard === 3 && <p className="hs-preview">{currentT.feature3Prev}</p>}
                </div>
                {dir === 'ltr' ? <ArrowRight size={15} color="#63666F" style={{ marginTop: '2px' }} /> : <ArrowLeft size={15} color="#63666F" style={{ marginTop: '2px' }} />}
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
