"use client";

import { usePathname } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { PreAuditRibbon } from "@/components/layout/PreAuditRibbon";
import { ScrollProgress } from "@/components/layout/ScrollProgress";

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
      <Header />
      <PreAuditRibbon />
      <main id="main-content">{children}</main>
      <Footer />
      <CommandPalette />
    </>
  );
}
