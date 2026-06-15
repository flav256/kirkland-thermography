-- Thermography Agent — Supabase schema (Phase 2 pilot).
-- Run once in the Supabase SQL Editor. Safe to re-run (idempotent-ish).

create extension if not exists postgis;

-- Processed thermal images / datasets (mirrors data/overlays.json)
create table if not exists datasets (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  kind text default 'thermography',
  file_path text,                        -- Storage path (overlays bucket) or URL
  bounds jsonb,                          -- {west,south,east,north}
  source text, date text,
  status text default 'review',          -- uploaded | review | published
  offset_e double precision default -4,
  offset_n double precision default 6,
  created_at timestamptz default now()
);

-- Scored building footprints
create table if not exists buildings (
  id bigint primary key,                 -- osm_id
  geom geometry(Polygon,4326) not null,
  score real, grade text, color text,
  valid_px int, total_px int,
  class_counts jsonb,
  addr text, name text,
  dataset_id uuid references datasets(id)
);
create index if not exists buildings_geom_idx on buildings using gist (geom);

-- ---- Row-level security ----
alter table buildings enable row level security;
alter table datasets  enable row level security;

drop policy if exists "public read buildings" on buildings;
create policy "public read buildings" on buildings for select using (true);

drop policy if exists "public read published datasets" on datasets;
create policy "public read published datasets" on datasets for select using (status = 'published');

-- ---- Read API: buildings as GeoJSON (callable by anon) ----
create or replace function buildings_geojson(min_score real default 0)
returns jsonb language sql stable as $$
  select jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(jsonb_build_object(
      'type', 'Feature',
      'geometry', ST_AsGeoJSON(geom)::jsonb,
      'properties', jsonb_build_object(
        'osm_id', id, 'score', score, 'grade', grade, 'color', color,
        'addr', addr, 'name', name)
    )), '[]'::jsonb)
  )
  from buildings
  where score >= min_score;
$$;
grant execute on function buildings_geojson(real) to anon, authenticated;

-- ---- Write API: bulk import a FeatureCollection (service role only) ----
create or replace function import_buildings(fc jsonb, p_dataset uuid default null)
returns int language plpgsql as $$
declare f jsonb; n int := 0;
begin
  for f in select * from jsonb_array_elements(fc->'features') loop
    insert into buildings (id, geom, score, grade, color, valid_px, total_px, class_counts, addr, name, dataset_id)
    values (
      (f->'properties'->>'osm_id')::bigint,
      ST_SetSRID(ST_GeomFromGeoJSON(f->'geometry'), 4326),
      nullif(f->'properties'->>'score','')::real,
      f->'properties'->>'grade',
      f->'properties'->>'color',
      nullif(f->'properties'->>'valid_px','')::int,
      nullif(f->'properties'->>'total_px','')::int,
      f->'properties'->'class_counts',
      f->'properties'->>'addr',
      f->'properties'->>'name',
      p_dataset
    )
    on conflict (id) do update set
      geom = excluded.geom, score = excluded.score, grade = excluded.grade, color = excluded.color,
      valid_px = excluded.valid_px, total_px = excluded.total_px, class_counts = excluded.class_counts,
      addr = excluded.addr, name = excluded.name, dataset_id = excluded.dataset_id;
    n := n + 1;
  end loop;
  return n;
end; $$;
-- only the service-role loader may call this; never anon/authenticated
revoke all on function import_buildings(jsonb, uuid) from public, anon, authenticated;
