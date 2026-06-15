'use client';

import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { loadOverlays, loadBuildings } from '@/lib/data';

const GRADE_COLOR = { A: '#1eaa46', B: '#86c33b', C: '#dcdc3c', D: '#e8a02e', E: '#dc5a28', F: '#dc2828' };
const LEGEND = [
  ['#1eaa46', '85–100 · A (excellent)'], ['#86c33b', '70–84 · B'], ['#dcdc3c', '55–69 · C'],
  ['#e8a02e', '40–54 · D'], ['#dc5a28', '25–39 · E'], ['#dc2828', '0–24 · F (poor)'],
];

function bboxOf(fc) {
  let w = 180, s = 90, e = -180, n = -90;
  for (const f of fc.features) {
    for (const ring of f.geometry.coordinates) {
      for (const [x, y] of ring) { if (x < w) w = x; if (x > e) e = x; if (y < s) s = y; if (y > n) n = y; }
    }
  }
  return [[w, s], [e, n]];
}

export default function MapView() {
  const ref = useRef(null);
  const mapRef = useRef(null);
  const [status, setStatus] = useState('loading');   // loading | supabase | fallback | none
  const [count, setCount] = useState(0);
  const [opacity, setOpacity] = useState(0.7);

  useEffect(() => {
    if (mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        sources: {
          carto: {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
              'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap, © CARTO · Thermography: Ville de Montréal',
          },
        },
        layers: [{ id: 'base', type: 'raster', source: 'carto' }],
      },
      center: [-73.87, 45.45],
      zoom: 11,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true }, trackUserLocation: true, showUserHeading: true,
    }), 'top-right');

    map.on('load', async () => {
      // thermal overlays
      const overlays = await loadOverlays();
      overlays.forEach((o, i) => {
        if (!o.file || !o.bounds) return;
        const b = o.bounds;
        map.addSource(`ov-${i}`, {
          type: 'image', url: o.file,
          coordinates: [[b.west, b.north], [b.east, b.north], [b.east, b.south], [b.west, b.south]],
        });
        map.addLayer({
          id: `ov-${i}`, type: 'raster', source: `ov-${i}`,
          paint: { 'raster-opacity': 0.7, 'raster-resampling': 'nearest' },
        });
      });

      // scored buildings
      const { collection, source } = await loadBuildings();
      setStatus(source);
      setCount(collection.features.length);
      map.addSource('buildings', { type: 'geojson', data: collection });
      map.addLayer({
        id: 'buildings-fill', type: 'fill', source: 'buildings',
        paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.8, 'fill-outline-color': 'rgba(0,0,0,0.25)' },
      });
      map.addLayer({
        id: 'buildings-hi', type: 'line', source: 'buildings',
        paint: { 'line-color': '#00e5ff', 'line-width': 2.5 }, filter: ['==', 'osm_id', -1],
      });
      if (collection.features.length) {
        try { map.fitBounds(bboxOf(collection), { padding: 40, animate: false }); } catch {}
      }

      const popup = new maplibregl.Popup({ closeButton: true, maxWidth: '300px' });
      map.on('click', 'buildings-fill', (e) => {
        const p = e.features[0].properties;
        map.setFilter('buildings-hi', ['==', 'osm_id', p.osm_id]);
        const title = p.addr || p.name || `Building ${p.osm_id}`;
        popup.setLngLat(e.lngLat).setHTML(
          `<div><b>${title}</b><br>` +
          `<span style="font-size:22px;font-weight:700;color:${p.color}">${p.score}</span>` +
          `<span style="color:#9aa6b2">/100</span> · grade ` +
          `<b style="color:${GRADE_COLOR[p.grade] || '#fff'}">${p.grade}</b></div>`
        ).addTo(map);
      });
      map.on('mouseenter', 'buildings-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'buildings-fill', () => { map.getCanvas().style.cursor = ''; });
    });

    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // opacity slider → all overlay layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    for (let i = 0; i < 20; i++) {
      if (map.getLayer(`ov-${i}`)) map.setPaintProperty(`ov-${i}`, 'raster-opacity', opacity);
    }
  }, [opacity]);

  const badge = status === 'supabase' ? ['live', 'data: Supabase']
    : status === 'fallback' ? ['fallback', 'data: static fallback']
    : status === 'loading' ? ['loading', 'loading…'] : ['fallback', 'no data'];

  return (
    <>
      <div className="map" ref={ref} />
      <div className="panel topbar">
        <h1>Thermography Agent</h1>
        <div className="sub">Aerial surface thermography → per-building insulation scores. Cooler roof = better insulation.</div>
        <div className={`badge ${badge[0]}`}>{badge[1]}{count ? ` · ${count.toLocaleString()} buildings` : ''}</div>
        <div className="row">overlay <input type="range" min="0" max="100" value={Math.round(opacity * 100)}
          onChange={(e) => setOpacity(e.target.value / 100)} /></div>
      </div>
      <div className="panel legend">
        <div className="sec">Insulation score</div>
        {LEGEND.map(([c, t]) => (
          <div className="item" key={t}><span className="sw" style={{ background: c }} />{t}</div>
        ))}
      </div>
    </>
  );
}
