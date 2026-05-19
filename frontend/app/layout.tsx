import type { Metadata } from "next";
import "./globals.css";
import { AppChrome } from "@/components/layout/AppChrome";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata: Metadata = {
  title: {
    default: "Web3Guard AI — Web3 Launch Readiness Scanner | RAADHANEX",
    template: "%s | Web3Guard AI",
  },
  description:
    "Evidence-first Web3 launch readiness scanner for websites, dApps, APIs, Solidity code, wallet UX, GitHub, and admin OpSec. Public beta. Pre-audit only; not a certified audit.",
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
    "bug bounty readiness",
  ],
  authors: [{ name: "RAADHANEX", url: "https://web3guard.ai" }],
  creator: "RAADHANEX",
  metadataBase: new URL("https://web3guard-raadhanex.vercel.app"),
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://web3guard-raadhanex.vercel.app",
    siteName: "Web3Guard AI",
    title: "Web3Guard AI — Web3 Launch Readiness Scanner",
    description:
      "Check launch readiness across websites, dApps, APIs, Solidity code, wallet UX, GitHub, and admin OpSec. Public beta. Pre-audit only; not a certified audit.",
    images: [{ url: "/og-image.svg", width: 1200, height: 630, alt: "Web3Guard AI — Web3 launch readiness scanner" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Web3Guard AI — Web3 Launch Readiness Scanner",
    description: "Evidence-first public beta scanner for Web3 launch readiness. Pre-audit only; not a certified audit.",
    images: ["/og-image.svg"],
    creator: "@raadhanex",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
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
