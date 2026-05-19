import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Web3Guard AI by RAADHANEX",
    short_name: "Web3Guard AI",
    description: "Evidence-first Web3 launch readiness scanner. Public beta. Pre-audit only; not a certified audit.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#030712",
    theme_color: "#030712",
    categories: ["security", "developer", "productivity"],
    icons: [
      { src: "/og-image.svg", sizes: "1200x630", type: "image/svg+xml" },
      { src: "/raadhanex-logo.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
  };
}
