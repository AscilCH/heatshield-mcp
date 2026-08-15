import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function WBGTForecastWidget({ data, onClose }) {
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
  );
}
