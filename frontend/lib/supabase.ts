import { createBrowserClient } from "@supabase/ssr";
import type { Session, SupabaseClient, User } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

let browserClient: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient | null {
  if (!isSupabaseConfigured) return null;

  if (!browserClient) {
    browserClient = createBrowserClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }

  return browserClient;
}

export async function getSession(): Promise<Session | null> {
  const client = getSupabaseClient();
  if (!client) return null;

  const { data, error } = await client.auth.getSession();
  if (error) return null;

  return data.session ?? null;
}

export async function getSessionToken(): Promise<string | null> {
  const session = await getSession();
  return session?.access_token ?? null;
}

export async function getCurrentUser(): Promise<User | null> {
  const client = getSupabaseClient();
  if (!client) return null;

  const { data, error } = await client.auth.getUser();
  if (error) return null;

  return data.user ?? null;
}

export async function getCurrentUserId(): Promise<string> {
  const client = getSupabaseClient();

  if (!client) {
    throw new Error(
      "Supabase frontend keys are missing. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel, then redeploy."
    );
  }

  const {
    data: { session },
    error,
  } = await client.auth.getSession();

  if (error) {
    throw new Error(error.message || "Could not read login session.");
  }

  if (!session?.user?.id) {
    throw new Error("Login required. Please login again.");
  }

  return session.user.id;
}

export async function signOutSupabase(): Promise<void> {
  const client = getSupabaseClient();
  if (!client) return;

  await client.auth.signOut();
}
