import type { MetadataRoute } from "next";

function siteUrl() {
  return (process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_FRONTEND_URL || "https://web3guard-raadhanex.vercel.app").replace(/\/$/, "");
}

export default function robots(): MetadataRoute.Robots {
  const base = siteUrl();
  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/scanner",
          "/scanner/unified-url",
          "/methodology",
          "/limitations",
          "/sample-reports",
          "/feature-status",
          "/engine-depth",
          "/provider-readiness",
          "/free-tools",
          "/privacy",
          "/terms",
          "/security",
          "/pricing",
        ],
        disallow: [
          "/admin",
          "/dashboard",
          "/settings",
          "/auth",
          "/report/professional",
        ],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
  };
}
