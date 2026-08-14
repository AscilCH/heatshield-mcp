import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';

const ClusterMarkers = ({ markers, createCustomIcon, getMarkerColor }) => {
  const map = useMap();

  useEffect(() => {
    if (!markers || markers.length === 0) return;

    const mcg = L.markerClusterGroup({ chunkedLoading: true });
    
    markers.forEach(marker => {
      const leafletMarker = L.marker([marker.lat, marker.lng], {
        icon: createCustomIcon(getMarkerColor(marker), marker.type === 'user_location')
      });
      
      let popupContent = '';
      if (marker.type === 'cooling_spot') {
        const type = marker.tags?.amenity || marker.tags?.leisure || 'Cooling Shelter';
        popupContent = `
          <div style="padding: 2px; min-width: 150px;">
            <h3 style="margin: 0 0 4px 0; font-size: 14px; color: #1e293b;">${marker.label || 'Location'}</h3>
            <p style="margin: 0 0 4px 0; font-size: 12px; color: #64748b; text-transform: capitalize;">Type: ${type}</p>
            ${marker.dist ? `<p style="margin: 0; font-size: 12px; font-weight: bold; color: #3b82f6;">${marker.dist} meters away (approx)</p>` : ''}
          </div>
        `;
      } else {
        popupContent = marker.label || 'Location';
      }
      
      leafletMarker.bindPopup(popupContent);
      
      // Add a permanent tooltip for the user/inspection location so it doesn't look like a stray pin
      if (marker.type === 'user_location') {
        leafletMarker.bindTooltip(marker.label || 'Inspection Point', { permanent: true, direction: 'top', offset: [0, -20] });
      }
      
      mcg.addLayer(leafletMarker);
    });

    map.addLayer(mcg);

    return () => {
      map.removeLayer(mcg);
    };
  }, [map, markers, createCustomIcon, getMarkerColor]);

  return null;
};

export default ClusterMarkers;
