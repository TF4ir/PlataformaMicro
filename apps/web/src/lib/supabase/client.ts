import { createBrowserClient } from "@supabase/ssr";

const DEFAULT_SUPABASE_URL = "https://oqjahhbqcethwgpufgnm.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY = "sb_publishable_u5AIwepBNqqKzQPxVtg5QQ_d_IQ3yrX";

export function createClient() {
  const supabaseUrl =
    process.env.NEXT_PUBLIC_SUPABASE_URL || DEFAULT_SUPABASE_URL;
  const supabaseAnonKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    DEFAULT_SUPABASE_ANON_KEY;

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
