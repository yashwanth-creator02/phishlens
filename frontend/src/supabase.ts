import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// These two are PUBLIC values for this project's Supabase instance. The anon key is a
// client-side key by design - Supabase ships it in every browser bundle and it grants only
// what the `anon` role may do, which here is nothing: no table in supabase/migrations/
// grants the anon role. The service_role key is a SECRET and must never reach the browser.
//
// They are defaults rather than build arguments so that a local checkout is authenticated
// the same way the deployment is. A build can still override them with VITE_SUPABASE_URL and
// VITE_SUPABASE_ANON_KEY.
const url = (import.meta.env.VITE_SUPABASE_URL as string | undefined)
  ?? "https://vmbtdrmevlovvvfvtqmd.supabase.co";
const key = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)
  ?? "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtYnRkcm1ldmxvdnZ2"
     + "ZnZ0cW1kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMxMTMyNDYsImV4cCI6MjEwODY4OTI0Nn0."
     + "KzuP3Lnud5iphPHslZTv4oTC-Fw8-djo9HfUlG7o_80";

export const supabase: SupabaseClient | null = url && key ? createClient(url, key) : null;
