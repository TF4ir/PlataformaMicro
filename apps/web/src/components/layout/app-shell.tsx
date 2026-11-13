"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { FlaskConical } from "lucide-react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { DEMO_BANNER_TEXT, isDemoModeEnabled } from "@/lib/data-provenance";

function DemoBanner() {
  if (!isDemoModeEnabled()) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full bg-amber-100 border-b border-amber-300 px-4 py-2 text-[11px] sm:text-xs font-semibold text-amber-900 flex items-center justify-center gap-2 text-center"
    >
      <FlaskConical className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
      <span>{DEMO_BANNER_TEXT}</span>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // 1. Auth routes (login, recovery) must NEVER show sidebar or top header
  const isAuthRoute =
    pathname === "/login" ||
    pathname.startsWith("/login/") ||
    pathname === "/recovery" ||
    pathname.startsWith("/recovery/");

  // 2. Focused learning views (microlesson and quiz) take full screen immersion
  const isFocusedMode =
    pathname.startsWith("/learn") || pathname.startsWith("/quiz");

  if (isAuthRoute) {
    return (
      <main className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col">
        <DemoBanner />
        {children}
      </main>
    );
  }

  if (isFocusedMode) {
    return (
      <main className="min-h-screen bg-white text-slate-900 flex flex-col">
        <DemoBanner />
        {children}
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <div className="lg:pl-64 flex flex-col min-h-screen min-w-0 w-full">
        <Header />
        <DemoBanner />
        <main className="flex-1 p-4 sm:p-6 md:p-8 lg:p-10 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
