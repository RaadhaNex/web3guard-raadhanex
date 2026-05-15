import { createBrowserClient } from "@supabase/ssr";

type DashboardAuthContext = {
  userId: string;
  email: string | null;
  accessToken: string;
  headers: Record<string, string>;
};

export async function currentDashboardUser(): Promise<DashboardAuthContext> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Supabase frontend keys are missing. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel, then redeploy."
    );
  }

  const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey);

  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    throw new Error(error.message || "Could not read login session.");
  }

  if (!session?.user?.id || !session.access_token) {
    throw new Error("Login required. Please login again.");
  }

  return {
    userId: session.user.id,
    email: session.user.email ?? null,
    accessToken: session.access_token,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "x-user-id": session.user.id,
    },
  };
}

export function fmtDate(value: string | null | undefined) {
  if (!value) return "Not available";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return date.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function scoreText(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Not assessed";
  }

  return `${Math.round(value)}/100`;
}