# Thermography Agent — Next.js app (Phase 2)

The Next.js + Vercel version of the app. Reads thermal overlays + scored
buildings from **Supabase**, falling back to the existing static site until
Supabase is seeded. The legacy static PWA stays at the repo root during the
transition.

## Stack
- **Next.js 14** (App Router, JS) · **MapLibre GL** · **@supabase/supabase-js**
- Data: Supabase **Postgres + PostGIS** (buildings, datasets) + **Storage** (overlay PNGs)

## 1. Configure
```bash
cd web
cp .env.local.example .env.local   # already filled for local dev
```
`.env.local` holds the public Supabase URL + anon key (safe). The **secret** key
is never stored here — it's passed at runtime to the loader only.

## 2. Run the database schema
Supabase → SQL Editor → paste **`web/supabase/schema.sql`** → Run. This creates
the tables, RLS policies, and the read/write RPCs.

Also create a **public Storage bucket** named `overlays` (for overlay PNGs).

## 3. Seed buildings into Supabase (optional but recommended)
Uses your **rotated** secret key (server-side, bypasses RLS):
```bash
cd web
npm install
SUPABASE_URL=https://<ref>.supabase.co \
SUPABASE_SECRET=<rotated-secret-key> \
npm run seed:buildings
```
This pushes `data/buildings_scored.geojson` into the `buildings` table. The app
then reads live from Supabase; before seeding it shows the static fallback.

## 4. Develop
```bash
npm install
npm run dev      # http://localhost:3000
```
The badge in the top-left shows whether data came from **Supabase** or the
**static fallback**.

## 5. Deploy to Vercel
1. Push this repo to GitHub (already done).
2. vercel.com → **Add New Project** → import the repo.
3. **Root Directory: `web`** (important — the Next app isn't at the repo root).
4. Add Environment Variables (Settings → Environment Variables):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_FALLBACK_BASE` = `https://flav256.github.io/kirkland-thermography`
   - *(do NOT add the secret key here — it's only for the local loader)*
5. Deploy. Every push to `main` → production; PRs → preview URLs.

> Vercel's free **Hobby** tier is non-commercial; use **Pro** for production.

## What's wired (Phase 2 so far)
- ✅ Supabase client + env config
- ✅ Map reads **published** overlays (`datasets`) + **buildings** (RPC) from Supabase
- ✅ Static fallback to the existing site when Supabase is empty/unset
- ✅ Geolocation, score legend, overlay opacity

## Next
- Port search (address geocoder), grade filters, the ☰ images drawer
- "Publish from Studio" → upload overlay PNG to Storage + insert `datasets` row
- Enrichment layers (property age/type, heat islands) + street/sector ranking
