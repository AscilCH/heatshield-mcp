import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ForecastWidget({ data, onClose }) {
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
  );
}
