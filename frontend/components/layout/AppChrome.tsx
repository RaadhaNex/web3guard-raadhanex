"use client";

import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PreAuditRibbon } from "@/components/layout/PreAuditRibbon";

const CommandPalette = dynamic(
  () => import("@/components/layout/CommandPalette").then((mod) => mod.CommandPalette),
  { ssr: false, loading: () => null }
);

const ScrollProgress = dynamic(
  () => import("@/components/layout/ScrollProgress").then((mod) => mod.ScrollProgress),
  { ssr: false, loading: () => null }
);

const ScrollMotionController = dynamic(
  () => import("@/components/motion/ScrollMotionController").then((mod) => mod.ScrollMotionController),
  { ssr: false, loading: () => null }
);

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const isAuthPage =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname.startsWith("/auth");

  if (isAuthPage) {
    return <main>{children}</main>;
  }

  return (
    <>
      <ScrollProgress />
      <ScrollMotionController />
      <Header />
      <PreAuditRibbon />
      <main id="main-content">{children}</main>
      <Footer />
      <CommandPalette />
    </>
  );
}
