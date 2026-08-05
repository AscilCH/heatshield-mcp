import { useState, useRef, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
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
      // Find the primary search location if any
      const searchLocation = markers.find(m => m.type === 'geocode_location')
      
      if (searchLocation) {
        map.flyTo([searchLocation.lat, searchLocation.lng], 13, { duration: 2 })
      } else {
        // Just fly to the last marker
        const last = markers[markers.length - 1]
        map.flyTo([last.lat, last.lng], 13, { duration: 2 })
      }
    }
  }, [markers, map])
  
  return null
}

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am HeatShield, your urban heat wave safety assistant. Where are you located, and how can I help you stay safe today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [markers, setMarkers] = useState([])
  const chatEndRef = useRef(null)

  // Scroll to bottom of chat automatically
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    
    const userMessage = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)
    
    try {
      // We pass the previous history excluding the very first greeting
      const history = messages.slice(1).map(m => ({ role: m.role, content: m.content }))
      
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: userMessage,
        history: history
      })
      
      const { text, markers: newMarkers } = response.data
      
      setMessages(prev => [...prev, { role: 'assistant', content: text }])
      
      if (newMarkers && newMarkers.length > 0) {
        setMarkers(newMarkers)
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

  // Helper to safely render markdown-like formatting in our simple chat
  const formatContent = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, i) => {
      if (line.startsWith('### ')) return <h3 key={i}>{line.replace('### ', '')}</h3>
      if (line.startsWith('* ')) return <li key={i}>{line.replace('* ', '')}</li>
      if (line.trim() === '---') return <hr key={i} style={{margin: '12px 0', borderColor: 'rgba(255,255,255,0.1)'}} />
      return <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
    })
  }

  return (
    <div className="app-container">
      {/* Background Map */}
      <div className="map-container">
        <MapContainer center={[49.0068, 8.4034]} zoom={4} style={{ height: '100%', width: '100%' }} zoomControl={false}>
          {/* Dark modern map tiles (CartoDB Dark Matter) */}
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          <MapController markers={markers} />
          
          {markers.map((marker, idx) => (
            <Marker key={idx} position={[marker.lat, marker.lng]}>
              <Popup>{marker.label || 'Location'}</Popup>
            </Marker>
          ))}
        </MapContainer>
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
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
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
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
