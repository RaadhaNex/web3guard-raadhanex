/** @type {import('next').NextConfig} */
const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "https://web3guard-raadhanex-backend.onrender.com").replace(/\/$/, "");
const supabaseUrl = (process.env.NEXT_PUBLIC_SUPABASE_URL || "").replace(/\/$/, "");
const razorpayKey = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "";

const connectSrc = [
  "'self'",
  apiBase,
  supabaseUrl,
  supabaseUrl ? `${supabaseUrl}/auth/v1` : "",
  supabaseUrl ? `${supabaseUrl}/rest/v1` : "",
  supabaseUrl ? `${supabaseUrl}/storage/v1` : "",
  "https://*.supabase.co",
  "https://api.razorpay.com",
  "https://checkout.razorpay.com",
].filter(Boolean).join(" ");

const frameSrc = [
  "'self'",
  razorpayKey ? "https://api.razorpay.com" : "",
  razorpayKey ? "https://checkout.razorpay.com" : "",
].filter(Boolean).join(" ");

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "style-src 'self' 'unsafe-inline'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://checkout.razorpay.com",
  `connect-src ${connectSrc}`,
  `frame-src ${frameSrc}`,
  "upgrade-insecure-requests",
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  productionBrowserSourceMaps: false,

  experimental: {
    cpus: 1,
    webpackBuildWorker: true,
    webpackMemoryOptimizations: true,
    staticGenerationRetryCount: 1,
    staticGenerationMaxConcurrency: 1,
    staticGenerationMinPagesPerWorker: 1,
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), usb=(), payment=(self)" },
          { key: "X-Web3Guard-Disclaimer", value: "pre-audit-readiness-not-certified-audit" },
        ],
      },
    ];
  },
};

export default nextConfig;
