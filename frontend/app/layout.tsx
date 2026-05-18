import type { Metadata } from "next";
import "./globals.css";
import { AppChrome } from "@/components/layout/AppChrome";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata: Metadata = {
  title: {
    default: "Web3Guard AI — Smart Contract Security Review | RAADHANEX",
    template: "%s | Web3Guard AI",
  },
  description:
    "AI-assisted Web3 launch security review for smart contracts, websites, dApps, APIs, wallet flows, and admin OpSec. Affordable pre-audit from ₹999. Hindi support. UPI payments.",
  keywords: [
    "web3 security", "smart contract audit", "solidity scanner", "web3 india",
    "smart contract security", "dapp security", "blockchain security",
    "pre-audit review", "web3 launch security", "solidity vulnerability scanner",
    "web3 security tool india", "affordable smart contract audit",
  ],
  authors: [{ name: "RAADHANEX", url: "https://web3guard.ai" }],
  creator: "RAADHANEX",
  metadataBase: new URL("https://web3guard-raadhanex.vercel.app"),
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://web3guard-raadhanex.vercel.app",
    siteName: "Web3Guard AI",
    title: "Web3Guard AI — Smart Contract Security Review Before Launch",
    description:
      "Check smart contracts, websites, dApps, APIs, wallet flows, and admin risks before launch. Affordable AI-assisted pre-audit from ₹999. Built for Indian Web3 builders.",
    images: [{ url: "/og-image.svg", width: 1200, height: 630, alt: "Web3Guard AI — AI-assisted Web3 launch security review" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Web3Guard AI — Affordable Web3 Security Review",
    description: "AI-assisted pre-audit for smart contracts, websites, and dApps. From ₹999. Hindi support.",
    images: ["/og-image.svg"],
    creator: "@raadhanex",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
  },
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#05070d" },
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
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
