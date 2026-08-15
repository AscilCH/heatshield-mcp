import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

export default function MapController({ markers, routeGeojson, uhiGeojson, isochroneGeojson, heatDomeGeojson, canvasCamera, canvasLayers }) {
  const map = useMap();
  
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
  }, [markers, routeGeojson, uhiGeojson, isochroneGeojson, heatDomeGeojson, canvasCamera, canvasLayers, map]);

  return null;
}
