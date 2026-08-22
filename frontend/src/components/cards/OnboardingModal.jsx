import React, { useState, useEffect } from 'react';
import { Globe, MapPin, Compass, Shield, ArrowRight } from 'lucide-react';

export default function OnboardingModal({ onComplete, setUserLocation }) {
  const [isOpen, setIsOpen] = useState(true);
  const [language, setLanguage] = useState('English');
  const [step, setStep] = useState(1);
  const [isDetecting, setIsDetecting] = useState(false);

  // Check if we've already onboarded
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

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-[#1C2025] border border-gray-700/50 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500/10 to-red-600/10 p-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-100">Welcome to HeatShield</h2>
              <p className="text-sm text-gray-400">Autonomous Urban Heat AI Agent</p>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6">
          
          {/* STEP 1: Language Selection */}
          {step === 1 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <h3 className="text-lg font-semibold text-gray-200 mb-2">1. Choose your language</h3>
              <p className="text-sm text-gray-400 mb-4">HeatShield operates natively across multiple languages.</p>
              
              <div className="grid grid-cols-2 gap-3">
                {['English', 'Français', 'Deutsch', 'العربية'].map(lang => (
                  <button
                    key={lang}
                    onClick={() => { setLanguage(lang); setStep(2); }}
                    className="p-3 border border-gray-700 rounded-lg text-gray-300 hover:bg-orange-500/10 hover:border-orange-500/50 hover:text-orange-400 transition-colors text-left flex justify-between items-center group"
                  >
                    {lang}
                    <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 2: Location Setup */}
          {step === 2 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <h3 className="text-lg font-semibold text-gray-200 mb-2">2. Set your location</h3>
              <p className="text-sm text-gray-400 mb-4">To provide accurate spatial risk assessments, HeatShield needs your location.</p>
              
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                <div className="flex flex-col gap-3">
                  <button 
                    onClick={requestLocation}
                    disabled={isDetecting}
                    className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-orange-600 hover:bg-orange-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                  >
                    <MapPin className="w-4 h-4" />
                    {isDetecting ? "Detecting GPS..." : "Use Current GPS Location"}
                  </button>
                  <div className="text-center text-xs text-gray-500 my-1">OR</div>
                  <button 
                    onClick={() => setStep(3)}
                    className="w-full py-2 px-4 bg-transparent border border-gray-600 hover:bg-gray-800 text-gray-300 rounded-lg font-medium transition-colors"
                  >
                    I'll type my city in the chat
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Capability Guide */}
          {step === 3 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <h3 className="text-lg font-semibold text-gray-200 mb-2">3. What you can do</h3>
              <p className="text-sm text-gray-400 mb-4">You are talking to an autonomous AI agent. Try asking it to:</p>
              
              <ul className="space-y-3">
                <li className="flex gap-3 items-start bg-gray-800/30 p-3 rounded-lg border border-gray-700/30">
                  <Globe className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="block text-sm font-medium text-gray-200">Track Urban Heat</span>
                    <span className="block text-xs text-gray-400">"Map the urban heat island effect here."</span>
                  </div>
                </li>
                <li className="flex gap-3 items-start bg-gray-800/30 p-3 rounded-lg border border-gray-700/30">
                  <Compass className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="block text-sm font-medium text-gray-200">Find Safe Routes</span>
                    <span className="block text-xs text-gray-400">"Find nearby cooling spots and draw a walking route."</span>
                  </div>
                </li>
                <li className="flex gap-3 items-start bg-gray-800/30 p-3 rounded-lg border border-gray-700/30">
                  <Shield className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="block text-sm font-medium text-gray-200">Calculate WBGT</span>
                    <span className="block text-xs text-gray-400">"Calculate the WBGT for heavy work."</span>
                  </div>
                </li>
              </ul>
              
              <button 
                onClick={handleFinish}
                className="w-full mt-4 py-3 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-400 hover:to-red-500 text-white rounded-xl font-bold shadow-lg transition-all"
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
