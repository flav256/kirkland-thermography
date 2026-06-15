# Supabase backend — setup guide (Phase 2)

Supabase gives us four things this product needs: **Postgres + PostGIS** (spatial
DB for buildings, parcels, scores, predictions), **Storage** (rasters/overlays),
**Auth** (reps log in), and **row-level security** (keep commercial data private).

> **What Supabase will NOT do:** heavy raster processing or ML training. Those
> run offline (Python / the in-browser Studio); only the *results* are written to
> Supabase. Keep that boundary and the stack stays simple.

## 0. Mental model
```
  GeoTIFF ──Studio/Python──► overlay PNG + scores ──► Supabase (Storage + DB)
  Property roll / heat islands ──ogr2ogr──► PostGIS tables
  Realised jobs (CSV) ──────────────────► jobs table (private, RLS)
  Python ML (offline) ── reads features, writes ──► predictions table
                                   │
                            PWA (supabase-js, anon key + RLS) reads it all
```

## 1. Create the project
1. supabase.com → New project. Pick a region close to Montréal (e.g. **East US**;
   `ca-central` if offered). Set a strong DB password.
2. Project Settings → **API**: copy the **Project URL** and the **anon public**
   key (both safe to ship in the PWA — they're protected by RLS). The
   **service_role** key is a secret: server/loaders only, never in the browser
   or the repo.

## 2. Enable PostGIS + schema
SQL Editor → run:
```sql
create extension if not exists postgis;

-- Thermal images / processed datasets (mirrors data/overlays.json)
create table datasets (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  kind text default 'thermography',      -- thermography | heat_island | other
  file_path text,                        -- Storage path to overlay PNG
  bounds jsonb,                          -- {west,south,east,north}
  source text, date text,
  status text default 'review',          -- uploaded | review | published
  offset_e double precision default -4,  -- registration nudge (m)
  offset_n double precision default 6,
  created_at timestamptz default now()
);

-- Scored building footprints
create table buildings (
  id bigint primary key,                 -- osm_id
  geom geometry(Polygon,4326) not null,
  score real, grade text, color text,
  valid_px int, total_px int,
  class_counts jsonb,
  addr text, name text,
  dataset_id uuid references datasets(id)
);
create index buildings_geom_idx on buildings using gist (geom);

-- Property roll: age + construction type
create table parcels (
  id bigint generated always as identity primary key,
  geom geometry(MultiPolygon,4326),
  annee_construction int,
  code_utilisation text,                 -- CUBF use code
  nombre_logements int,
  building_area real, value numeric, civic_address text
);
create index parcels_geom_idx on parcels using gist (geom);

-- Heat-island polygons (extra criterion)
create table heat_islands (
  id bigint generated always as identity primary key,
  geom geometry(MultiPolygon,4326),
  intensity int, year int
);
create index heat_islands_geom_idx on heat_islands using gist (geom);

-- Realised insulation jobs = the ML labels (PRIVATE)
create table jobs (
  id uuid primary key default gen_random_uuid(),
  building_id bigint references buildings(id),
  civic_address text, job_date date,
  scope text, cost numeric,
  outcome text,                          -- sold | installed | declined | no_contact
  created_by uuid references auth.users(id),
  created_at timestamptz default now()
);

-- ML output: deal probability per building (PRIVATE)
create table predictions (
  building_id bigint references buildings(id) primary key,
  prob_success real, model_version text, features jsonb,
  updated_at timestamptz default now()
);

-- Street / sector roll-ups (public-safe: aggregate thermal only)
create view street_stats as
select p.civic_address as street, count(*) n,
       round(avg(b.score)::numeric,1) avg_score
from buildings b
left join lateral (
  select civic_address from parcels
  order by parcels.geom <-> b.geom limit 1
) p on true
group by 1;
```

## 3. Storage buckets
Storage → New bucket:
- **`overlays`** — processed overlay PNGs. *Public* read (they're just colour
  maps); writes restricted to authenticated users.
- **`rasters`** — optional, for source TIFFs. *Private*. (TIFFs are big — see
  §6; you may keep raw TIFFs off-Supabase and only store the PNGs.)

## 4. Auth + row-level security
- Auth → Providers: enable **Email** (magic link or password) for reps/admins.
- Turn on RLS and add policies. Public layers readable by anyone; commercial
  data only by signed-in users:
```sql
alter table buildings enable row level security;
alter table datasets  enable row level security;
alter table jobs        enable row level security;
alter table predictions enable row level security;

-- public read of map layers
create policy "read buildings" on buildings for select using (true);
create policy "read published datasets" on datasets for select using (status='published');

-- jobs + predictions: only authenticated users
create policy "auth read jobs" on jobs for select using (auth.role() = 'authenticated');
create policy "auth write jobs" on jobs for insert with check (auth.role() = 'authenticated');
create policy "auth read predictions" on predictions for select using (auth.role() = 'authenticated');
```

## 5. Loading data
- **Buildings GeoJSON** (Studio export) → load with `ogr2ogr`:
  ```bash
  ogr2ogr -f PostgreSQL "PG:host=db.<ref>.supabase.co user=postgres \
    password=*** dbname=postgres" buildings_scored.geojson \
    -nln buildings -append -lco GEOMETRY_NAME=geom
  ```
- **Property roll / heat islands** (GeoJSON or SHP) → same `ogr2ogr` into
  `parcels` / `heat_islands`.
- **Jobs CSV** → import via the Supabase Table editor or `\copy`.
- Run loaders with the **service_role** key / direct DB connection, never the
  anon key.

## 6. Free-tier reality
Free tier ≈ 500 MB DB, 1 GB Storage, 5 GB egress. Plenty for a **pilot** (one
sector/borough: overlay PNGs are ~1 MB each; a borough's buildings are small).
Full-agglomeration property roll + many boroughs → move to **Pro (~$25/mo)** and
keep raw TIFFs out of Supabase (process locally, store only PNGs + scores).

## 7. Wire the PWA (I'll build this)
```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY); // both public, RLS-guarded
  // published overlays → ☰ drawer; buildings → map; jobs/predictions behind login
</script>
```
Plan: published `datasets` feed the image registry; `buildings` replace the
static geojson (or hydrate from it); the Studio's "Publish" writes the PNG to
Storage + a `datasets` row; reps log in to see `predictions` + log `jobs`.

## What I need from you to start Phase 2
1. **Project URL** + **anon public key** (safe to share/commit).
2. Confirm region + whether reps need login now or later.
Then I'll add the supabase-js client, switch the map to read from Supabase, and
add Publish-from-Studio. Keep the **service_role** key private — don't paste it.
