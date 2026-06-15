// Seed the Supabase `buildings` table from a scored GeoJSON file.
// Uses the SECRET (service-role) key to bypass RLS — server-side only.
//
//   SUPABASE_URL=https://<ref>.supabase.co \
//   SUPABASE_SECRET=<rotated-secret-key> \
//   node scripts/load-buildings.mjs [path/to/buildings_scored.geojson]
//
// Default input: ../../data/buildings_scored.geojson (the existing repo data).

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createClient } from '@supabase/supabase-js';

const URL = process.env.SUPABASE_URL;
const SECRET = process.env.SUPABASE_SECRET;
if (!URL || !SECRET) {
  console.error('Set SUPABASE_URL and SUPABASE_SECRET env vars.');
  process.exit(1);
}

const input = process.argv[2]
  || fileURLToPath(new URL('../../data/buildings_scored.geojson', import.meta.url));
const fc = JSON.parse(readFileSync(input, 'utf8'));
const feats = fc.features || [];
console.log(`loaded ${feats.length} features from ${input}`);

const sb = createClient(URL, SECRET, { auth: { persistSession: false } });

const CHUNK = 400;
let done = 0;
for (let i = 0; i < feats.length; i += CHUNK) {
  const chunk = { type: 'FeatureCollection', features: feats.slice(i, i + CHUNK) };
  const { data, error } = await sb.rpc('import_buildings', { fc: chunk });
  if (error) { console.error('chunk failed:', error.message); process.exit(1); }
  done += data;
  console.log(`  upserted ${done}/${feats.length}`);
}
console.log('done.');
