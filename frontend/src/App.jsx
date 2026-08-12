import { useState, useRef, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap, GeoJSON, Pane } from 'react-leaflet'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Navigation, Sun, PlusSquare, MapPin, Heart, Briefcase, User, MoreHorizontal, AlertTriangle, CheckCircle2, Phone } from 'lucide-react'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import './App.css'

// API URL: uses environment variable in production, falls back to localhost for dev
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

// Helper component to smoothly move the map when markers change
function MapController({ markers }) {
  const map = useMap()
  
  useEffect(() => {
    if (markers.length > 0) {
      const searchLocation = markers.find(m => m.type === 'geocode_location')
      
      if (searchLocation) {
        map.flyTo([searchLocation.lat, searchLocation.lng], 13, { duration: 2 })
      } else {
        const userLoc = markers.find(m => m.type === 'user_location')
        if (userLoc) {
            map.flyTo([userLoc.lat, userLoc.lng], 13, { duration: 2 })
        } else {
            const last = markers[markers.length - 1]
            map.flyTo([last.lat, last.lng], 13, { duration: 2 })
        }
      }
    }
  }, [markers, map])
  
  return null
}

// Chart Component for Heatwave & Soil Moisture Forecast
function ForecastWidget({ data, onClose }) {
  if (!data || data.length === 0) return null;
  
  const chartData = data.map(d => ({
    name: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
    Temp: d.max_temp_c,
    FeelsLike: d.feels_like_c,
    Moisture: d.soil_moisture * 100 // Scale to 0-100 for better visibility on same chart
  }));

  return (
    <div className="forecast-widget">
      <div className="widget-header">
        <h3>7-Day Heat & Drought Prediction</h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div style={{ height: '200px', width: '100%', marginTop: '10px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis dataKey="name" stroke="#fff" fontSize={12} />
            <YAxis yAxisId="left" stroke="#fff" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} />
            <YAxis yAxisId="right" orientation="right" stroke="#3b82f6" fontSize={12} domain={[0, 100]} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Line yAxisId="left" type="monotone" dataKey="Temp" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Max Temp (°C)" />
            <Line yAxisId="left" type="monotone" dataKey="FeelsLike" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Feels Like (°C)" />
            <Line yAxisId="right" type="monotone" dataKey="Moisture" stroke="#3b82f6" strokeWidth={2} name="Soil Moisture (%)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Chart Component for Air Quality Forecast
function AQForecastWidget({ data, onClose }) {
  if (!data || data.length === 0) return null;
  
  const chartData = data.map(d => ({
    name: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
    PM10: d.max_pm10,
    PM25: d.max_pm25
  }));

  return (
    <div className="forecast-widget aq-widget">
      <div className="widget-header">
        <h3>5-Day Air Quality Forecast</h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div style={{ height: '200px', width: '100%', marginTop: '10px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis dataKey="name" stroke="#fff" fontSize={12} />
            <YAxis stroke="#fff" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Line type="monotone" dataKey="PM10" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4 }} name="PM10 (Dust)" />
            <Line type="monotone" dataKey="PM25" stroke="#ec4899" strokeWidth={3} dot={{ r: 4 }} name="PM2.5 (Smoke)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function SafetyAdviceWidget({ advice, onClose }) {
  if (!advice) return null;
  
  // Format the raw text from the tool output
  const formattedLines = advice.split('\n').filter(l => l.trim().length > 0);
  
  return (
    <div className="forecast-widget" style={{ borderLeft: '4px solid #ef4444' }}>
      <div className="widget-header">
        <h3>⚕️ WHO/CDC Safety Advice</h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div style={{ padding: '10px 0', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.5' }}>
        {formattedLines.map((line, i) => {
          if (line.startsWith('-') || line.startsWith('•')) {
            return <p key={i} style={{ marginLeft: '10px', marginBottom: '8px' }}>{line}</p>;
          }
          return <p key={i} style={{ marginBottom: '8px' }}><strong>{line}</strong></p>;
        })}
      </div>
    </div>
  )
}

function AlertBanner({ alert, onClose }) {
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
  )
}

function SymptomTriageCard({ onSubmit, onEmergency }) {
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
  )
}

function PlannerDashboard() {
  return (
    <div className="zero-state-dashboard planner-dashboard" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', color: '#f8fafc' }}>City Operations</h2>
        <button style={{ backgroundColor: '#1e293b', color: '#94a3b8', border: '1px solid #334155', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}>
          Export Report ⬇
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
        <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#94a3b8' }}>UHI Severity (Avg)</p>
          <h3 style={{ margin: 0, fontSize: '24px', color: '#fca5a5' }}>+4.2°C</h3>
        </div>
        <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#94a3b8' }}>Vulnerable Pop at Risk</p>
          <h3 style={{ margin: 0, fontSize: '24px', color: '#f8fafc' }}>12,400</h3>
        </div>
      </div>

      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#f8fafc' }}>High Risk Neighborhoods</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left', color: '#cbd5e1' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
            <th style={{ padding: '8px 0' }}>Area</th>
            <th style={{ padding: '8px 0' }}>UHI</th>
            <th style={{ padding: '8px 0' }}>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: '1px solid #334155' }}>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Südstadt</td>
            <td style={{ padding: '12px 0', color: '#fca5a5' }}>+5.1°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#fff' }}>Critical</span></td>
          </tr>
          <tr style={{ borderBottom: '1px solid #334155' }}>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Innenstadt-Ost</td>
            <td style={{ padding: '12px 0', color: '#f59e0b' }}>+3.8°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#f59e0b', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#000' }}>Warning</span></td>
          </tr>
          <tr>
            <td style={{ padding: '12px 0', fontWeight: 'bold', color: '#f8fafc' }}>Oststadt</td>
            <td style={{ padding: '12px 0', color: '#4ade80' }}>+1.2°C</td>
            <td style={{ padding: '12px 0' }}><span style={{ background: '#22c55e', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', color: '#fff' }}>Stable</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am HeatShield, your urban heat wave safety assistant. Where are you located, and how can I help you stay safe today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [markers, setMarkers] = useState([])
  const [contacts, setContacts] = useState([])
  const [forecastData, setForecastData] = useState(null)
  const [aqForecastData, setAqForecastData] = useState(null)
  const [uhiGeojson, setUhiGeojson] = useState(null)
  const [routeGeojson, setRouteGeojson] = useState(null)
  const [isochroneGeojson, setIsochroneGeojson] = useState(null)
  const [safetyAdvice, setSafetyAdvice] = useState(null)
  const [workRestGuidance, setWorkRestGuidance] = useState(null)
  const [userLocation, setUserLocation] = useState(null)
  const [currentAction, setCurrentAction] = useState(null)
  const [wsAlert, setWsAlert] = useState(null)
  const [currentView, setCurrentView] = useState('dashboard') // 'dashboard', 'chat', 'check-in'
  const [currentWeather, setCurrentWeather] = useState(null)
  const [symptomTriage, setSymptomTriage] = useState(false)
  const [isPlannerMode, setIsPlannerMode] = useState(false)
  const chatEndRef = useRef(null)

  // Establish WebSocket connection for real-time push notifications
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/alerts`);
    
    ws.onopen = () => console.log('Connected to HeatShield Emergency WebSocket');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'emergency_alert') {
          setWsAlert(data);
          // Auto-dismiss after 15 seconds
          setTimeout(() => setWsAlert(null), 15000);
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };
    
    ws.onclose = () => console.log('WebSocket connection closed');
    
    return () => ws.close();
  }, []);

  // Request geolocation on mount, with a fallback
  useEffect(() => {
    const fetchDefaultMap = (lat, lng) => {
      axios.post(`${API_URL}/api/default-map`, { lat, lng })
        .then(res => {
          if (res.data.current_weather) setCurrentWeather(res.data.current_weather);
          if (res.data.uhi_geojson) setUhiGeojson(res.data.uhi_geojson);
          if (res.data.isochrone_geojson) setIsochroneGeojson(res.data.isochrone_geojson);
          if (res.data.markers && res.data.markers.length > 0) {
             setMarkers(prev => {
                const nonCooling = prev.filter(m => m.type !== 'cooling_spot');
                return [...nonCooling, ...res.data.markers];
             });
          }
        })
        .catch(err => console.error("Error fetching default map:", err));
    };

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setUserLocation(loc);
          setMarkers(prev => [...prev, { ...loc, label: "You are here", type: "user_location" }]);
          fetchDefaultMap(loc.lat, loc.lng);
        },
        (error) => {
          console.error("Error getting location: ", error);
          const fallbackLoc = { lat: 35.5024, lng: 11.0622 };
          setUserLocation(fallbackLoc);
          setMarkers(prev => [...prev, { ...fallbackLoc, label: "You are here", type: "user_location" }]);
          fetchDefaultMap(fallbackLoc.lat, fallbackLoc.lng);
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    } else {
      const fallbackLoc = { lat: 35.5024, lng: 11.0622 };
      setUserLocation(fallbackLoc);
      setMarkers(prev => [...prev, { ...fallbackLoc, label: "You are here", type: "user_location" }]);
      fetchDefaultMap(fallbackLoc.lat, fallbackLoc.lng);
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Poll for contacts when in check-in view
  useEffect(() => {
    let interval;
    if (currentView === 'check-in') {
      const fetchContacts = () => {
        axios.get(`${API_URL}/api/contacts`)
          .then(res => setContacts(res.data))
          .catch(err => console.error(err));
      };
      fetchContacts();
      interval = setInterval(fetchContacts, 3000);
    }
    return () => clearInterval(interval);
  }, [currentView]);

  const handleQuickAction = (actionText) => {
    setInput(actionText);
    setCurrentView('chat');
    submitMessage(actionText);
  }

  const resetChat = () => {
    setMessages([{ role: 'assistant', content: 'Hello! I am HeatShield, your urban heat wave safety assistant. Where are you located, and how can I help you stay safe today?' }]);
    setMarkers(userLocation ? [{ ...userLocation, label: "You are here", type: "user_location" }] : []);
    setUhiGeojson(null);
    setRouteGeojson(null);
    setIsochroneGeojson(null);
    setForecastData(null);
    setAqForecastData(null);
    setSafetyAdvice(null);
    setWorkRestGuidance(null);
    setInput('');
    setCurrentView('dashboard');
  }

  const submitMessage = async (userMessage) => {
    if (!userMessage.trim() || isLoading) return
    
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)
    setCurrentAction("Thinking...") // Initial action
    setForecastData(null) // Clear previous forecast chart on new request
    setAqForecastData(null) // Clear previous AQ chart on new request
    setSafetyAdvice(null) // Clear previous safety advice
    setWorkRestGuidance(null)
    setSymptomTriage(false)
    
    try {
      // Create history from the current state (before this message was added)
      // We skip the first message (the greeting)
      const history = messages.slice(1).map(m => ({ role: m.role, content: m.content }))

      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-API-Key': 'heatshield-demo-key'
        },
        body: JSON.stringify({
          message: userMessage,
          history: history,
          userLocation: userLocation
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown API error" }));
        throw new Error(errorData.detail || `HTTP Error ${response.status}`);
      }
      
      if (!response.body) throw new Error("No response body");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let done = false;
      let buffer = "";
      
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
            buffer += decoder.decode(value, { stream: true });
            
            // Split buffer by newlines to process complete JSON objects
            const parts = buffer.split('\n');
            // Keep the last part in the buffer if it's incomplete
            buffer = parts.pop();
            
            for (const part of parts) {
                if (!part.trim()) continue;
                
                try {
                    const data = JSON.parse(part);
                    
                    if (data.type === 'tool_call') {
                        // Map the tool name to a user-friendly action string
                        const actionMap = {
                            "geocode_location": "🔍 Geocoding location...",
                            "get_weather_and_heat_risk": "🌤️ Checking live weather & WHO risk levels...",
                            "get_air_quality": "💨 Checking air quality...",
                            "get_air_quality_forecast": "🔮 Predicting 5-day air quality...",
                            "find_cooling_spots": "🏖️ Searching OSM for nearby cooling spots...",
                            "get_heat_safety_advice": "📚 Consulting WHO safety guidelines...",
                            "get_heatwave_forecast": "📈 Generating 7-day drought & heat forecast...",
                            "query_emergency_protocols": "⚕️ Searching ChromaDB for medical protocols...",
                            "get_urban_heat_island_heatmap": "🗺️ Generating spatial UHI heatmap...",
                            "get_walking_route": "🚶 Calculating walking route...",
                            "generate_walkability_isochrone": "⏱️ Generating 15-minute radial walkability isochrone...",
                            "search_web_for_pdfs": "🌐 Searching DuckDuckGo for official PDFs...",
                            "ingest_emergency_document_url": "📥 Downloading and vectorizing PDF...",
                            "get_occupational_heat_guidance": "👷 Fetching OSHA/NIOSH work-rest cycles..."
                        };
                        setCurrentAction(actionMap[data.name] || `⚙️ Running ${data.name}...`);
                    } else if (data.type === 'final') {
                        // We got the final response
                        const { text, markers: newMarkers, forecast, aq_forecast, uhi_geojson, route_geojson, isochrone_geojson, safety_advice, work_rest_guidance, current_weather, symptom_triage } = data;
                        // Clean up lone hashes that the LLM might emit due to markdown prompt confusion
                        const cleanedText = (text || "").replace(/\n#\n/g, '\n### ').replace(/\n##\n/g, '\n### ');
                        if (cleanedText.trim().length > 0) {
                            setMessages(prev => [...prev, { role: 'assistant', content: cleanedText }]);
                        }
                        if (newMarkers && newMarkers.length > 0) setMarkers(newMarkers);
                        if (forecast) setForecastData(forecast);
                        if (aq_forecast) setAqForecastData(aq_forecast);
                        if (uhi_geojson) setUhiGeojson(uhi_geojson);
                        if (route_geojson) setRouteGeojson(route_geojson);
                        if (isochrone_geojson) setIsochroneGeojson(isochrone_geojson);
                        if (safety_advice) setSafetyAdvice(safety_advice);
                        if (work_rest_guidance) setWorkRestGuidance(work_rest_guidance);
                        if (current_weather) setCurrentWeather(current_weather);
                        if (symptom_triage) setSymptomTriage(true);
                        setCurrentAction(null);
                    }
                } catch (e) {
                    console.error("Failed to parse stream chunk", part, e);
                }
            }
        }
      }
      
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `⚠️ **Connection or Security Error:** ${error.message}` 
      }])
    } finally {
      setIsLoading(false)
      setCurrentAction(null)
    }
  }

  // Parses markdown headers and wraps sections into "Cards"
  const formatContent = (text) => {
    if (!text) return null;
    
    // Split by Markdown headers (h2 or h3)
    const sections = text.split(/(?=###? )/);
    
    return sections.map((section, idx) => {
      // Clean up stray hashes or empty sections
      if (section.trim() === '#' || section.trim() === '##' || section.trim() === '') return null;
      
      let isWarning = section.includes('Alert') || section.includes('Warning') || section.includes('EXTREME');
      let isWeather = section.includes('Weather') || section.includes('Temperature');
      let isSpots = section.includes('Cooling') || section.includes('Spots');
      
      let cardClass = "chat-card";
      if (isWarning) cardClass += " warning-card";
      if (isWeather) cardClass += " weather-card";
      if (isSpots) cardClass += " spots-card";

      // Enhanced markdown parsing for standard prose
      const processMarkdown = (str) => {
          return str
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/(?<!\*)\*(?!\*)(.*?)\*/g, '<em>$1</em>') // Italic (single asterisk, but not double)
            .replace(/\n\*/g, '<br/>•') // Fix bullet points starting with *
            .replace(/\n-/g, '<br/>•')  // Fix bullet points starting with -
            .replace(/\n/g, '<br/>');
      };
      
      // If it doesn't start with a header, it's just normal text
      if (!section.startsWith('#')) {
         return (
           <div key={idx} className="chat-normal-text" dangerouslySetInnerHTML={{ 
             __html: processMarkdown(section)
           }} />
         );
      }
      
      // Clean up the text for the card
      const lines = section.split('\n');
      const header = lines[0].replace(/###? /, '');
      const body = lines.slice(1).join('\n');
      
      return (
        <div key={idx} className={cardClass}>
          <h4>{header}</h4>
          <div className="card-body" dangerouslySetInnerHTML={{ __html: processMarkdown(body) }} />
        </div>
      );
    });
  }

  return (
    <div className="app-container">
      <AlertBanner alert={wsAlert} onClose={() => setWsAlert(null)} />
      {/* Background Map */}
      <div className="map-container">
        <MapContainer center={[49.0068, 8.4034]} zoom={4} style={{ height: '100%', width: '100%' }} zoomControl={false}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          <MapController markers={markers} />
          {markers.map((marker, idx) => (
            <Marker key={idx} position={[marker.lat, marker.lng]}>
              <Popup>
                {marker.type === 'cooling_spot' ? (
                  <div style={{ padding: '2px', minWidth: '150px' }}>
                    <h3 style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#1e293b' }}>{marker.label}</h3>
                    <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#64748b', textTransform: 'capitalize' }}>
                      Type: {marker.tags?.amenity || marker.tags?.leisure || 'Cooling Shelter'}
                    </p>
                    {marker.dist && (
                      <p style={{ margin: 0, fontSize: '12px', fontWeight: 'bold', color: '#3b82f6' }}>
                        {marker.dist} meters away (approx)
                      </p>
                    )}
                  </div>
                ) : (
                  marker.label || 'Location'
                )}
              </Popup>
            </Marker>
          ))}
          {uhiGeojson && (
            <Pane name="heat-pane" className="heat-pane-blur" style={{ zIndex: 450 }}>
              <GeoJSON 
                key={"uhi" + Date.now()} 
                data={uhiGeojson} 
                style={(feature) => ({
                  color: 'transparent',
                  fillColor: feature.properties?.color || '#ef4444',
                  weight: 0,
                  fillOpacity: 1.0
                })}
              />
            </Pane>
          )}
          {routeGeojson && (
            <GeoJSON 
              key={"route" + Date.now()} 
              data={routeGeojson} 
              style={(feature) => ({ color: feature.properties?.color || '#3b82f6', weight: 5, fillOpacity: 0 })}
            />
          )}
          {isochroneGeojson && (
            <GeoJSON 
              key={"iso" + Date.now()} 
              data={isochroneGeojson} 
              style={{ color: '#10b981', fillColor: '#10b981', weight: 2, fillOpacity: 0.2 }}
            />
          )}
        </MapContainer>
      
      {/* Map Overlays: Legend & Route Callout */}
      <div className="map-legend">
        <span><div className="legend-dot" style={{background: '#ef4444'}}></div> Extreme</span>
        <span><div className="legend-dot" style={{background: '#f59e0b'}}></div> Caution</span>
        <span><div className="legend-dot" style={{background: '#22c55e'}}></div> Cool spot</span>
      </div>
      
      {currentWeather?.heat_risk_level === 'EXTREME' && routeGeojson && (
        <div className="route-safety-callout">
           <MapPin size={20} />
           <span>Nearest cool spot is outside the hottest zone, but longer walking routes cross an extreme-heat area right now. Proceed with caution.</span>
        </div>
      )}
      
      {routeGeojson?.features?.[0]?.properties?.optimized && (
        <div className="route-safety-callout" style={{ bottom: 'auto', top: '70px', background: '#ecfdf5', color: '#065f46', borderColor: '#34d399', zIndex: 900 }}>
           <MapPin size={20} />
           <span>This route is <strong>Shade-Optimized</strong>. The agent intersected potential paths with the UHI heatmap to minimize heat exposure.</span>
        </div>
      )}
      
      {/* Floating Forecast Widgets over the map! */}
      <div className="forecast-overlay-container">
          {forecastData && (
            <div className="forecast-overlay">
               <ForecastWidget data={forecastData} onClose={() => setForecastData(null)} />
            </div>
          )}
          {aqForecastData && (
            <div className="forecast-overlay aq-overlay">
               <AQForecastWidget data={aqForecastData} onClose={() => setAqForecastData(null)} />
            </div>
          )}
          {safetyAdvice && (
            <div className="forecast-overlay">
               <SafetyAdviceWidget advice={safetyAdvice} onClose={() => setSafetyAdvice(null)} />
            </div>
          )}
        </div>
      </div>

      {/* Floating Glassmorphism Chat Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.5rem' }}>🛡️</span>
            <h1>HeatShield</h1>
          </div>
          <div style={{ display: 'flex', gap: '16px', color: '#94a3b8' }}>
            <Briefcase 
              size={24} 
              style={{ cursor: 'pointer', color: isPlannerMode ? '#3b82f6' : '#94a3b8' }} 
              onClick={() => setIsPlannerMode(!isPlannerMode)} 
              title="Toggle Planner Mode"
            />
            <User size={24} style={{ cursor: 'pointer', color: !isPlannerMode ? '#3b82f6' : '#94a3b8' }} />
            <MoreHorizontal size={24} style={{ cursor: 'pointer' }} />
          </div>
        </div>
        
        {currentView === 'dashboard' && (
          isPlannerMode ? <PlannerDashboard /> : (
          <div className="zero-state-dashboard citizen-dashboard">
            {/* Hero Alert Banner */}
            <div className="hero-alert-banner">
              <div className="alert-top">
                <span className="location-text">Right now near you</span>
                <Sun size={28} color="#fca5a5" />
              </div>
              <h2>{currentWeather ? `${currentWeather.heat_risk_level} heat — ${currentWeather.feels_like_celsius}°C` : 'Extreme heat — 41°C'}</h2>
              <p>Avoid going outside 1–5pm. Drink water now.</p>
            </div>
            
            {/* 2x2 Action Grid */}
            <div className="action-grid">
              <button className="action-btn btn-red" onClick={() => handleQuickAction("I don't feel well. Please ask me for my symptoms to triage heat exhaustion vs heat stroke.")}>
                <PlusSquare size={28} />
                <span>I don't feel well</span>
              </button>
              <button className="action-btn btn-gray" onClick={() => handleQuickAction("Find a cool place nearby and give me a safe walking route to it.")}>
                <MapPin size={28} />
                <span>Find cool place nearby</span>
              </button>
              <button className="action-btn btn-gray" onClick={() => setCurrentView('check-in')}>
                <Heart size={28} />
                <span>Check on someone</span>
              </button>
              <button className="action-btn btn-gray" onClick={() => handleQuickAction("Is it safe to work outside right now? What are the CDC work/rest cycles for 41C?")}>
                <Briefcase size={28} />
                <span>Safe to work outside?</span>
              </button>
            </div>

            {/* Timeline */}
            <div className="safe-windows-section">
              <h4>Today's safe windows</h4>
              <div className="safe-windows-row">
                <div className="time-block block-safe">
                  <span className="time">6–9am</span>
                  <span className="status">Safe</span>
                </div>
                <div className="time-block block-avoid">
                  <span className="time">1–5pm</span>
                  <span className="status">Avoid</span>
                </div>
                <div className="time-block block-caution">
                  <span className="time">7–9pm</span>
                  <span className="status">Caution</span>
                </div>
              </div>
            </div>
          </div>
          )
        )}

        {currentView === 'check-in' && (
          <div className="check-in-view">
            <div className="check-in-header">
              <button className="back-btn" onClick={() => setCurrentView('dashboard')}>←</button>
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
        )}

        {currentView === 'chat' && (
          <>
            <div className="chat-header-actions" style={{ padding: '20px 20px 0', display: 'flex', justifyContent: 'flex-start' }}>
              <button 
                className="test-siren-btn-small" 
                onClick={resetChat}
              >
                🔙 Back to Dashboard
              </button>
            </div>
            <div className="chat-history">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  <div className="message-content">
                    {msg.role === 'user' ? msg.content : formatContent(msg.content)}
                  </div>
                </div>
              ))}
            {/* Structured Symptom Triage Card */}
            {symptomTriage && (
               <div className="message assistant">
                  <div className="message-content" style={{ background: 'transparent', padding: 0, border: 'none' }}>
                     <SymptomTriageCard 
                        onSubmit={(symptoms) => submitMessage(`I am experiencing: ${symptoms.join(', ')}. What should I do?`)} 
                        onEmergency={(symptoms) => submitMessage(`EMERGENCY: I am calling emergency services! My symptoms are: ${symptoms.join(', ')}`)} 
                     />
                  </div>
               </div>
            )}
            
            {/* Structured Occupational Heat Card */}
              {workRestGuidance && (
                <div className="message assistant">
                  <div className="message-content" style={{ background: 'transparent', padding: 0, border: 'none' }}>
                    <div className="work-rest-card">
                      <div className="wrc-header">
                        <div className="wrc-title">
                          <h3>Feels like {currentWeather ? currentWeather.feels_like_celsius : workRestGuidance.feels_like}°C</h3>
                          <span className={`wrc-badge badge-${(currentWeather?.heat_risk_level || workRestGuidance.risk_level).toLowerCase()}`}>{currentWeather?.heat_risk_level || workRestGuidance.risk_level}</span>
                        </div>
                        <p>Actual {currentWeather ? currentWeather.temperature_celsius : workRestGuidance.actual}°C · {workRestGuidance.humidity_level} humidity</p>
                      </div>
                      
                      <div className="wrc-body">
                        <h4>Work/rest cycle at this heat level</h4>
                        <table className="wrc-table">
                          <thead>
                            <tr>
                              <th>Workload</th>
                              <th>Work</th>
                              <th>Rest</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td style={{ fontWeight: '600' }}>Light</td>
                              <td>{workRestGuidance.schedule.light.work}</td>
                              <td>{workRestGuidance.schedule.light.rest}</td>
                            </tr>
                            <tr className={workRestGuidance.risk_level === 'Extreme' || workRestGuidance.risk_level === 'High' ? 'row-warning' : ''}>
                              <td style={{ fontWeight: '600' }}>Moderate</td>
                              <td>{workRestGuidance.schedule.moderate.work}</td>
                              <td>{workRestGuidance.schedule.moderate.rest}</td>
                            </tr>
                            <tr className={workRestGuidance.risk_level === 'Extreme' ? 'row-danger' : (workRestGuidance.risk_level === 'High' ? 'row-warning' : '')}>
                              <td style={{ fontWeight: '600' }}>Heavy</td>
                              <td>{workRestGuidance.schedule.heavy.work}</td>
                              <td>{workRestGuidance.schedule.heavy.rest}</td>
                            </tr>
                          </tbody>
                        </table>
                        
                        <div className="wrc-info">
                          <span style={{ fontSize: '1.2rem' }}>ⓘ</span>
                          <p>Based on NIOSH heat-stress guidance for {workRestGuidance.humidity_level} humidity. Heavy exertion outdoors is not recommended at this heat level.</p>
                        </div>
                        
                        <button className="wrc-action-btn">
                          Alert supervisor to pause work
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {isLoading && (
                <div className="message assistant">
                  <div className="action-badge" style={{ padding: '8px 12px', background: '#3b82f640', color: '#60a5fa', borderRadius: '8px', fontSize: '0.9rem', display: 'inline-block', fontWeight: '500', border: '1px solid #3b82f680' }}>
                    {currentAction || "Thinking..."}
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </>
        )}
        {(currentView === 'dashboard' || currentView === 'chat') && (
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
        )}
      </div>
    </div>
  )
}

export default App
