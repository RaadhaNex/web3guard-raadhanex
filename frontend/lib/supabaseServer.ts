import { cookies } from "next/headers";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const isSupabaseServerConfigured = Boolean(
  supabaseUrl && supabaseAnonKey
);

export async function getSupabaseServerClient() {
  if (!isSupabaseServerConfigured) {
    return null;
  }

  const cookieStore = await cookies();

  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      get(name: string) {
        return cookieStore.get(name)?.value;
      },

      set(name: string, value: string, options: CookieOptions) {
        try {
          cookieStore.set({
            name,
            value,
            ...options,
          });
        } catch {
          // Server Components cannot always set cookies.
          // Middleware/client auth flow will handle refresh/logout.
        }
      },

      remove(name: string, options: CookieOptions) {
        try {
          cookieStore.set({
            name,
            value: "",
            ...options,
          });
        } catch {
          // Server Components cannot always delete cookies.
        }
      },
    },
  });
}