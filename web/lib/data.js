import { supabase } from './supabase';

const FALLBACK = process.env.NEXT_PUBLIC_FALLBACK_BASE || '';

function publicUrl(path) {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  if (supabase) return supabase.storage.from('overlays').getPublicUrl(path).data.publicUrl;
  return `${FALLBACK}/${path}`;
}

// Published thermal overlays. Supabase first, then the static overlays.json.
// Returns [{ id, title, file, bounds, source, date, opacity }]
export async function loadOverlays() {
  if (supabase) {
    const { data, error } = await supabase
      .from('datasets').select('*').eq('status', 'published');
    if (!error && data && data.length) {
      return data.map((d) => ({
        id: d.id, title: d.title, file: publicUrl(d.file_path),
        bounds: d.bounds, source: d.source, date: d.date, opacity: 0.7,
      }));
    }
  }
  try {
    const r = await fetch(`${FALLBACK}/data/overlays.json`);
    const j = await r.json();
    return (j.overlays || []).filter((o) => !o.pending).map((o) => ({
      ...o, file: `${FALLBACK}/${o.file}`,
    }));
  } catch {
    return [];
  }
}

// Scored buildings as a GeoJSON FeatureCollection.
// Supabase RPC first (buildings_geojson), then the static geojson.
export async function loadBuildings() {
  if (supabase) {
    const { data, error } = await supabase.rpc('buildings_geojson');
    if (!error && data && data.features && data.features.length) {
      return { collection: data, source: 'supabase' };
    }
  }
  try {
    const r = await fetch(`${FALLBACK}/data/buildings_scored.geojson`);
    return { collection: await r.json(), source: 'fallback' };
  } catch {
    return { collection: { type: 'FeatureCollection', features: [] }, source: 'none' };
  }
}
