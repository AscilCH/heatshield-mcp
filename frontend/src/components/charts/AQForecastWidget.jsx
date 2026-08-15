import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AQForecastWidget({ data, onClose }) {
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
  );
}
