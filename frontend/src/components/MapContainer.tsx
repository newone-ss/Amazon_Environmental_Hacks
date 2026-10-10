import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { Village } from '../types';
import { bhujalAPI } from '../services/api';

interface MapContainerProps {
  selectedSiteId: string | null;
  onSiteSelect: (siteId: string) => void;
  demoModeActive: boolean;
}

const MapContainer: React.FC<MapContainerProps> = ({
  selectedSiteId,
  onSiteSelect,
  demoModeActive
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [villages, setVillages] = useState<Village[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Priority colors for settlements
  const priorityColors: Record<string, string> = {
    'Odisha': '#FF6B6B',        // Red for Odisha priority
    'Madhya Pradesh': '#4ECDC4', // Teal for MP priority
    'Jharkhand': '#45B7D1',      // Blue for Jharkhand priority
    'Pan-India': '#96CEB4'       // Green for Pan-India
  };

  // Fetch villages on mount
  useEffect(() => {
    const fetchVillages = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await bhujalAPI.getVillages();
        setVillages(response.data);
      } catch (err) {
        setError('Failed to load village data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchVillages();
  }, []);

  // Add settlement markers to the map
  const addSettlementMarkers = (map: maplibregl.Map, villageList: Village[]) => {
    if (villageList.length === 0) return;

    // Create a GeoJSON FeatureCollection from villages
    const features = villageList.map(village => ({
      type: 'Feature' as const,
      properties: {
        name: village.name,
        village_id: village.village_id,
        state: village.state,
        site_id: `site_${village.village_id.slice(-3)}`
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [village.lon, village.lat] as [number, number]
      }
    }));

    const geojson = {
      type: 'FeatureCollection' as const,
      features
    };

    const existingSource = map.getSource('settlements') as maplibregl.GeoJSONSource | undefined;
    if (existingSource) {
      existingSource.setData(geojson);
    } else {
      map.addSource('settlements', {
        type: 'geojson',
        data: geojson
      });

      // Add layer for markers
      map.addLayer({
        id: 'settlements',
        type: 'circle',
        source: 'settlements',
        paint: {
          'circle-radius': 8,
          'circle-color': [
            'match',
            ['get', 'state'],
            'Odisha', priorityColors.Odisha,
            'Madhya Pradesh', priorityColors['Madhya Pradesh'],
            'Jharkhand', priorityColors.Jharkhand,
            'Pan-India', priorityColors['Pan-India'],
            '#cccccc'
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-opacity': 0.8
        }
      });

      // Add hover state
      map.addLayer({
        id: 'settlements-hover',
        type: 'circle',
        source: 'settlements',
        paint: {
          'circle-radius': 12,
          'circle-color': '#ffffff',
          'circle-opacity': 0.5
        },
        filter: ['==', '$type', 'Point']
      });
    }
  };

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [],
      },
      center: [78.9629, 20.5937], // Center of India
      zoom: 5,
      hash: false
    });

    mapRef.current = map;

    // Add default style layer
    map.on('load', () => {
      // Add a simple background
      map.addLayer({
        id: 'background',
        type: 'background',
        paint: {
          'background-color': '#f0f8ff'
        }
      });

      // Handle marker clicks
      map.on('click', 'settlements', (e: any) => {
        const features = e.features as any[];
        if (features && features.length > 0) {
          const siteId = features[0].properties.site_id;
          onSiteSelect(siteId);

          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`
              <h3>${features[0].properties.name}</h3>
              <p>${features[0].properties.village_id}</p>
            `)
            .addTo(map);
        }
      });

      // Change cursor to pointer when hovering over settlements
      map.on('mouseenter', 'settlements', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      map.on('mouseleave', 'settlements', () => {
        map.getCanvas().style.cursor = '';
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onSiteSelect]);

  // Sync settlement markers when villages load or update
  useEffect(() => {
    if (!mapRef.current || villages.length === 0) return;
    const map = mapRef.current;
    if (map.isStyleLoaded()) {
      addSettlementMarkers(map, villages);
    } else {
      map.once('load', () => addSettlementMarkers(map, villages));
    }
  }, [villages]);

  // Update marker for selected site
  useEffect(() => {
    if (!mapRef.current || !selectedSiteId) return;
    // Highlighting selected site: can be enhanced with layers
  }, [selectedSiteId]);

  // Handle demo mode - auto-select sites
  useEffect(() => {
    if (!demoModeActive || villages.length === 0) return;

    const demoSites = ['site_001', 'site_mp_001', 'site_jh_004'];
    let index = 0;

    const interval = setInterval(() => {
      if (index >= demoSites.length) index = 0;
      onSiteSelect(demoSites[index]);
      index++;
    }, 5000);

    return () => clearInterval(interval);
  }, [demoModeActive, villages.length, onSiteSelect]);

  return (
    <div className="map-container" style={{ position: 'relative', width: '100%', height: '100%', minHeight: '400px' }}>
      <div ref={mapContainerRef} className="map" style={{ width: '100%', height: '100%', minHeight: '400px' }} />
      {loading && (
        <div className="map-loading" style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, background: 'rgba(255,255,255,0.9)', padding: '6px 12px', borderRadius: '4px' }}>
          Loading settlement data...
        </div>
      )}
      {error && (
        <div className="map-error" style={{ position: 'absolute', top: 12, left: 12, zIndex: 10, background: 'rgba(255,230,230,0.95)', color: '#c53030', padding: '6px 12px', borderRadius: '4px' }}>
          {error}
        </div>
      )}
      {!demoModeActive && selectedSiteId === null && (
        <div className="map-instructions" style={{ position: 'absolute', bottom: 12, left: 12, zIndex: 10, background: 'rgba(255,255,255,0.9)', padding: '6px 12px', borderRadius: '4px' }}>
          <p style={{ margin: 0 }}>Click on a settlement to view details</p>
        </div>
      )}
      {demoModeActive && (
        <div className="map-demo-badge" style={{ position: 'absolute', bottom: 12, left: 12, zIndex: 10, background: '#3182ce', color: '#fff', padding: '6px 12px', borderRadius: '4px' }}>
          Demo Mode: Auto-cycling through priority sites
        </div>
      )}
    </div>
  );
};

export default MapContainer;