import type { MetadataRoute } from "next";

function siteUrl() {
  return (process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXT_PUBLIC_FRONTEND_URL || "https://web3guard-raadhanex.vercel.app").replace(/\/$/, "");
}

const publicRoutes = [
  "",
  "/scanner",
  "/scanner/unified-url",
  "/methodology",
  "/limitations",
  "/sample-reports",
  "/feature-status",
  "/engine-depth",
  "/provider-readiness",
  "/free-tools",
  "/launch-readiness",
  "/production-deployment-qa",
  "/launch-qa",
  "/report/verify",
  "/pricing",
  "/privacy",
  "/terms",
  "/security",
  "/responsible-use",
  "/contact",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const now = new Date();
  return publicRoutes.map((route) => ({
    url: `${base}${route}`,
    lastModified: now,
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : route.includes("scanner") ? 0.9 : 0.65,
  }));
}
