import type { Metadata } from "next";
import "./globals.css";
import { AppChrome } from "@/components/layout/AppChrome";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const siteUrl = "https://web3guard-raadhanex.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),

  title: {
    default: "Web3Guard AI — Web3 Launch Readiness Scanner | RAADHANEX",
    template: "%s | Web3Guard AI",
  },

  description:
    "India-first evidence-first Web3 founder pre-audit launch readiness scanner for websites, dApps, APIs, Solidity code, wallet UX, GitHub, and admin OpSec. Public beta. Not a certified audit.",

  applicationName: "Web3Guard AI",
  authors: [{ name: "RAADHANEX", url: siteUrl }],
  creator: "RAADHANEX",
  publisher: "RAADHANEX",

  keywords: [
    "web3 security readiness",
    "smart contract scanner",
    "solidity scanner",
    "web3 india",
    "dapp security readiness",
    "blockchain launch checklist",
    "pre-audit review",
    "web3 launch security",
    "web3 security tool india",
    "founder security os",
    "RAADHANEX",
  ],

  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon.png", type: "image/png", sizes: "512x512" },
      { url: "/icon-192.png", type: "image/png", sizes: "192x192" },
      {
        url: "/brand/kavachwing-emblem-transparent.png",
        type: "image/png",
        sizes: "1024x1024",
      },
    ],
    shortcut: "/favicon.ico",
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },

  openGraph: {
    type: "website",
    locale: "en_IN",
    url: siteUrl,
    siteName: "Web3Guard AI",
    title: "Web3Guard AI — Web3 Launch Readiness Scanner",
    description:
      "Check Web3 launch readiness across websites, dApps, APIs, Solidity code, wallet UX, GitHub, and admin OpSec. Public beta. Pre-audit only; not a certified audit.",
    images: [
      {
        url: "/brand/kavachwing-hero.png",
        width: 1200,
        height: 630,
        alt: "Web3Guard AI — Web3 launch readiness scanner by RAADHANEX",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    title: "Web3Guard AI — Web3 Launch Readiness Scanner",
    description:
      "Evidence-first public beta scanner for Web3 launch readiness. Pre-audit only; not a certified audit.",
    images: ["/brand/kavachwing-hero.png"],
    creator: "@raadhanex",
  },

  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
    },
  },

  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#030712" },
    { media: "(prefers-color-scheme: light)", color: "#030712" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
      </head>
      <body>
        <AppChrome>{children}</AppChrome>
      </body>
    </html>
  );
}
