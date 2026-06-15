import { createClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Null when env isn't configured — callers fall back to static data.
export const supabase = url && anon ? createClient(url, anon) : null;
export const hasSupabase = Boolean(supabase);
