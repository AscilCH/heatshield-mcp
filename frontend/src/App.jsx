import React, { useState, useRef, useEffect, Fragment } from 'react'
import { MapContainer, TileLayer, Marker, useMap, GeoJSON, Pane } from 'react-leaflet'
import ClusterMarkers from './components/MarkerClusterGroup'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import DOMPurify from 'dompurify'
import axios from 'axios'
import { Shield, Briefcase, User, MoreHorizontal, ArrowLeft, Navigation, MapPin, AlertTriangle } from 'lucide-react'

// Modular Components (Single Responsibility Principle)
import MapController from './components/canvas/MapController'
import ForecastWidget from './components/charts/ForecastWidget'
import WBGTForecastWidget from './components/charts/WBGTForecastWidget'
import AQForecastWidget from './components/charts/AQForecastWidget'
import AlertBanner from './components/cards/AlertBanner'
import SymptomTriageCard from './components/cards/SymptomTriageCard'
import WorkRestCard from './components/cards/WorkRestCard'
import MedicalTriageAdvice from './components/cards/MedicalTriageAdvice'
import CitizenDashboard from './components/dashboard/CitizenDashboard'
import PlannerDashboard from './components/dashboard/PlannerDashboard'
import CheckInView from './components/dashboard/CheckInView'
import MarkdownRenderer from './components/chat/MarkdownRenderer'
import ComparisonWidget from './components/cards/ComparisonWidget'
import OnboardingModal from './components/cards/OnboardingModal'

import './App.css'

// API & WebSocket URLs
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace(/^http/, 'ws');

// Fix missing marker icons in Leaflet with Vite
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
})
L.Marker.prototype.options.icon = DefaultIcon

function App() {
  const [messages, setMessages] = useState([]);
  const [appLanguage, setAppLanguage] = useState('English');

  const handleOnboardComplete = (lang) => {
    setAppLanguage(lang);
    let welcomeMessage = 'Hello! I am HeatShield, your urban heat wave safety assistant. Where are you located, and how can I help you stay safe today?';
    if (lang === 'Français') welcomeMessage = 'Bonjour ! Je suis HeatShield, votre assistant de sécurité contre les vagues de chaleur urbaines. Où vous trouvez-vous et comment puis-je vous aider à rester en sécurité aujourd\'hui ?';
    if (lang === 'Deutsch') welcomeMessage = 'Hallo! Ich bin HeatShield, Ihr Assistent für urbane Hitzewellen. Wo befinden Sie sich und wie kann ich Ihnen heute helfen, sicher zu bleiben?';
    if (lang === 'العربية') welcomeMessage = 'مرحباً! أنا HeatShield، مساعدك للسلامة من موجات الحرارة الحضرية. أين أنت وكيف يمكنني مساعدتك اليوم؟';
    
    setMessages([{ role: 'assistant', content: welcomeMessage }]);
  };
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [markers, setMarkers] = useState([])
  const [forecastData, setForecastData] = useState(null)
  const [showWbgtForecast, setShowWbgtForecast] = useState(true)
  const [isStatCardCollapsed, setIsStatCardCollapsed] = useState(false)
  const [aqForecastData, setAqForecastData] = useState(null)
  const [uhiGeojson, setUhiGeojson] = useState(null)
  const [heatDomeGeojson, setHeatDomeGeojson] = useState(null)
  const [routeGeojson, setRouteGeojson] = useState(null)
  const [isochroneGeojson, setIsochroneGeojson] = useState(null)
  const [safetyAdvice, setSafetyAdvice] = useState(null)
  const [workRestGuidance, setWorkRestGuidance] = useState(null)
  const [canvasLayers, setCanvasLayers] = useState([])
  const [canvasChartData, setCanvasChartData] = useState(null)
  const [canvasComparisonData, setCanvasComparisonData] = useState(null)
  const [canvasCamera, setCanvasCamera] = useState(null)
  const [userLocation, setUserLocation] = useState(null)
  const [currentAction, setCurrentAction] = useState(null)
  const [wsAlert, setWsAlert] = useState(null)
  const [currentView, setCurrentView] = useState('dashboard') // 'dashboard', 'chat', 'check-in'
  const [currentWeather, setCurrentWeather] = useState(null)
  const [symptomTriage, setSymptomTriage] = useState(false)
  const [medicalTriageAdvice, setMedicalTriageAdvice] = useState(null)
  const [isPlannerMode, setIsPlannerMode] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState("")
  const [displayedStreamingMessage, setDisplayedStreamingMessage] = useState("")
  const [contacts, setContacts] = useState([
    { id: 1, name: "Grandma Fatima", status: "ok", last_update: "Replied 20 min ago", initials: "GF" },
    { id: 2, name: "Uncle Hedi", status: "alert", last_update: "No reply in 3 hours", initials: "UH" }
  ])
  const orchestratorCache = useRef({})
  const [orchestratorStatus, setOrchestratorStatus] = useState({})
  const chatEndRef = useRef(null)

  useEffect(() => {
    if (displayedStreamingMessage.length < streamingMessage.length) {
      const timeout = setTimeout(() => {
        setDisplayedStreamingMessage(streamingMessage.slice(0, displayedStreamingMessage.length + 1));
      }, 15);
      return () => clearTimeout(timeout);
    }
  }, [streamingMessage, displayedStreamingMessage]);

  // Telemetry Tracker
  useEffect(() => {
    const startTime = Date.now();
    let visitorId = localStorage.getItem('visitor_id');
    if (!visitorId) {
      visitorId = 'viz_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('visitor_id', visitorId);
    }
    
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;

    fetch(`${API_URL}/api/telemetry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'visit',
        visitor_id: visitorId,
        url: window.location.href,
        timezone: tz
      })
    }).catch(e => console.error("Telemetry warning", e));

    const handleUnload = () => {
      const duration = Math.round((Date.now() - startTime) / 1000);
      const payload = JSON.stringify({
        action: 'leave',
        visitor_id: visitorId,
        url: window.location.href,
        duration: duration,
        timezone: tz
      });
      // Try sendBeacon for reliability during unload, fallback to fetch if unavailable
      if (navigator.sendBeacon && Blob) {
        const blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon(`${API_URL}/api/telemetry`, blob);
      }
    };

    window.addEventListener('beforeunload', handleUnload);
    return () => {
      window.removeEventListener('beforeunload', handleUnload);
    };
  }, []);

  // Establish WebSocket connection for real-time push notifications
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/alerts`);
    ws.onopen = () => console.log('Connected to HeatShield Emergency WebSocket');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'emergency_alert') {
          setWsAlert(data);
          setTimeout(() => setWsAlert(null), 15000);
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };
    ws.onclose = () => console.log('WebSocket connection closed');
    return () => ws.close();
  }, []);

  // Request geolocation on mount
  useEffect(() => {
    const fetchClientWeather = async (lat, lng, fallbackCity) => {
      try {
        let cityName = fallbackCity;
        if (!cityName) {
          try {
            const nomRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=jsonv2`, {
              headers: { 'User-Agent': 'heatshield-mcp/0.1.0 (GeoAI Research Project)' }
            });
            const nomData = await nomRes.json();
            const addr = nomData.address || {};
            cityName = addr.city || addr.town || addr.village || addr.suburb || addr.county || addr.state || nomData.name || "Your Location";
          } catch(e) {
            cityName = "Your Location";
          }
        }

        const omRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,shortwave_radiation&hourly=uv_index,apparent_temperature&timezone=auto&forecast_days=1`);
        const omData = await omRes.json();
        
        if (omData.current) {
          const current = omData.current;
          const hourly = omData.hourly || {};
          const tempArray = hourly.apparent_temperature || [];
          const uvArray = hourly.uv_index || [];
          const maxUv = Math.max(...uvArray.filter(u => u !== null && u !== undefined), 0);
          
          const calcRisk = (appTemp, uv) => {
            if (appTemp >= 39.0 || uv >= 8.0) return "EXTREME";
            if (appTemp >= 33.0 || uv >= 6.0) return "HIGH";
            if (appTemp >= 27.0 || uv >= 3.0) return "MODERATE";
            return "LOW";
          };

          const getBlockRisk = (startIdx, endIdx) => {
            if (!tempArray || tempArray.length <= endIdx) return "UNKNOWN";
            const blockTemps = tempArray.slice(startIdx, endIdx + 1);
            const blockUvs = uvArray.slice(startIdx, endIdx + 1);
            const maxT = Math.max(...blockTemps.filter(t => t !== null && t !== undefined), 0);
            const maxU = Math.max(...blockUvs.filter(u => u !== null && u !== undefined), 0);
            return calcRisk(maxT, maxU);
          };

          const riskToStatus = (risk) => {
            if (risk === "EXTREME" || risk === "HIGH") return "Avoid";
            if (risk === "MODERATE") return "Caution";
            return "Safe";
          };

          const weatherObj = {
            type: "current_weather",
            location: cityName,
            temperature_celsius: current.temperature_2m,
            feels_like_celsius: current.apparent_temperature,
            humidity_percent: current.relative_humidity_2m,
            wind_speed_kmh: current.wind_speed_10m,
            uv_index: maxUv,
            heat_risk_level: calcRisk(current.apparent_temperature, maxUv),
            solar_radiation_wm2: current.shortwave_radiation,
            safe_windows: {
              morning: { time: "6am-11am", risk: getBlockRisk(6, 11), status: riskToStatus(getBlockRisk(6, 11)) },
              midday: { time: "12pm-4pm", risk: getBlockRisk(12, 16), status: riskToStatus(getBlockRisk(12, 16)) },
              evening: { time: "5pm-9pm", risk: getBlockRisk(17, 21), status: riskToStatus(getBlockRisk(17, 21)) }
            }
          };

          setCurrentWeather(weatherObj);
          setUserLocation({ lat, lng, name: cityName });
          setMarkers([{ lat, lng, label: `You are here (${cityName})`, type: "user_location" }]);
        }
      } catch (err) {
        console.error("Instant client weather fetch failed:", err);
      }
    };

    const fetchDefaultMap = (lat, lng, fallbackName) => {
      fetchClientWeather(lat, lng, fallbackName);
      axios.post(`${API_URL}/api/default-map`, { lat, lng })
        .then(res => {
          if (res.data.current_weather) {
            setCurrentWeather(res.data.current_weather);
            const cityName = res.data.current_weather.location || fallbackName || "Your Location";
            setUserLocation({ lat, lng, name: cityName });
          }
          if (res.data.uhi_geojson) setUhiGeojson(res.data.uhi_geojson);
          if (res.data.heat_dome_geojson) setHeatDomeGeojson(res.data.heat_dome_geojson);
          if (res.data.isochrone_geojson) setIsochroneGeojson(res.data.isochrone_geojson);
          if (res.data.markers && res.data.markers.length > 0) {
             setMarkers(res.data.markers);
          }
        })
        .catch(err => console.error("Error fetching default map:", err));
    };

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setUserLocation(loc);
          setMarkers([{ ...loc, label: "You are here", type: "user_location" }]);
          fetchDefaultMap(loc.lat, loc.lng);
        },
        () => {
          setUserLocation(null);
          setMarkers([]);
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleQuickAction = (actionText) => {
    setInput(actionText);
    setCurrentView('chat');
    submitMessage(actionText);
  };

  const resetChat = () => {
    setMessages([{ role: 'assistant', content: 'Hello! I am HeatShield, your urban heat wave safety assistant. Where are you located, and how can I help you stay safe today?' }]);
    setMarkers(userLocation ? [{ ...userLocation, label: "You are here", type: "user_location" }] : []);
    setUhiGeojson(null);
    setHeatDomeGeojson(null);
    setRouteGeojson(null);
    setIsochroneGeojson(null);
    setForecastData(null);
    setAqForecastData(null);
    setSafetyAdvice(null);
    setWorkRestGuidance(null);
    setSymptomTriage(false);
    setMedicalTriageAdvice(null);
    setCanvasLayers([]);
    setCanvasChartData(null);
    setCanvasComparisonData(null);
    setCanvasCamera(null);
    orchestratorCache.current = {};
    setOrchestratorStatus({});
    setCurrentView('dashboard');
  };

  const submitMessage = async (msgText) => {
    const textToSend = msgText || input;
    if (!textToSend.trim()) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: textToSend }]);
    setIsLoading(true);
    setCurrentAction("🧠 Initializing agentic reasoning...");
    setStreamingMessage("");
    setDisplayedStreamingMessage("");

    // Inject language directive under the hood
    let apiMessage = textToSend;
    if (appLanguage !== 'English') {
       apiMessage = `[SYSTEM INSTRUCTION: The user's interface language is set to ${appLanguage}. You MUST generate your final response, markdown, and advice entirely in ${appLanguage}.] ` + textToSend;
    }

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'heatshield-demo-key'
        },
        body: JSON.stringify({
          message: apiMessage,
          history: messages,
          latitude: userLocation?.lat || null,
          longitude: userLocation?.lng || null
        })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = "";

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n');
          buffer = parts.pop();

          for (const part of parts) {
            if (part.trim()) {
              try {
                const data = JSON.parse(part);
                if (data.type === 'chunk') {
                  setStreamingMessage(prev => prev + data.text);
                } else if (data.type === 'clear_chunk') {
                  setStreamingMessage("");
                  setDisplayedStreamingMessage("");
                } else if (data.type === 'tool_call') {
                  setStreamingMessage("");
                  setDisplayedStreamingMessage("");
                  const actionMap = {
                    "geocode_location": "🔍 Geocoding location...",
                    "get_weather_and_heat_risk": "🌤️ Checking live weather & risk...",
                    "get_air_quality": "💨 Checking air quality...",
                    "get_air_quality_forecast": "🔮 Predicting 5-day air quality...",
                    "find_cooling_spots": "🏖️ Searching OSM for cooling spots...",
                    "get_heat_safety_advice": "📚 Consulting WHO safety guidelines...",
                    "get_heatwave_forecast": "📈 Generating 7-day forecast...",
                    "query_emergency_protocols": "⚕️ Searching ChromaDB for protocols...",
                    "get_urban_heat_island_heatmap": "🗺️ Generating spatial UHI heatmap...",
                    "get_walking_route": "🚶 Calculating walking route...",
                    "generate_walkability_isochrone": "⏱️ Generating walkability isochrone...",
                    "search_web_for_pdfs": "🌐 Searching for official PDFs...",
                    "ingest_emergency_document_url": "📥 Downloading & vectorizing PDF...",
                    "get_occupational_heat_guidance": "👷 Fetching OSHA/NIOSH work-rest cycles..."
                  };
                  setCurrentAction(actionMap[data.name] || `⚙️ Running ${data.name}...`);
                } else if (data.type === 'partial_map_update') {
                  try {
                    const parsedData = typeof data.data === 'string' ? JSON.parse(data.data) : data.data;
                    if (parsedData.heatmap_geojson) {
                      setUhiGeojson(prev => {
                        if (!prev) return parsedData.heatmap_geojson;
                        return {
                          ...prev,
                          features: [...(prev.features || []), ...(parsedData.heatmap_geojson.features || [])]
                        };
                      });
                    }
                    if (parsedData.isochrone_geojson) {
                      setIsochroneGeojson(prev => {
                        if (!prev) return parsedData.isochrone_geojson;
                        return {
                          ...prev,
                          features: [...(prev.features || []), ...(parsedData.isochrone_geojson.features || [])]
                        };
                      });
                    }
                    if (parsedData.elements) {
                      const newMarkers = parsedData.elements
                        .filter(el => el.lat && el.lon)
                        .slice(0, 20)
                        .map(el => {
                          const tags = el.tags || {};
                          return {
                            type: "cooling_spot",
                            lat: el.lat,
                            lng: el.lon,
                            label: tags.name || tags.amenity || tags.leisure || 'Cooling Spot',
                            tags: tags
                          };
                        });
                      setMarkers(prev => [...(prev || []), ...newMarkers]);
                    }
                  } catch (e) {
                    console.error("Error parsing partial_map_update data", e);
                  }
                } else if (data.type === 'final') {
                  const { text, markers: newMarkers, forecast, aq_forecast, uhi_geojson, heat_dome_geojson, route_geojson, isochrone_geojson, safety_advice, work_rest_guidance, medical_triage_advice, symptom_triage } = data;
                  const cleanedText = (text || "").replace(/\n#\n/g, '\n### ').replace(/\n##\n/g, '\n### ');
                  if (cleanedText.trim().length > 0) {
                    setMessages(prev => [...prev, { role: 'assistant', content: cleanedText }]);
                  }
                  setStreamingMessage("");
                  if (forecast !== undefined) { setForecastData(forecast); setShowWbgtForecast(true); }
                  if (aq_forecast !== undefined) setAqForecastData(aq_forecast);
                  if (uhi_geojson !== undefined) setUhiGeojson(uhi_geojson);
                  if (heat_dome_geojson !== undefined) setHeatDomeGeojson(heat_dome_geojson);
                  if (route_geojson !== undefined) setRouteGeojson(route_geojson);
                  if (isochrone_geojson !== undefined) setIsochroneGeojson(isochrone_geojson);
                  if (safety_advice !== undefined) setSafetyAdvice(safety_advice);
                  if (work_rest_guidance !== undefined) setWorkRestGuidance(work_rest_guidance);
                  if (medical_triage_advice !== undefined) setMedicalTriageAdvice(medical_triage_advice);
                  if (symptom_triage !== undefined) setSymptomTriage(symptom_triage);
                  if (data.canvas_layers) setCanvasLayers(data.canvas_layers);
                  if (data.canvas_chart) setCanvasChartData(data.canvas_chart);
                  if (data.canvas_comparison) setCanvasComparisonData(data.canvas_comparison);
                  if (data.canvas_camera) setCanvasCamera(data.canvas_camera);
                  if (newMarkers && newMarkers.length > 0) setMarkers(newMarkers);
                }
              } catch (e) {
                console.error("Error parsing stream chunk:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `⚠️ **Connection or Security Error:** ${error.message}` 
      }]);
    } finally {
      setIsLoading(false);
      setCurrentAction(null);
    }
  };

  const createCustomIcon = (color, isUserLocation = false) => {
    if (isUserLocation) {
      return new L.DivIcon({
        className: 'custom-div-icon',
        html: `<div class="user-location-pulse"></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
    }
    return new L.DivIcon({
      className: 'custom-div-icon',
      html: `<div style="background-color:${color};width:16px;height:16px;border-radius:50%;border:2px solid #1A1512;box-shadow:0 0 10px ${color}"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
  };

  const getMarkerColor = (marker) => {
    if (marker.type === 'cooling_spot') return '#2ECF8E';
    if (marker.tags?.risk === 'EXTREME') return '#FF5A3C';
    if (marker.tags?.risk === 'CAUTION') return '#FFB020';
    return '#FF5A3C';
  };

  const getRiskColorClass = (risk) => {
    if (!risk) return 'neutral';
    switch (risk.toUpperCase()) {
      case 'EXTREME': return 'risk-extreme';
      case 'HIGH': return 'risk-high';
      case 'MODERATE': return 'risk-moderate';
      case 'LOW': return 'risk-low';
      default: return 'neutral';
    }
  };

  const getDynamicWindow = (timeKey, fallbackTitle) => {
    if (currentWeather?.safe_windows?.[timeKey]) {
      const win = currentWeather.safe_windows[timeKey];
      return {
        title: fallbackTitle,
        time: win.time,
        status: win.status,
        class: `block-${win.status.toLowerCase()}`
      };
    }
    return { title: fallbackTitle, time: '---', status: '---', class: 'block-neutral' };
  };

  const riskLevel = currentWeather?.heat_risk_level;
  const morningWindow = getDynamicWindow('morning', 'Morning');
  const middayWindow = getDynamicWindow('midday', 'Midday');
  const eveningWindow = getDynamicWindow('evening', 'Evening');

  return (
    <div className="app-container">
      <OnboardingModal setUserLocation={setUserLocation} />
      <AlertBanner alert={wsAlert} onClose={() => setWsAlert(null)} />
      
      {/* Background Map & Canvas */}
      <div className="map-container">
        {(uhiGeojson || heatDomeGeojson || routeGeojson || isochroneGeojson || markers.length > 1) && (
          <button 
            onClick={() => {
              setUhiGeojson(null);
              setHeatDomeGeojson(null);
              setRouteGeojson(null);
              setIsochroneGeojson(null);
              setMarkers(userLocation ? [{ ...userLocation, label: "You are here", type: "user_location" }] : []);
              orchestratorCache.current = {};
              setOrchestratorStatus({});
            }}
            className="clear-overlay-btn"
            style={{
              position: 'absolute', bottom: '30px', left: '30px', zIndex: 1000,
              background: 'rgba(38, 32, 29, 0.9)', backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.1)', color: '#f8fafc',
              padding: '10px 16px', borderRadius: '8px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px'
            }}
          >
            ✕ Clear Map Overlays
          </button>
        )}
        <MapContainer center={[0, 0]} zoom={2} style={{ height: '100%', width: '100%' }} zoomControl={false}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          <MapController markers={markers} routeGeojson={routeGeojson} uhiGeojson={uhiGeojson} isochroneGeojson={isochroneGeojson} heatDomeGeojson={heatDomeGeojson} canvasCamera={canvasCamera} canvasLayers={canvasLayers} />
          <ClusterMarkers markers={markers} createCustomIcon={createCustomIcon} getMarkerColor={getMarkerColor} />
          
          {heatDomeGeojson && (
            <Pane name="heat-dome-pane" style={{ zIndex: 400 }}>
              <GeoJSON 
                data={heatDomeGeojson} 
                style={() => ({ color: '#ff1744', fillColor: '#f43f5e', weight: 3.5, dashArray: '8, 8', fillOpacity: 0.35 })}
                onEachFeature={(feat, layer) => layer.bindPopup("<div style='color:#1e293b; padding:4px;'><strong>🔥 500hPa Blocking High (Heat Dome)</strong></div>")}
              />
            </Pane>
          )}

          {uhiGeojson && (
            <Pane name="heat-pane" className="heat-pane-blur" style={{ zIndex: 450 }}>
              <GeoJSON 
                data={uhiGeojson} 
                style={(feature) => ({
                  color: feature.properties?.isHighway ? feature.properties?.color : (feature.properties?.type === 'heat_trap_low' ? feature.properties?.color : 'transparent'),
                  fillColor: feature.properties?.color || '#ef4444',
                  weight: feature.properties?.isHighway ? 3 : (feature.properties?.type === 'heat_trap_low' ? 1 : 0),
                  fillOpacity: feature.properties?.isHighway ? 0 : (feature.properties?.fillOpacity ?? 0.8)
                })}
              />
            </Pane>
          )}

          {routeGeojson?.features?.length > 0 && (
            <>
              <GeoJSON data={routeGeojson} style={(feat) => ({ color: feat.properties?.color || '#2ECF8E', weight: 5, fillOpacity: 0 })} />
              {routeGeojson.features.map((feat, fIdx) => {
                const coords = feat?.geometry?.coordinates;
                if (!coords || coords.length < 2) return null;
                return (
                  <Fragment key={"route_markers_" + fIdx}>
                    <Marker position={[coords[0][1], coords[0][0]]} icon={createCustomIcon('#2ECF8E')} />
                    <Marker position={[coords[coords.length - 1][1], coords[coords.length - 1][0]]} icon={createCustomIcon('#2ECF8E')} />
                  </Fragment>
                );
              })}
            </>
          )}

          {isochroneGeojson && (
            <GeoJSON data={isochroneGeojson} style={(feat) => ({ color: feat.properties?.color || '#10b981', fillColor: feat.properties?.fillColor || '#10b981', weight: 2, fillOpacity: feat.properties?.fillOpacity ?? 0.35 })} />
          )}
        </MapContainer>

        <div className="map-legend">
          <span><div className="legend-dot" style={{background: '#E63946'}}></div> Extreme</span>
          <span><div className="legend-dot" style={{background: '#F5A623'}}></div> Caution</span>
          <span><div className="legend-dot" style={{background: '#3ECF8E'}}></div> Cool spot</span>
          <span><div className="legend-dot" style={{background: '#10B981'}}></div> Natural cool zone</span>
        </div>
      </div>

      {/* Floating Glassmorphism Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={28} color="var(--risk-extreme)" />
            <h1>HeatShield</h1>
          </div>
          <div style={{ display: 'flex', gap: '16px', color: '#94a3b8', alignItems: 'center' }}>
            <Briefcase 
              size={28} 
              className="header-icon"
              style={{ color: isPlannerMode ? '#3b82f6' : '#94a3b8' }} 
              onClick={() => setIsPlannerMode(!isPlannerMode)} 
              title="Toggle Planner Mode"
            />
            <User size={28} className="header-icon" style={{ color: !isPlannerMode ? '#3b82f6' : '#94a3b8' }} />
            <MoreHorizontal size={28} className="header-icon" />
          </div>
        </div>
        
        {currentView === 'dashboard' && (
          isPlannerMode ? <PlannerDashboard /> : (
            <CitizenDashboard 
              currentWeather={currentWeather}
              riskLevel={riskLevel}
              getRiskColorClass={getRiskColorClass}
              morningWindow={morningWindow}
              middayWindow={middayWindow}
              eveningWindow={eveningWindow}
              onQuickAction={handleQuickAction}
              onOpenCheckIn={() => setCurrentView('check-in')}
            />
          )
        )}

        {currentView === 'check-in' && (
          <CheckInView contacts={contacts} onBack={() => setCurrentView('dashboard')} />
        )}

        {currentView === 'chat' && (
          <>
            <div className="chat-header-actions" style={{ padding: '20px 20px 0', display: 'flex', justifyContent: 'flex-start' }}>
              <button className="test-siren-btn-small" onClick={resetChat} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ArrowLeft size={16} /> Back to Dashboard
              </button>
            </div>
            
            <div className="chat-history">
              {messages.map((msg, idx) => {
                if (msg.role === 'user') {
                  return <div key={idx} className="msg-user">{msg.content}</div>;
                }
                return (
                  <div key={idx} className="msg-ai">
                    <MarkdownRenderer content={msg.content} />
                  </div>
                );
              })}

              {symptomTriage && (
                <SymptomTriageCard 
                  onSubmit={(symptoms) => submitMessage(`I am experiencing: ${symptoms.join(', ')}. What should I do?`)} 
                  onEmergency={(symptoms) => submitMessage(`EMERGENCY: I am calling emergency services! My symptoms are: ${symptoms.join(', ')}`)} 
                />
              )}

              {medicalTriageAdvice && (
                <MedicalTriageAdvice 
                  medicalTriageAdvice={medicalTriageAdvice} 
                  onEmergencyCall={() => submitMessage(`EMERGENCY: I am calling emergency services!`)} 
                />
              )}

              {workRestGuidance && <WorkRestCard workRestGuidance={workRestGuidance} />}

              {isLoading && (
                <div className="message assistant">
                  {displayedStreamingMessage && <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(displayedStreamingMessage.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')) }} />}
                  {currentAction && (
                    <div className="msg-status" style={{ marginBottom: '10px' }}>
                      <span className="spinner" style={{marginRight: '8px', display: 'inline-block'}}>⏳</span> 
                      {currentAction}
                    </div>
                  )}
                  {!displayedStreamingMessage && !currentAction && (
                    <div className="action-badge" style={{ padding: '8px 12px', background: '#3b82f640', color: '#60a5fa', borderRadius: '8px', fontSize: '0.9rem', display: 'inline-block', fontWeight: '500', border: '1px solid #3b82f680' }}>
                      Thinking...
                    </div>
                  )}
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </>
        )}
      </div>

      {/* Panel Dock (Top Right: Live Gauges & Forecast Overlays) */}
      <div className="panel-dock">
        {currentWeather && (
          <div className="floating-stat-card">
            <div className="stat-card" style={{ padding: isStatCardCollapsed ? '16px 20px' : '24px' }}>
              <div className="stat-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: isStatCardCollapsed ? 0 : '12px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '11px', letterSpacing: '1px', color: 'var(--text-faint)', fontWeight: 600 }}>TODAY'S READING</span>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>📍 {userLocation?.name || currentWeather.location || "Location"}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isStatCardCollapsed && (
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--risk-extreme)' }}>
                      {Math.round(currentWeather.temperature_celsius)}°C • {currentWeather.heat_risk_level || "RISK"}
                    </span>
                  )}
                  <button 
                    className="close-btn" 
                    style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '6px', background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' }}
                    onClick={() => setIsStatCardCollapsed(!isStatCardCollapsed)}
                  >
                    {isStatCardCollapsed ? '▼ Expand' : '▲ Minimize'}
                  </button>
                </div>
              </div>
            
              {!isStatCardCollapsed && (
                <>
                  <div className="radial-gauge-container">
                    <div 
                      className="radial-gauge" 
                      data-risk={currentWeather.heat_risk_level || "UNKNOWN"}
                      style={{
                        background: (() => {
                          const temp = currentWeather.temperature_celsius || 20;
                          const percentage = Math.max(0, Math.min(100, ((temp - 10) / (45 - 10)) * 100));
                          return `conic-gradient(from 200deg, #10b981 0%, #eab308 ${Math.min(percentage, 35)}%, #f97316 ${Math.min(percentage, 65)}%, #ef4444 ${percentage}%, rgba(255,255,255,0.05) ${percentage}%, rgba(255,255,255,0.05) 100%)`;
                        })()
                      }}
                    >
                      <div className="radial-gauge-text">
                        <span className="temp">{Math.round(currentWeather.temperature_celsius)}°</span>
                        <span className="feels-like">FEELS {Math.round(currentWeather.feels_like_celsius || currentWeather.apparent_temperature_celsius || currentWeather.temperature_celsius)}</span>
                      </div>
                    </div>
                    
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="stat-label">HUMIDITY</span>
                        <span className="stat-value">{Math.round(currentWeather.humidity_percent)}%</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">MAX UV</span>
                        <span className="stat-value">{currentWeather.uv_index?.toFixed(2) || "8.5"}</span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">PEAK HRS</span>
                        <span className="stat-value">12-4PM</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <div className="forecast-overlay-container">
          {canvasComparisonData && (
            <div className="forecast-overlay comparison-overlay" style={{ width: '100%' }}>
              <ComparisonWidget data={canvasComparisonData} onClose={() => setCanvasComparisonData(null)} />
            </div>
          )}
          {forecastData && (
            <>
              <div className="forecast-overlay" style={{ width: '100%' }}>
                <ForecastWidget data={forecastData} onClose={() => setForecastData(null)} />
              </div>
              {forecastData[0]?.wbgt_celsius && showWbgtForecast && (
                <div className="forecast-overlay" style={{ width: '100%' }}>
                  <WBGTForecastWidget data={forecastData} onClose={() => setShowWbgtForecast(false)} />
                </div>
              )}
            </>
          )}
          {aqForecastData && (
            <div className="forecast-overlay aq-overlay">
              <AQForecastWidget data={aqForecastData} onClose={() => setAqForecastData(null)} />
            </div>
          )}
        </div>
      </div>

      {/* Floating Chat Pill */}
      {(currentView === 'dashboard' || currentView === 'chat') && (
        <div className="chat-input-wrapper">
          <div className="quick-action-bubbles">
            <button onClick={() => { setCurrentView('chat'); submitMessage("What is the heat risk today?"); }}>🌡️ Heat Risk</button>
            <button onClick={() => { setCurrentView('chat'); submitMessage("Give me the nearest cold place and direction"); }}>❄️ Nearest Cool Spot</button>
            <button onClick={() => { setCurrentView('chat'); submitMessage("Give me a safe work schedule"); }}>👷 Work Schedule</button>
          </div>
          <form className="input-area" onSubmit={(e) => { e.preventDefault(); setCurrentView('chat'); submitMessage(input); }}>
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask HeatShield anything"
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
              <Navigation size={18} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;
