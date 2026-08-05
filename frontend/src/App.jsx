import { useState, useRef, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Droplet, Sun, Thermometer, Navigation, Umbrella } from 'lucide-react'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import './App.css'

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
        const last = markers[markers.length - 1]
        map.flyTo([last.lat, last.lng], 13, { duration: 2 })
      }
    }
  }, [markers, map])
  
  return null
}

// Chart Component for Forecast
function ForecastWidget({ data }) {
  if (!data || data.length === 0) return null;
  
  const chartData = data.map(d => ({
    name: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
    Temp: d.max_temp_c,
    FeelsLike: d.feels_like_c
  }));

  return (
    <div className="forecast-widget">
      <h3>7-Day Heatwave Prediction</h3>
      <div style={{ height: '200px', width: '100%', marginTop: '10px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis dataKey="name" stroke="#fff" fontSize={12} />
            <YAxis stroke="#fff" fontSize={12} domain={['dataMin - 2', 'dataMax + 2']} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Line type="monotone" dataKey="Temp" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="FeelsLike" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </div>
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
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleQuickAction = (actionText) => {
    sendMessage(null, actionText)
  }

  const sendMessage = async (e, directText = null) => {
    if (e) e.preventDefault()
    
    const userMessage = directText || input
    if (!userMessage.trim() || isLoading) return
    
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)
    setForecastData(null) // Clear previous forecast chart on new request
    
    try {
      const history = messages.slice(1).map(m => ({ role: m.role, content: m.content }))
      
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: userMessage,
        history: history
      })
      
      const { text, markers: newMarkers, forecast } = response.data
      
      setMessages(prev => [...prev, { role: 'assistant', content: text }])
      
      if (newMarkers && newMarkers.length > 0) {
        setMarkers(newMarkers)
      }
      
      if (forecast) {
        setForecastData(forecast)
      }
      
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I encountered an error connecting to the HeatShield API. Make sure the FastAPI backend is running.' 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  // Parses markdown headers and wraps sections into "Cards"
  const formatContent = (text) => {
    if (!text) return null;
    
    // Split by Markdown headers (h2 or h3)
    const sections = text.split(/(?=###? )/);
    
    return sections.map((section, idx) => {
      let isWarning = section.includes('Alert') || section.includes('Warning') || section.includes('EXTREME');
      let isWeather = section.includes('Weather') || section.includes('Temperature');
      let isSpots = section.includes('Cooling') || section.includes('Spots');
      
      let cardClass = "chat-card";
      if (isWarning) cardClass += " warning-card";
      if (isWeather) cardClass += " weather-card";
      if (isSpots) cardClass += " spots-card";
      
      // If it doesn't start with a header, it's just normal text
      if (!section.startsWith('#')) {
         return (
           <div key={idx} className="chat-normal-text" dangerouslySetInnerHTML={{ 
             __html: section.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') 
           }} />
         );
      }
      
      // Clean up the text for the card
      const lines = section.split('\n');
      const header = lines[0].replace(/###? /, '');
      const body = lines.slice(1).join('\n')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\*/g, '<br/>•')
        .replace(/\n/g, '<br/>');
      
      return (
        <div key={idx} className={cardClass}>
          <h4>{header}</h4>
          <div className="card-body" dangerouslySetInnerHTML={{ __html: body }} />
        </div>
      );
    });
  }

  return (
    <div className="app-container">
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
              <Popup>{marker.label || 'Location'}</Popup>
            </Marker>
          ))}
        </MapContainer>
        
        {/* Floating Forecast Widget over the map! */}
        {forecastData && (
          <div className="forecast-overlay">
             <ForecastWidget data={forecastData} />
          </div>
        )}
      </div>

      {/* Floating Glassmorphism Chat Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>🌡️ HeatShield AI</h1>
        </div>
        
        <div className="chat-history">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {formatContent(msg.content)}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="loading-dots">
                <div className="dot"></div><div className="dot"></div><div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        
        {/* Quick Actions Area */}
        <div className="quick-actions">
           <button onClick={() => {
             const cities = ['Berlin', 'Paris', 'Madrid', 'Rome', 'Sfax', 'Tokyo']
             const randomCity = cities[Math.floor(Math.random() * cities.length)]
             handleQuickAction(`What is the 7-day forecast for ${randomCity}?`)
           }}><Thermometer size={14}/> Predict Heatwave</button>
           
           <button onClick={() => {
             const cities = ['Athens', 'Dubai', 'Seville', 'Marseille']
             const randomCity = cities[Math.floor(Math.random() * cities.length)]
             handleQuickAction(`Find cooling spots near me in ${randomCity}`)
           }}><Umbrella size={14}/> Find Shade</button>
           
           <button onClick={() => {
             const cities = ['London', 'New York', 'Beijing', 'Los Angeles']
             const randomCity = cities[Math.floor(Math.random() * cities.length)]
             handleQuickAction(`What is the air quality in ${randomCity}?`)
           }}><Sun size={14}/> Air Quality</button>
        </div>

        <form className="input-area" onSubmit={sendMessage}>
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about heat risks or cooling spots..."
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
            <Navigation size={18} />
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
