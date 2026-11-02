"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Search, Bell, Menu, Sparkles } from "lucide-react";
import { useRole } from "@/lib/role-context";

export function Header() {
  const pathname = usePathname();
  const { role, toggleMobileMenu } = useRole();
  const effectiveRole = pathname.startsWith("/teacher") ? "teacher" : role;

  const searchPlaceholder =
    effectiveRole === "student"
      ? "Buscar en mis cursos..."
      : "Buscar cursos, conceptos o estudiantes...";

  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/90 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-20 gap-3">
      {/* Mobile Hamburger & Brand */}
      <div className="flex items-center gap-3 lg:hidden">
        <button
          onClick={toggleMobileMenu}
          className="h-10 w-10 rounded-xl border border-slate-200 flex items-center justify-center text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          aria-label="Abrir menú de navegación"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-[#69D7C9] text-[#0B2D34] flex items-center justify-center shadow-xs">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-bold text-slate-900 text-base tracking-tight">
            Nexo
          </span>
        </div>
      </div>

      {/* Search Input (Fluid & Responsive) */}
      <div className="flex-1 max-w-xs sm:max-w-md lg:max-w-lg">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            className="w-full h-10 pl-10 pr-4 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0A635F]/30 focus:border-[#0A635F] transition-all text-slate-800 placeholder:text-slate-400 truncate"
          />
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        <div className="hidden sm:flex items-center">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
            {effectiveRole === "student" ? "Estudiante" : "Docente"}
          </span>
        </div>

        <button
          className="relative h-10 w-10 rounded-xl border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
          title="Notificaciones"
          aria-label="Notificaciones"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-2.5 right-2.5 h-2 w-2 rounded-full bg-[#0A635F] ring-2 ring-white" />
        </button>
      </div>
    </header>
  );
}
