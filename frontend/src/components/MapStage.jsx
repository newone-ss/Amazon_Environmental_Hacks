import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl(workerUrl);
import {
  ChevronDown,
  ChevronUp,
  Crosshair,
  Droplets,
  Globe,
  Layers,
  MapPin,
  Navigation,
  Sun,
  Waves,
} from 'lucide-react';

const BASEMAP_STYLES = {
  dark: {
    id: 'dark',
    name: 'Dark Matter',
    icon: '🌙',
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  },
  osm: {
    id: 'osm',
    name: 'OpenStreetMap',
    icon: '🗺️',
    style: {
      version: 8,
      sources: {
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: 'osm-tiles-layer',
          type: 'raster',
          source: 'osm-tiles',
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
  satellite: {
    id: 'satellite',
    name: 'Satellite (ESRI)',
    icon: '🛰️',
    style: {
      version: 8,
      sources: {
        'esri-satellite': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '&copy; Esri, Maxar, Earthstar Geographics',
        },
      },
      layers: [
        {
          id: 'esri-satellite-layer',
          type: 'raster',
          source: 'esri-satellite',
          minzoom: 0,
          maxzoom: 19,
        },
      ],
    },
  },
  light: {
    id: 'light',
    name: 'Positron',
    icon: '☀️',
    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  },
};

const STATE_BOUNDS = {
  'All states': [
    [74.0, 17.8],
    [87.5, 24.5],
  ],
  Odisha: [
    [81.8, 18.0],
    [83.8, 19.8],
  ],
  'Madhya Pradesh': [
    [74.2, 21.8],
    [82.2, 23.8],
  ],
  Jharkhand: [
    [84.5, 22.0],
    [86.5, 23.5],
  ],
};


export default function MapStage({
  villages,
  sites,
  selectedVillage,
  onSelectVillage,
  stateFilter,
  layerMode,
  setLayerMode,
  showSafetyRings,
  setShowSafetyRings,
  showSprings,
  setShowSprings,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const popupRef = useRef(null);
  const aoiDataRef = useRef(null);

  const [layersCollapsed, setLayersCollapsed] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [basemapMode, setBasemapMode] = useState('dark');
  const [cursorCoords, setCursorCoords] = useState(null);
  const [locatingUser, setLocatingUser] = useState(false);

  // Helper to re-attach AOI and Settlements layers to the map
  function reAttachLayers(map) {
    if (!map) return;

    // 1. AOI Boundaries GeoJSON
    if (aoiDataRef.current && !map.getSource('aoi-boundaries')) {
      try {
        map.addSource('aoi-boundaries', {
          type: 'geojson',
          data: aoiDataRef.current,
        });

        if (!map.getLayer('aoi-fill')) {
          map.addLayer({
            id: 'aoi-fill',
            type: 'fill',
            source: 'aoi-boundaries',
            paint: {
              'fill-color': '#38bdf8',
              'fill-opacity': 0.07,
            },
          });
        }

        if (!map.getLayer('aoi-lines')) {
          map.addLayer({
            id: 'aoi-lines',
            type: 'line',
            source: 'aoi-boundaries',
            paint: {
              'line-color': '#38bdf8',
              'line-width': 1.6,
              'line-opacity': 0.4,
              'line-dasharray': [3, 2],
            },
          });
        }
      } catch (err) {
        console.warn('AOI layer mount error:', err);
      }
    }

    // 2. Settlements GeoJSON
    if (!map.getSource('settlements')) {
      map.addSource('settlements', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });
    }

    // 3. Safety Outer Ring Layer
    if (!map.getLayer('settlement-safety-rings')) {
      map.addLayer({
        id: 'settlement-safety-rings',
        type: 'circle',
        source: 'settlements',
        paint: {
          'circle-radius': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            17,
            13,
          ],
          'circle-color': 'transparent',
          'circle-stroke-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            3.5,
            2.5,
          ],
          'circle-stroke-color': [
            'match',
            ['get', 'safety_status'],
            'SAFE', '#22c55e',
            'CONDITIONAL', '#f59e0b',
            'REJECTED', '#ef4444',
            '#94a3b8',
          ],
          'circle-stroke-opacity': 0.95,
        },
      });
    }

    // 4. Score Fill Circle Layer
    if (!map.getLayer('settlement-circles')) {
      map.addLayer({
        id: 'settlement-circles',
        type: 'circle',
        source: 'settlements',
        paint: {
          'circle-radius': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            11,
            8,
          ],
          'circle-color': '#38bdf8',
          'circle-opacity': 0.92,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#07111b',
        },
      });
    }

    // 5. Spring Indicator Layer
    if (!map.getLayer('settlement-springs')) {
      map.addLayer({
        id: 'settlement-springs',
        type: 'circle',
        source: 'settlements',
        filter: ['==', ['get', 'has_spring'], true],
        paint: {
          'circle-radius': 3.5,
          'circle-color': '#67e8f9',
          'circle-opacity': 0.95,
        },
      });
    }

    // 6. Labels with Halo
    if (!map.getLayer('settlement-labels')) {
      map.addLayer({
        id: 'settlement-labels',
        type: 'symbol',
        source: 'settlements',
        layout: {
          'text-field': ['get', 'name'],
          'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
          'text-size': 11,
          'text-offset': [0, 1.4],
          'text-anchor': 'top',
          'text-allow-overlap': false,
        },
        paint: {
          'text-color': '#f8fafc',
          'text-halo-color': '#07111b',
          'text-halo-width': 2.5,
          'text-halo-blur': 0.5,
        },
      });
    }
  }

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: BASEMAP_STYLES.dark.style,
      center: [82.5, 21.0],
      zoom: 5.5,
      attributionControl: false,
    });

    // Add scale bar
    const scale = new maplibregl.ScaleControl({ maxWidth: 100, unit: 'metric' });
    map.addControl(scale, 'bottom-right');

    // Add navigation controls (Zoom +/-, 3D compass)
    const navControl = new maplibregl.NavigationControl({ visualizePitch: true });
    map.addControl(navControl, 'top-right');

    // Add Fullscreen control
    const fullscreen = new maplibregl.FullscreenControl();
    map.addControl(fullscreen, 'top-right');

    // Preload AOI GeoJSON with timeout
    const aoiController = new AbortController();
    const aoiTimeout = setTimeout(() => aoiController.abort(), 5000);
    fetch('/aoi.geojson', { signal: aoiController.signal })
      .then((res) => {
        clearTimeout(aoiTimeout);
        return res.ok ? res.json() : null;
      })
      .then((data) => {
        aoiDataRef.current = data;
        if (mapLoaded) reAttachLayers(map);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.warn('AOI GeoJSON fetch bypassed:', err);
        }
      });

    // Create interactive reusable popup
    const popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      className: 'bhujal-map-popup',
      offset: 14,
    });
    popupRef.current = popup;

    map.on('load', () => {
      reAttachLayers(map);
      setMapLoaded(true);
    });

    // Re-attach layers when basemap style changes
    map.on('style.load', () => {
      reAttachLayers(map);
      setMapLoaded(true);
    });

    // Fallback if vector style encounters error
    map.on('error', (e) => {
      if (e.error && String(e.error).includes('style')) {
        console.warn('Vector style error, falling back to OSM tiles:', e.error);
        map.setStyle(BASEMAP_STYLES.osm.style);
      }
    });

    // Marker click interaction with popup
    map.on('click', 'settlement-circles', (e) => {
      if (!e.features || e.features.length === 0) return;
      const props = e.features[0].properties;
      const match = villages.find((v) => v.id === props.id);
      if (match) {
        onSelectVillage(match);
        const coords = e.features[0].geometry.coordinates.slice();
        const site = sites[props.id];
        const rec = site?.recommendations?.[0]?.intervention_name || 'Bio-Engineering & Monitoring';
        const status = props.safety_status || 'SAFE';

        popup
          .setLngLat(coords)
          .setHTML(
            `<div class="map-popup-card">
              <div class="popup-head">
                <strong>${props.name}</strong>
                <span class="status-pill ${status.toLowerCase()}">${status}</span>
              </div>
              <div class="popup-sub">${props.district}, ${props.state}</div>
              <div class="popup-scores-row">
                <div><small>Recharge</small> <b>${Number(props.recharge_score || 50).toFixed(1)}/100</b></div>
                <div><small>Heat Stress</small> <b>${Number(props.heat_score || 50).toFixed(1)}/100</b></div>
              </div>
              <div class="popup-rec-action">
                <small>Plan:</small> <span>${status === 'REJECTED' ? 'CONSTRUCTION PROHIBITED' : rec}</span>
              </div>
            </div>`
          )
          .addTo(map);
      }
    });

    map.on('mouseenter', 'settlement-circles', () => {
      map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'settlement-circles', () => {
      map.getCanvas().style.cursor = '';
    });

    // Track live cursor coordinates
    map.on('mousemove', (e) => {
      setCursorCoords({
        lat: e.lngLat.lat.toFixed(4),
        lon: e.lngLat.lng.toFixed(4),
      });
    });

    mapRef.current = map;

    return () => {
      popup.remove();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Switch basemap theme
  function handleSwitchBasemap(mode) {
    if (!mapRef.current) return;
    setBasemapMode(mode);
    const targetStyle = BASEMAP_STYLES[mode]?.style || BASEMAP_STYLES.dark.style;
    mapRef.current.setStyle(targetStyle);
  }

  // Locate User via device GPS
  function handleLocateUser() {
    // Check for HTTPS requirement
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
      alert('Geolocation requires HTTPS. Please access the app via HTTPS or localhost.');
      return;
    }
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setLocatingUser(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        mapRef.current?.flyTo({
          center: [longitude, latitude],
          zoom: 11,
          speed: 1.2,
        });
        setLocatingUser(false);
      },
      (err) => {
        alert('GPS location access restricted: ' + err.message);
        setLocatingUser(false);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  // Update GeoJSON features when villages, sites, or active layer changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;
    const source = map.getSource('settlements');
    if (!source) return;

    const features = villages.map((v) => {
      const site = sites[v.id];
      const safetyStatus = site?.safety?.status || 'SAFE';
      const recharge = site?.scores?.find((s) => s.score_type === 'recharge_score')?.value ?? 50;
      const heat = site?.scores?.find((s) => s.score_type === 'heat_water_stress')?.value ?? 50;
      const spring = site?.scores?.find((s) => s.score_type === 'spring_drying_index')?.value ?? 50;

      return {
        type: 'Feature',
        id: v.id,
        properties: {
          id: v.id,
          name: v.name,
          district: v.district,
          state: v.state,
          safety_status: safetyStatus,
          has_spring: v.has_spring,
          recharge_score: recharge,
          heat_score: heat,
          spring_score: spring,
        },
        geometry: {
          type: 'Point',
          coordinates: [v.lon, v.lat],
        },
      };
    });

    source.setData({
      type: 'FeatureCollection',
      features,
    });

    // Set active score color ramp on settlement-circles
    if (map.getLayer('settlement-circles')) {
      if (layerMode === 'Recharge Potential') {
        map.setPaintProperty('settlement-circles', 'circle-color', [
          'interpolate',
          ['linear'],
          ['get', 'recharge_score'],
          0, '#bfdbfe',
          40, '#60a5fa',
          70, '#2563eb',
          100, '#1d4ed8',
        ]);
      } else if (layerMode === 'Heat-Water Vulnerability') {
        map.setPaintProperty('settlement-circles', 'circle-color', [
          'interpolate',
          ['linear'],
          ['get', 'heat_score'],
          0, '#fef08a',
          40, '#f59e0b',
          70, '#ea580c',
          100, '#dc2626',
        ]);
      } else {
        map.setPaintProperty('settlement-circles', 'circle-color', [
          'interpolate',
          ['linear'],
          ['get', 'spring_score'],
          0, '#fed7aa',
          40, '#fb923c',
          70, '#ef4444',
          100, '#991b1b',
        ]);
      }
    }

    // Toggle layers visibility
    if (map.getLayer('settlement-safety-rings')) {
      map.setLayoutProperty(
        'settlement-safety-rings',
        'visibility',
        showSafetyRings ? 'visible' : 'none'
      );
    }
    if (map.getLayer('settlement-springs')) {
      map.setLayoutProperty(
        'settlement-springs',
        'visibility',
        showSprings ? 'visible' : 'none'
      );
    }
  }, [villages, sites, layerMode, showSafetyRings, showSprings, mapLoaded]);

  // Fit bounds when state filter changes
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const bounds = STATE_BOUNDS[stateFilter] || STATE_BOUNDS['All states'];
    mapRef.current.fitBounds(bounds, {
      padding: { top: 60, bottom: 60, left: 60, right: 380 },
      duration: 900,
    });
  }, [stateFilter, mapLoaded]);

  // Fly to selected village
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !selectedVillage) return;
    const map = mapRef.current;

    map.flyTo({
      center: [selectedVillage.lon, selectedVillage.lat],
      zoom: 9.2,
      duration: 800,
      essential: true,
    });

    villages.forEach((v) => {
      try {
        map.setFeatureState(
          { source: 'settlements', id: v.id },
          { selected: v.id === selectedVillage.id }
        );
      } catch {
        // Ignored if feature not loaded
      }
    });
  }, [selectedVillage?.id, mapLoaded]);

  return (
    <section className="map-stage" aria-label="Area of interest map stage">
      {/* MapLibre WebGL container */}
      <div ref={mapContainerRef} className="maplibre-container" />

      {/* Mobile Layer Chips (Visible < 768px) */}
      <div className="mobile-layer-chips-container" role="radiogroup" aria-label="Score layer selector">
        <button
          type="button"
          className={`mobile-layer-chip ${layerMode === 'Recharge Potential' ? 'active' : ''}`}
          onClick={() => setLayerMode('Recharge Potential')}
          role="radio"
          aria-checked={layerMode === 'Recharge Potential'}
        >
          <Droplets size={12} />
          <span>Recharge</span>
        </button>
        <button
          type="button"
          className={`mobile-layer-chip ${layerMode === 'Heat-Water Vulnerability' ? 'active' : ''}`}
          onClick={() => setLayerMode('Heat-Water Vulnerability')}
          role="radio"
          aria-checked={layerMode === 'Heat-Water Vulnerability'}
        >
          <Sun size={12} />
          <span>Heat-Water</span>
        </button>
        <button
          type="button"
          className={`mobile-layer-chip ${layerMode === 'Spring Desiccation Risk' ? 'active' : ''}`}
          onClick={() => setLayerMode('Spring Desiccation Risk')}
          role="radio"
          aria-checked={layerMode === 'Spring Desiccation Risk'}
        >
          <Waves size={12} />
          <span>Springs</span>
        </button>
        <button
          type="button"
          className={`mobile-layer-chip chip-toggle ${showSafetyRings ? 'active' : ''}`}
          onClick={() => setShowSafetyRings((r) => !r)}
          role="checkbox"
          aria-checked={showSafetyRings}
          aria-label="Toggle safety rings"
        >
          <span>Safety Rings</span>
        </button>
      </div>

      {/* Floating Collapsible Layer & Basemap Control (Desktop) */}
      <div className={`map-layer-card ${layersCollapsed ? 'collapsed' : ''}`} aria-label="Map Layers">
        <div className="layer-card-header" onClick={() => setLayersCollapsed((c) => !c)}>
          <div className="layer-header-title">
            <Layers size={16} />
            <span>Map Layers &amp; Themes</span>
          </div>
          <button type="button" className="layer-collapse-btn" aria-label="Toggle layers panel">
            {layersCollapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>

        {!layersCollapsed && (
          <div className="layer-card-body">
            <span className="layer-subhead">LIVE BASEMAP THEME</span>
            <div className="basemap-switch-grid">
              {Object.values(BASEMAP_STYLES).map((bm) => (
                <button
                  key={bm.id}
                  type="button"
                  className={`basemap-pill-btn ${basemapMode === bm.id ? 'active' : ''}`}
                  onClick={() => handleSwitchBasemap(bm.id)}
                  title={`Switch to ${bm.name}`}
                >
                  <span>{bm.icon}</span>
                  <span>{bm.name}</span>
                </button>
              ))}
            </div>

            <span className="layer-subhead mt-2">CORE SCORING LAYERS</span>
            <label className="layer-option">
              <input
                type="radio"
                name="score-layer"
                checked={layerMode === 'Recharge Potential'}
                onChange={() => setLayerMode('Recharge Potential')}
              />
              <Droplets size={14} className="layer-icon blue" />
              <span>Recharge Potential</span>
            </label>
            <label className="layer-option">
              <input
                type="radio"
                name="score-layer"
                checked={layerMode === 'Heat-Water Vulnerability'}
                onChange={() => setLayerMode('Heat-Water Vulnerability')}
              />
              <Sun size={14} className="layer-icon orange" />
              <span>Heat-Water Stress</span>
            </label>
            <label className="layer-option">
              <input
                type="radio"
                name="score-layer"
                checked={layerMode === 'Spring Desiccation Risk'}
                onChange={() => setLayerMode('Spring Desiccation Risk')}
              />
              <Waves size={14} className="layer-icon cyan" />
              <span>Spring Drying Risk</span>
            </label>

            <span className="layer-subhead mt-2">SAFETY &amp; FEATURES</span>
            <label className="layer-option">
              <input
                type="checkbox"
                checked={showSafetyRings}
                onChange={(e) => setShowSafetyRings(e.target.checked)}
              />
              <span className="safety-legend-swatch" />
              <span>Safety Status Rings</span>
            </label>
            <label className="layer-option">
              <input
                type="checkbox"
                checked={showSprings}
                onChange={(e) => setShowSprings(e.target.checked)}
              />
              <span className="spring-legend-swatch" />
              <span>Perched Springs <small>(Proxy)</small></span>
            </label>
          </div>
        )}
      </div>

      {/* Recenter & Geolocation Quick Action Bar */}
      <div className="map-action-buttons-group">
        <button
          className="map-target map-locate-btn"
          aria-label="Locate my GPS position"
          title="Locate my position via device GPS"
          onClick={handleLocateUser}
        >
          <Crosshair size={17} className={locatingUser ? 'spin-icon' : ''} />
        </button>

        <button
          className="map-target"
          aria-label="Recenter map bounds"
          title="Recenter map bounds"
          onClick={() => {
            const bounds = STATE_BOUNDS[stateFilter] || STATE_BOUNDS['All states'];
            mapRef.current?.fitBounds(bounds, { padding: 60, duration: 800 });
          }}
        >
          <Navigation size={17} />
        </button>
      </div>

      {/* Floating Dynamic Legend */}
      <div className="map-legend-card" aria-label="Map Legend">
        <div className="legend-title">{layerMode}</div>
        <div
          className={`legend-gradient-bar ${
            layerMode === 'Recharge Potential'
              ? 'ramp-recharge'
              : layerMode === 'Heat-Water Vulnerability'
              ? 'ramp-heat'
              : 'ramp-spring'
          }`}
        />
        <div className="legend-labels">
          <span>Lower</span>
          <span>Higher</span>
        </div>

        <div className="legend-symbol-key">
          <div className="symbol-item">
            <span className="symbol-ring safe" />
            <span>SAFE</span>
          </div>
          <div className="symbol-item">
            <span className="symbol-ring conditional" />
            <span>CONDITIONAL</span>
          </div>
          <div className="symbol-item">
            <span className="symbol-ring rejected" />
            <span>REJECTED</span>
          </div>
        </div>
      </div>

      {/* North Compass Arrow */}
      <div className="north-arrow" aria-label="North orientation">
        <span>N</span>
        <svg viewBox="0 0 24 24" width="16" height="16">
          <polygon points="12,2 17,20 12,16 7,20" fill="#38bdf8" />
        </svg>
      </div>

      {/* Bottom live status bar */}
      <div className="map-bottom-note">
        <span className="map-status-dot" />
        <span>13 Curated Settlement Sites</span>
        <span className="map-bottom-sep" />
        <span>District AOI Boundaries: Active</span>
        {cursorCoords && (
          <>
            <span className="map-bottom-sep" />
            <span className="cursor-coords-pill">
              {cursorCoords.lat}° N, {cursorCoords.lon}° E
            </span>
          </>
        )}
      </div>
    </section>
  );
}

