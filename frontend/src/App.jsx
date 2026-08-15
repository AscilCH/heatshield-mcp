import React, { useState, useRef, useEffect, Fragment } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap, GeoJSON, Pane } from 'react-leaflet'
import ClusterMarkers from './components/MarkerClusterGroup'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Shield, Thermometer, Wind, Droplets, MapPin, Search, AlertTriangle, CheckCircle2, User, Target, Navigation, ArrowRight, ArrowLeft, Sun, Info, Briefcase, PlusSquare, Heart, MoreHorizontal, Phone } from 'lucide-react'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import DOMPurify from 'dompurify';
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
function MapController({ markers, routeGeojson, uhiGeojson, isochroneGeojson, heatDomeGeojson, canvasCamera, canvasLayers }) {
  const map = useMap()
  
  useEffect(() => {
    // 0. Top Priority: Explicit Canvas Camera
    if (canvasCamera && canvasCamera.lat && canvasCamera.lng) {
      setTimeout(() => {
        map.invalidateSize();
        map.flyTo([canvasCamera.lat, canvasCamera.lng], canvasCamera.zoom || 12, { duration: 1.5 });
      }, 100);
      return;
    }

    // 1. High Priority: Heat Dome Footprint
    if (heatDomeGeojson && heatDomeGeojson.features && heatDomeGeojson.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(heatDomeGeojson);
        const b = geoJsonLayer.getBounds();
        if (b.isValid()) {
          setTimeout(() => {
            map.invalidateSize();
            map.flyToBounds(b, { padding: [50, 50], maxZoom: 7, duration: 1.5 });
          }, 100);
          return;
        }
      } catch(e) {
        console.error("Error flying to heat dome bounds:", e);
      }
    }

    // 2. High Priority: Walking Route
    if (routeGeojson && routeGeojson.features && routeGeojson.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(routeGeojson);
        const b = geoJsonLayer.getBounds();
        if (b.isValid()) {
          setTimeout(() => {
            map.invalidateSize();
            map.flyToBounds(b, { padding: [50, 50], maxZoom: 15, duration: 1.5 });
          }, 100);
          return;
        }
      } catch(e) {
        console.error("Error flying to route bounds:", e);
      }
    }

    // 3. High Priority: UHI Heatmap
    if (uhiGeojson && uhiGeojson.features && uhiGeojson.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(uhiGeojson);
        const b = geoJsonLayer.getBounds();
        if (b.isValid()) {
          setTimeout(() => {
            map.invalidateSize();
            map.flyToBounds(b, { padding: [50, 50], maxZoom: 14, duration: 1.5 });
          }, 100);
          return;
        }
      } catch(e) {
        console.error("Error flying to UHI bounds:", e);
      }
    }

    // 4. High Priority: Walkability Isochrone
    if (isochroneGeojson && isochroneGeojson.features && isochroneGeojson.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(isochroneGeojson);
        const b = geoJsonLayer.getBounds();
        if (b.isValid()) {
          setTimeout(() => {
            map.invalidateSize();
            map.flyToBounds(b, { padding: [50, 50], maxZoom: 14, duration: 1.5 });
          }, 100);
          return;
        }
      } catch(e) {
        console.error("Error flying to isochrone bounds:", e);
      }
    }

    // 5. Markers: If AI Inspection Point / Target exists, fly to it; otherwise fly to user location
    if (markers && markers.length > 0) {
      const nonUserMarkers = markers.filter(m => m.type !== 'user_location');
      const targetMarkers = nonUserMarkers.length > 0 ? nonUserMarkers : markers;
      
      let bounds = new L.LatLngBounds();
      let maxDist = 0;
      for (let i = 0; i < targetMarkers.length; i++) {
        for (let j = i + 1; j < targetMarkers.length; j++) {
          const d = Math.hypot(targetMarkers[i].lat - targetMarkers[j].lat, targetMarkers[i].lng - targetMarkers[j].lng);
          if (d > maxDist) maxDist = d;
        }
        if (targetMarkers[i].lat && targetMarkers[i].lng) {
          bounds.extend([targetMarkers[i].lat, targetMarkers[i].lng]);
        }
      }
      
      if (bounds.isValid()) {
        setTimeout(() => {
          map.invalidateSize();
          if (maxDist > 15 || targetMarkers.length === 1) {
            const primary = targetMarkers[targetMarkers.length - 1];
            map.flyTo([primary.lat, primary.lng], 11, { duration: 1.5 });
          } else {
            map.flyToBounds(bounds, { padding: [50, 50], maxZoom: 14, duration: 1.5 });
          }
        }, 100);
      }
    }
  }, [markers, routeGeojson, uhiGeojson, isochroneGeojson, heatDomeGeojson, canvasCamera, canvasLayers, map])

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
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="name" stroke="#a8a29e" fontSize={12} />
            <YAxis yAxisId="left" stroke="#a8a29e" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} tickFormatter={(value) => value.toFixed(1)} />
            <YAxis yAxisId="right" orientation="right" stroke="#a8a29e" fontSize={12} domain={[0, 100]} tickFormatter={(value) => Math.round(value)} label={{ value: 'Moisture %', angle: -90, position: 'insideRight', fill: '#a8a29e', fontSize: 10 }} />
            <Tooltip contentStyle={{ backgroundColor: 'rgba(38, 32, 29, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} formatter={(value) => typeof value === 'number' ? value.toFixed(1) : value} />
            <Line yAxisId="left" type="monotone" dataKey="Temp" stroke="#FF5A3C" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Max Temp (°C)" />
            <Line yAxisId="left" type="monotone" dataKey="FeelsLike" stroke="#FFB020" strokeWidth={2} name="Feels Like (°C)" />
            <Line yAxisId="right" type="monotone" dataKey="Moisture" stroke="#94a3b8" strokeWidth={2} strokeDasharray="4 4" name="Soil Moisture (%)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// Chart Component for 7-Day Predictive WBGT Curve
function WBGTForecastWidget({ data, onClose }) {
  if (!data || data.length === 0 || !data[0].wbgt_celsius) return null;
  
  const chartData = data.map(d => ({
    name: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
    WBGT: d.wbgt_celsius
  }));

  return (
    <div className="forecast-widget">
      <div className="widget-header">
        <h3>7-Day Predictive WBGT (Outdoor Labor)</h3>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div style={{ height: '220px', width: '100%', marginTop: '10px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="name" stroke="#a8a29e" fontSize={12} />
            <YAxis stroke="#a8a29e" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} tickFormatter={(value) => value.toFixed(1)} />
            <Tooltip contentStyle={{ backgroundColor: 'rgba(38, 32, 29, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} formatter={(value) => typeof value === 'number' ? value.toFixed(1) : value} />
            
            <ReferenceLine y={28} stroke="#FFB020" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Moderate Risk (28°C)', fill: '#FFB020', fontSize: 10 }} />
            <ReferenceLine y={30} stroke="#FF5A3C" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'High Risk (30°C)', fill: '#FF5A3C', fontSize: 10 }} />
            <ReferenceLine y={31.5} stroke="#b91c1c" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Halt Heavy Labor (31.5°C)', fill: '#b91c1c', fontSize: 10 }} />
            
            <Line type="monotone" dataKey="WBGT" stroke="#2ECF8E" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Peak WBGT (°C)" />
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
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="name" stroke="#a8a29e" fontSize={12} />
            <YAxis stroke="#a8a29e" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: 'rgba(38, 32, 29, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} formatter={(value) => typeof value === 'number' ? value.toFixed(1) : value} />
            <Line type="monotone" dataKey="PM10" stroke="#FFB020" strokeWidth={3} dot={{ r: 4 }} name="PM10 (Dust)" />
            <Line type="monotone" dataKey="PM25" stroke="#FF5A3C" strokeWidth={3} dot={{ r: 4 }} name="PM2.5 (Smoke)" />
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
  const orchestratorCache = useRef({})
  const [orchestratorStatus, setOrchestratorStatus] = useState({})

  useEffect(() => {
    if (displayedStreamingMessage.length < streamingMessage.length) {
      const timeout = setTimeout(() => {
        setDisplayedStreamingMessage(streamingMessage.slice(0, displayedStreamingMessage.length + 1));
      }, 15);
      return () => clearTimeout(timeout);
    }
  }, [streamingMessage, displayedStreamingMessage]);
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

    const handleGeolocationFallback = () => {
      console.warn("Geolocation unavailable or denied: Location remains unselected.");
      setUserLocation(null);
      setMarkers([]);
    };

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const loc = { lat: position.coords.latitude, lng: position.coords.longitude };
          setUserLocation(loc);
          setMarkers([{ ...loc, label: "You are here", type: "user_location" }]);
          fetchDefaultMap(loc.lat, loc.lng);
        },
        (error) => {
          console.warn("GPS location permission not granted, leaving location unassigned: ", error);
          handleGeolocationFallback();
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    } else {
      handleGeolocationFallback();
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
    setHeatDomeGeojson(null);
    setRouteGeojson(null);
    setIsochroneGeojson(null);
    setForecastData(null);
    setAqForecastData(null);
    setSafetyAdvice(null);
    setWorkRestGuidance(null);
    setSymptomTriage(false);
    setMedicalTriageAdvice(null);
    orchestratorCache.current = {};
    setOrchestratorStatus({});
    setStreamingMessage("");
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
    setWorkRestGuidance(null);
    setSymptomTriage(false);
    setMedicalTriageAdvice(null);
    orchestratorCache.current = {};
    setOrchestratorStatus({});
    
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
          latitude: userLocation?.lat,
          longitude: userLocation?.lng
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
                    
                    if (data.type === 'chunk') {
                        setStreamingMessage(prev => prev + data.text);
                    } else if (data.type === 'clear_chunk') {
                        setStreamingMessage("");
                        setDisplayedStreamingMessage("");
                    } else if (data.type === 'trace') {
                        console.log(`%c${data.message}`, 'color: #3b82f6; font-weight: bold;');
                    } else if (data.type === 'tool_call') {
                        setStreamingMessage("");
                        setDisplayedStreamingMessage("");
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
                            "navigate_to_nearest_cooling_spot": "🧭 Finding nearest safe spot & plotting route...",
                            "generate_walkability_isochrone": "⏱️ Generating radial walkability isochrone...",
                            "search_web_for_pdfs": "🌐 Searching DuckDuckGo for official PDFs...",
                            "ingest_emergency_document_url": "📥 Downloading and vectorizing PDF...",
                            "get_occupational_heat_guidance": "👷 Fetching OSHA/NIOSH work-rest cycles..."
                        };
                        setCurrentAction(actionMap[data.name] || `⚙️ Running ${data.name}...`);
                    } else if (data.type === 'partial_map_update') {
                        setOrchestratorStatus(prev => ({ ...prev, [data.task_id]: { status: data.status, error: data.error } }));
                        
                        if (data.status === 'success' && data.data) {
                            try {
                                const parsed = JSON.parse(data.data);
                                if (parsed.heatmap_geojson) orchestratorCache.current[data.task_id] = { type: 'uhi', features: parsed.heatmap_geojson.features || [] };
                                if (parsed.isochrone_geojson) orchestratorCache.current[data.task_id] = { type: 'isochrone', features: parsed.isochrone_geojson.features || [] };
                                if (parsed.elements) orchestratorCache.current[data.task_id] = { type: 'markers', elements: parsed.elements || [] };
                                
                                const allUhi = [];
                                const allIso = [];
                                const allMarks = [];
                                
                                Object.values(orchestratorCache.current).forEach(c => {
                                    if (c.type === 'uhi' && c.features) allUhi.push(...c.features);
                                    if (c.type === 'isochrone' && c.features) allIso.push(...c.features);
                                    if (c.type === 'markers' && c.elements) {
                                        const m = c.elements.slice(0, 20).filter(el => el.lat && el.lon).map(el => ({
                                            type: "cooling_spot", lat: el.lat, lng: el.lon,
                                            label: el.tags?.name || el.tags?.amenity || el.tags?.leisure || "Cooling Spot",
                                            tags: el.tags, dist: el.distance_m
                                        }));
                                        allMarks.push(...m);
                                    }
                                });
                                
                                if (allUhi.length > 0) setUhiGeojson({ type: "FeatureCollection", features: allUhi });
                                if (allIso.length > 0) setIsochroneGeojson({ type: "FeatureCollection", features: allIso });
                                if (allMarks.length > 0) {
                                    setMarkers(prev => {
                                        const nonCooling = prev.filter(m => m.type !== 'cooling_spot');
                                        return [...nonCooling, ...allMarks];
                                    });
                                }
                            } catch(e) {}
                        }
                    } else if (data.type === 'final') {
                        // We got the final response
                        const { text, markers: newMarkers, forecast, aq_forecast, uhi_geojson, heat_dome_geojson, route_geojson, isochrone_geojson, safety_advice, work_rest_guidance, medical_triage_advice, current_weather, symptom_triage } = data;
                        // Clean up lone hashes that the LLM might emit due to markdown prompt confusion
                        const cleanedText = (text || "").replace(/\n#\n/g, '\n### ').replace(/\n##\n/g, '\n### ');
                        if (cleanedText.trim().length > 0) {
                            setMessages(prev => [...prev, { role: 'assistant', content: cleanedText }]);
                        }
                        setStreamingMessage("");
                        if (forecast !== undefined) {
                            setForecastData(forecast);
                            setShowWbgtForecast(true);
                        }
                        if (aq_forecast !== undefined) setAqForecastData(aq_forecast);
                        if (uhi_geojson !== undefined) setUhiGeojson(uhi_geojson);
                        if (heat_dome_geojson !== undefined) setHeatDomeGeojson(heat_dome_geojson);
                        if (route_geojson !== undefined) setRouteGeojson(route_geojson);
                        if (isochrone_geojson !== undefined) setIsochroneGeojson(isochrone_geojson);
                        if (safety_advice !== undefined) setSafetyAdvice(safety_advice);
                        if (work_rest_guidance !== undefined) setWorkRestGuidance(work_rest_guidance);
                        if (medical_triage_advice !== undefined) setMedicalTriageAdvice(medical_triage_advice);
                        
                        if (data.current_weather) {
                          const updatedWeather = { ...data.current_weather };
                          // Override weather location with geocoded name if available, else fallback to search query
                          if (data.geocoded_location_name) {
                            updatedWeather.location = data.geocoded_location_name;
                          } else if (!updatedWeather.location) {
                            updatedWeather.location = input;
                          }
                          setCurrentWeather(updatedWeather);
                        } else if (data.geocoded_location_name) {
                          // If weather wasn't fetched, but we got a geocoded location, update the location string
                          setCurrentWeather(prev => prev ? { ...prev, location: data.geocoded_location_name } : { location: data.geocoded_location_name });
                        }
                        
                        if (data.geocoded_location_name) {
                          setUserLocation(prev => ({ ...prev, name: data.geocoded_location_name }));
                        } else if (data.current_weather && data.current_weather.location) {
                          setUserLocation(prev => ({ ...prev, name: data.current_weather.location }));
                        }
                        
                        if (symptom_triage) setSymptomTriage(true);
                        if (data.canvas_layers && data.canvas_layers.length > 0) {
                          setCanvasLayers(prev => [...prev, ...data.canvas_layers]);
                        }
                        if (data.canvas_chart) setCanvasChartData(data.canvas_chart);
                        if (data.canvas_comparison) setCanvasComparisonData(data.canvas_comparison);
                        if (data.canvas_camera) setCanvasCamera(data.canvas_camera);
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

  // Function to create color-coded map pins
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
    if (marker.type === 'cooling_spot') return '#2ECF8E'; // Risk Cool (Teal)
    if (marker.tags?.risk === 'EXTREME') return '#FF5A3C'; // Risk Extreme (Red)
    if (marker.tags?.risk === 'CAUTION') return '#FFB020'; // Risk Caution (Amber)
    return '#FF5A3C'; // Default Ember
  };

  // Parses markdown headers and wraps sections into "Cards"
  const formatContent = (text) => {
    if (!text) return null;
    
    const sections = text.split(/(?=###? )/);
    return sections.map((section, idx) => {
      if (section.trim() === '#' || section.trim() === '##' || section.trim() === '') return null;
      
      const processMarkdown = (str) => {
          const lines = str.split('\n');
          let inTable = false;
          let tableHeaders = [];
          let tableRows = [];
          let outputLines = [];

          const renderCurrentTable = () => {
              if (tableHeaders.length === 0 && tableRows.length === 0) return '';
              const headers = tableHeaders.length > 0 ? tableHeaders : (tableRows.length > 0 ? tableRows.shift() : []);
              let tHtml = '<div class="table-responsive"><table class="chat-md-table"><thead><tr>';
              headers.forEach(h => { tHtml += `<th>${h}</th>`; });
              tHtml += '</tr></thead><tbody>';
              tableRows.forEach(row => {
                  tHtml += '<tr>';
                  for (let cIdx = 0; cIdx < headers.length; cIdx++) {
                      tHtml += `<td>${row[cIdx] !== undefined ? row[cIdx] : ''}</td>`;
                  }
                  tHtml += '</tr>';
              });
              tHtml += '</tbody></table></div>';
              tableHeaders = [];
              tableRows = [];
              inTable = false;
              return tHtml;
          };

          for (let i = 0; i < lines.length; i++) {
              const line = lines[i].trim();
              
              if (/^\|?[-:\s|]+\|?$/.test(line) && line.includes('-') && (line.includes('|') || line.includes(':'))) {
                  inTable = true;
                  continue;
              }
              
              if (line.includes('|')) {
                  const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => {
                      if ((idx === 0 || idx === arr.length - 1) && c === '') return false;
                      return true;
                  });
                  if (cells.length >= 2) {
                      if (!inTable && tableHeaders.length === 0) {
                          tableHeaders = cells;
                      } else {
                          tableRows.push(cells);
                      }
                      inTable = true;
                      continue;
                  }
              }
              
              if (inTable || tableHeaders.length > 0 || tableRows.length > 0) {
                  outputLines.push(renderCurrentTable());
              }
              outputLines.push(line);
          }
          
          if (inTable || tableHeaders.length > 0 || tableRows.length > 0) {
              outputLines.push(renderCurrentTable());
          }

          let html = outputLines.join('\n')
            .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-markdown-link">🔗 $1 ↗</a>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/(?<!\*)\*(?!\*)(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\*/g, '<br/> • ')
            .replace(/\n-/g, '<br/> • ')
            .replace(/\n/g, '<br/>');
          return DOMPurify.sanitize(html, { ADD_ATTR: ['target', 'rel'] });
      };
      
      if (!section.startsWith('#')) {
         return (
           <div key={idx} className="chat-normal-text" dangerouslySetInnerHTML={{ 
             __html: processMarkdown(section)
           }} />
         );
      }
      
      const lines = section.split('\n');
      const header = lines[0].replace(/###? /, '');
      const body = lines.slice(1).join('\n');
      
      return (
        <div key={idx} className="chat-card">
          <h4>{header}</h4>
          <div className="card-body" dangerouslySetInnerHTML={{ __html: processMarkdown(body) }} />
        </div>
      );
    });
  }

  const getRiskColorClass = (riskLevel) => {
    if (!riskLevel) return 'neutral';
    switch (riskLevel.toUpperCase()) {
      case 'EXTREME': return 'risk-extreme';
      case 'HIGH': return 'risk-high';
      case 'MODERATE': return 'risk-moderate';
      case 'LOW': return 'risk-low';
      default: return 'neutral';
    }
  };

  const getDynamicWindow = (timeKey, fallbackTitle) => {
    if (currentWeather && currentWeather.safe_windows && currentWeather.safe_windows[timeKey]) {
      const win = currentWeather.safe_windows[timeKey];
      return {
        title: fallbackTitle,
        time: win.time,
        status: win.status,
        class: `block-${win.status.toLowerCase()}` // block-safe, block-avoid, block-caution
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
      <AlertBanner alert={wsAlert} onClose={() => setWsAlert(null)} />
      {/* Background Map */}
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
            style={{
              position: 'absolute',
              bottom: '30px',
              left: '30px',
              zIndex: 1000,
              background: 'rgba(38, 32, 29, 0.9)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#f8fafc',
              padding: '10px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              boxShadow: '0 8px 16px rgba(0,0,0,0.5)',
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(60, 50, 45, 0.9)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'rgba(38, 32, 29, 0.9)'}
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
                key={"heatDome_" + (heatDomeGeojson?.features?.length || 0) + "_" + JSON.stringify(heatDomeGeojson?.features?.[0]?.geometry?.coordinates?.[0]?.[0] || "")} 
                data={heatDomeGeojson} 
                style={(feature) => ({
                  color: '#ff1744',
                  fillColor: '#f43f5e',
                  weight: 3.5,
                  dashArray: '8, 8',
                  fillOpacity: 0.35
                })}
                onEachFeature={(feature, layer) => {
                  layer.bindPopup("<div style='color:#1e293b; font-family:sans-serif; padding:4px;'><strong>🔥 500hPa Blocking High (Heat Dome)</strong><br/><span style='font-size:12px; color:#475569;'>Persistent upper-atmospheric ridge trapping extreme surface heat for 3+ consecutive days.</span></div>");
                }}
              />
            </Pane>
          )}
          {uhiGeojson && (
            <Pane name="heat-pane" className="heat-pane-blur" style={{ zIndex: 450 }}>
              <GeoJSON 
                key={"uhi_" + (uhiGeojson?.features?.length || 0) + "_" + JSON.stringify(uhiGeojson?.features?.[0]?.geometry?.coordinates?.[0]?.[0] || "")} 
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
          {routeGeojson && routeGeojson.features?.length > 0 && (
            <>
              <GeoJSON 
                key={"route_" + (routeGeojson?.features?.length || 0) + "_" + (routeGeojson?.features?.[0]?.geometry?.coordinates?.length || 0)} 
                data={routeGeojson} 
                style={(feature) => ({ color: feature.properties?.color || '#2ECF8E', weight: 5, fillOpacity: 0 })}
              />
              {routeGeojson.features.map((feat, fIdx) => {
                const coords = feat?.geometry?.coordinates;
                if (!coords || coords.length < 2) return null;
                return (
                  <React.Fragment key={"route_markers_" + fIdx}>
                    <Marker position={[coords[0][1], coords[0][0]]} icon={createCustomIcon('#2ECF8E')} />
                    <Marker position={[coords[coords.length - 1][1], coords[coords.length - 1][0]]} icon={createCustomIcon('#2ECF8E')} />
                  </React.Fragment>
                );
              })}
            </>
          )}
          {isochroneGeojson && (
            <GeoJSON 
              key={"iso_" + (isochroneGeojson?.features?.length || 0) + "_" + (isochroneGeojson?.features?.[0]?.geometry?.coordinates?.length || 0)} 
              data={isochroneGeojson} 
              style={(feature) => ({
                color: feature.properties?.color || '#10b981',
                fillColor: feature.properties?.fillColor || '#10b981',
                weight: 2,
                fillOpacity: feature.properties?.fillOpacity ?? 0.35
              })}
            />
          )}
          {/* Generic Dynamic Canvas Vector Layers */}
          {canvasLayers && canvasLayers.map((layer, lIdx) => {
            if (!layer.geojson) return null;
            return (
              <GeoJSON
                key={"canvas_layer_" + (layer.layer_id || lIdx) + "_" + JSON.stringify(layer.style || {})}
                data={layer.geojson}
                style={(feature) => ({
                  color: layer.style?.color || '#ef4444',
                  fillColor: layer.style?.fillColor || '#ef4444',
                  fillOpacity: layer.style?.fillOpacity !== undefined ? layer.style.fillOpacity : 0.35,
                  weight: layer.style?.weight || 3
                })}
                onEachFeature={(feature, l) => {
                  if (layer.popup_html) {
                    l.bindPopup(`<div style="color:#1e293b; font-family:sans-serif; padding:4px;">${DOMPurify.sanitize(layer.popup_html)}</div>`);
                  } else if (layer.label) {
                    l.bindPopup(`<div style="color:#1e293b; font-family:sans-serif; padding:4px;"><strong>${DOMPurify.sanitize(layer.label)}</strong></div>`);
                  }
                }}
              />
            );
          })}
        </MapContainer>
      
      {/* Map Overlays: Legend & Route Callout */}
      <div className="map-legend">
        <span><div className="legend-dot" style={{background: '#E63946'}}></div> Extreme</span>
        <span><div className="legend-dot" style={{background: '#F5A623'}}></div> Caution</span>
        <span><div className="legend-dot" style={{background: '#3ECF8E'}}></div> Cool spot</span>
        <span><div className="legend-dot" style={{background: '#10B981'}}></div> Natural cool zone</span>
      </div>
      
      {/* Floating Route Safety Alert Banner */}
      {routeGeojson && routeGeojson.features?.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          background: 'rgba(30, 20, 25, 0.88)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(244, 63, 94, 0.45)',
          borderLeft: '5px solid #f43f5e',
          borderRadius: '14px',
          padding: '14px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          boxShadow: '0 12px 36px rgba(0,0,0,0.65)',
          maxWidth: '580px',
          pointerEvents: 'auto',
          animation: 'slideIn 0.4s ease'
        }}>
          <AlertTriangle size={24} color="#f43f5e" style={{ flexShrink: 0 }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <div style={{ color: '#fff', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🚨 Route Thermal Alert</span>
              <span style={{ 
                background: 'rgba(244, 63, 94, 0.2)', 
                color: '#fb7185', 
                fontSize: '11px', 
                padding: '2px 8px', 
                borderRadius: '12px',
                border: '1px solid rgba(244, 63, 94, 0.3)'
              }}>
                {routeGeojson.features[0]?.properties?.distance_km || ((routeGeojson.features[0]?.properties?.distance_m || 16200) / 1000).toFixed(1)} km (~{Math.round((routeGeojson.features[0]?.properties?.duration_s || 11520) / 60)} min walk)
              </span>
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '12px', lineHeight: '1.4' }}>
              Walking exceeds safe heat exposure limits. <strong>Take motorized transit</strong> or stay within shaded 10-minute zones.
            </div>
          </div>
          <button 
            onClick={() => setRouteGeojson(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '16px',
              padding: '4px',
              marginLeft: 'auto'
            }}
            title="Dismiss Alert"
          >
            ✕
          </button>
        </div>
      )}

      {/* Stacked Safety Callouts */}
      <div className="callout-container">
        {currentWeather?.heat_risk_level === 'EXTREME' && routeGeojson?.features?.[0]?.properties?.exposure_m > 0 && (
          <div className="route-safety-callout" style={{ background: 'rgba(230, 57, 70, 0.15)', color: 'var(--accent-danger)', borderColor: 'rgba(230, 57, 70, 0.4)' }}>
             <MapPin size={20} />
             <span>Nearest cool spot is outside the hottest zone, but longer walking routes cross an extreme-heat area right now. Proceed with caution.</span>
          </div>
        )}
        
        {routeGeojson?.features?.[0]?.properties?.optimized && (
          <div className="route-safety-callout" style={{ background: 'rgba(62, 207, 142, 0.15)', color: 'var(--accent-teal)', borderColor: 'rgba(62, 207, 142, 0.4)' }}>
             <MapPin size={20} />
             <span>This route is <strong>Shade-Optimized</strong>. The agent intersected potential paths with the UHI heatmap to minimize heat exposure.</span>
          </div>
        )}
      </div>

      </div>

      {/* Floating Glassmorphism Chat Sidebar */}
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
          <div className="zero-state-dashboard citizen-dashboard">
            {/* Hero Alert Banner */}
            <div className={`hero-alert-banner ${getRiskColorClass(riskLevel)}`}>
              <div className="alert-top">
                <span className="location-text">{currentWeather ? 'Right now near you' : 'Location required'}</span>
                <Sun size={28} color={currentWeather ? (riskLevel === 'LOW' ? '#86efac' : '#fca5a5') : "#a1a1aa"} />
              </div>
              <h2>{currentWeather ? `${currentWeather.heat_risk_level} heat — ${Math.round(currentWeather.feels_like_celsius)}°C` : 'Analyzing conditions...'}</h2>
              <p>{currentWeather ? (riskLevel === 'EXTREME' || riskLevel === 'HIGH' ? 'Avoid going outside during peak hours. Drink water.' : 'Conditions are relatively safe. Stay hydrated.') : 'Please enter your location to get safety alerts.'}</p>
            </div>
            
            {/* 2x2 Action Grid */}
            <div className="action-grid">
              <button className={`action-btn ${currentWeather ? 'btn-red' : 'btn-gray'}`} onClick={() => handleQuickAction("I don't feel well. Please ask me for my symptoms to triage heat exhaustion vs heat stroke.")}>
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
          )
        )}

        {currentView === 'check-in' && (
          <div className="check-in-view">
            <div className="check-in-header">
              <button className="back-btn" onClick={() => setCurrentView('dashboard')}><ArrowLeft size={20} /></button>
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
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <ArrowLeft size={16} /> Back to Dashboard
              </button>
            </div>
            <div className="chat-history">
              {messages.map((msg, idx) => {
                const isSystem = msg.role === 'assistant' && (msg.content.includes('Weather data updated') || (msg.content.length < 40 && msg.content.includes('updated')));
                if (isSystem) {
                  return (
                    <div key={idx} className="msg-status">
                      Weather data updated.
                    </div>
                  );
                }
                
                // If it's a normal message
                if (msg.role === 'user') {
                  return (
                    <div key={idx} className="msg-user">
                      {msg.content}
                    </div>
                  );
                }
                
                return (
                  <div key={idx} className="msg-ai">
                    {formatContent(msg.content)}
                  </div>
                );
              })}
            {/* Structured Symptom Triage Card */}
            {symptomTriage && (
               <SymptomTriageCard 
                  onSubmit={(symptoms) => submitMessage(`I am experiencing: ${symptoms.join(', ')}. What should I do?`)} 
                  onEmergency={(symptoms) => submitMessage(`EMERGENCY: I am calling emergency services! My symptoms are: ${symptoms.join(', ')}`)} 
               />
            )}
            
            {/* Structured Medical Triage Advice */}
            {medicalTriageAdvice && (
              <div className="msg-emergency">
                <div className="emergency-head">
                  <span>🚨</span> {medicalTriageAdvice.title}
                </div>
                <div style={{ padding: '4px 0', fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                  {medicalTriageAdvice.steps.split('\n').filter(l => l.trim().length > 0).map((line, i) => (
                    <p key={i} style={{ marginBottom: '8px' }}>
                      {line.startsWith('-') || line.startsWith('•') ? <span style={{ marginLeft: '10px' }}>{line}</span> : <strong>{line}</strong>}
                    </p>
                  ))}
                </div>
                {medicalTriageAdvice.requires_emergency && (
                  <button className="emergency-call-btn" onClick={() => submitMessage(`EMERGENCY: I am calling emergency services!`)}>
                    📞 CALL EMERGENCY SERVICES
                  </button>
                )}
              </div>
            )}
            
            {/* Structured Occupational Heat Card */}
              {workRestGuidance && (
                <div className="msg-ai">
                  <div className="message-content" style={{ background: 'transparent', padding: 0, border: 'none' }}>
                    <div className="work-rest-card" style={{ background: workRestGuidance.halt_operations ? 'rgba(255, 90, 60, 0.15)' : 'var(--bg-panel-raised)', padding: '20px', borderRadius: '12px', border: workRestGuidance.halt_operations ? '1px solid var(--risk-extreme)' : '1px solid var(--line)', marginTop: '10px' }}>
                      <div className="wrc-header" style={{ marginBottom: '15px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                          <h3 style={{ margin: '0', fontSize: '18px', lineHeight: '1.2' }}>Workload Safety{workRestGuidance.halt_operations ? ': Unsafe' : ''}</h3>
                          <span style={{ 
                            display: 'inline-block', whiteSpace: 'nowrap', flexShrink: 0,
                            padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold',
                            background: workRestGuidance.halt_operations ? 'var(--text-primary)' : (workRestGuidance.rest_minutes === 0 ? 'var(--risk-cool)' : 'var(--risk-caution)'),
                            color: 'var(--bg-panel)'
                          }}>
                            {workRestGuidance.halt_operations ? 'HALT OPERATIONS' : (workRestGuidance.rest_minutes === 0 ? 'CONTINUOUS WORK' : 'SCHEDULE REQUIRED')}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '12px', gap: '8px' }}>
                          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>Calculated via Wet Bulb Globe Temp (WBGT)</p>
                          <p style={{ margin: 0, fontSize: '16px', fontWeight: 'bold', whiteSpace: 'nowrap', flexShrink: 0 }}>{workRestGuidance.wbgt_celsius.toFixed(1)}°C WBGT</p>
                        </div>
                      </div>

                      <div className="wrc-progress-container" style={{ display: 'flex', height: '30px', borderRadius: '8px', overflow: 'hidden', marginBottom: '15px' }}>
                        {workRestGuidance.halt_operations ? (
                           <div style={{ flex: 1, background: 'var(--risk-extreme)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>STOP WORK IMMEDIATELY</div>
                        ) : (
                           <>
                             <div className="progress-stripes" style={{ flex: workRestGuidance.work_minutes, minWidth: 0, background: 'var(--risk-cool)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 'bold', fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                               WORK {workRestGuidance.work_minutes}M
                             </div>
                             {workRestGuidance.rest_minutes > 0 && (
                               <div style={{ flex: workRestGuidance.rest_minutes, minWidth: 0, background: 'var(--risk-extreme)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                                 REST {workRestGuidance.rest_minutes}M
                               </div>
                             )}
                           </>
                        )}
                      </div>

                      <div className="wrc-footer" style={{ borderTop: '1px solid var(--line)', paddingTop: '15px', marginTop: '5px', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Droplets size={16} color="var(--risk-natural)" />
                          <strong>Hydration:</strong> {workRestGuidance.hydration_rule}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                          <Info size={16} /> Based on official NIOSH thresholds for unacclimatized workers.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {Object.keys(orchestratorStatus).length > 0 && (
                <div className="msg-status" style={{ marginBottom: '10px', display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '350px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '0.9em', color: '#f8fafc' }}>
                    Batch Progress ({Object.values(orchestratorStatus).filter(s => s.status === 'success').length}/{Object.keys(orchestratorStatus).length})
                  </div>
                  {Object.entries(orchestratorStatus).map(([tid, info]) => (
                    <div key={tid} style={{ fontSize: '0.85em', color: info.status === 'error' ? '#ef4444' : '#10b981', display: 'flex', gap: '6px' }}>
                      <span>{info.status === 'success' ? '✅' : '⚠️'}</span>
                      <span style={{ wordBreak: 'break-word' }}>{tid} {info.status === 'error' ? `- ${info.error}` : 'Loaded'}</span>
                    </div>
                  ))}
                </div>
              )}
              
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

      {/* Panel Dock (Top Right) */}
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
                      title={isStatCardCollapsed ? "Expand Reading" : "Collapse Reading"}
                    >
                      {isStatCardCollapsed ? '▼ Expand' : '▲ Minimize'}
                    </button>
                  </div>
                </div>
              
              {!isStatCardCollapsed && (
                <>
                  <div className="stat-card-body">
                    <div className="risk-pill-container">
                      <div className="risk-pill extreme-pulse">
                        <span className="risk-dot"></span>
                        <div className="risk-text">
                          • {currentWeather.heat_risk_level || "UNKNOWN"} RISK
                        </div>
                      </div>
                    </div>
                  </div>
                  
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
                  
                  {safetyAdvice && (
                    <div className="recommendations-card">
                      <h3><MapPin size={18} /> Safety recommendations</h3>
                      <ul>
                        <li>Avoid outdoor physical exertion during peak afternoon hours.</li>
                        <li>Stay hydrated by drinking water regularly, even without thirst.</li>
                        <li>Seek shaded or air-conditioned spaces — several parks are nearby.</li>
                        <li>Wear lightweight, loose-fitting, light-colored clothing.</li>
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        <div className="forecast-overlay-container">
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
            {canvasComparisonData && (
              <div className="forecast-overlay" style={{ width: '100%' }}>
                <div className="stat-card" style={{ padding: '16px', background: 'rgba(26, 22, 19, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h4 style={{ margin: 0, fontSize: '14px', color: '#f8fafc' }}>{canvasComparisonData.title || "Comparative Matrix"}</h4>
                    <button className="close-btn" onClick={() => setCanvasComparisonData(null)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '14px' }}>✕</button>
                  </div>
                  <div className="table-responsive">
                    <table className="chat-md-table" style={{ margin: 0 }}>
                      <thead>
                        <tr>
                          {canvasComparisonData.columns?.map((col, cIdx) => (
                            <th key={cIdx}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {canvasComparisonData.rows?.map((row, rIdx) => (
                          <tr key={rIdx}>
                            {row.map((cell, cellIdx) => (
                              <td key={cellIdx}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
        </div>
      </div>

      {/* Floating Chat Pill & Quick Actions */}
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
  )
}

export default App
