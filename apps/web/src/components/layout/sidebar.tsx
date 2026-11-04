"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  BookOpen,
  BarChart2,
  Layers,
  Sparkles,
  Users,
  FileQuestion,
  TrendingUp,
  LogOut,
  X,
  ShieldCheck,
  ClipboardCheck,
} from "lucide-react";
import { useRole } from "@/lib/role-context";
import { mockStudent, mockTeacher } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();
  const { role, isMobileMenuOpen, setIsMobileMenuOpen, logout, currentUser } =
    useRole();

  const studentNavItems = [
    { label: "Inicio", href: "/dashboard", icon: Home },
    { label: "Mis cursos", href: "/courses", icon: BookOpen },
    { label: "Mi progreso", href: "/progress", icon: BarChart2 },
    { label: "Estados del sistema", href: "/system-status", icon: Layers },
  ];

  const teacherNavItems = [
    { label: "Dashboard", href: "/teacher/dashboard", icon: Home },
    { label: "Cursos", href: "/teacher/courses", icon: BookOpen },
    { label: "Cuestionarios", href: "/teacher/activities", icon: ClipboardCheck },
    { label: "Banco de preguntas", href: "/teacher/questions", icon: FileQuestion },
    { label: "Estudiantes", href: "/teacher/students", icon: Users },
    { label: "Reportes", href: "/teacher/reports", icon: TrendingUp },
    { label: "Estados del sistema", href: "/system-status", icon: Layers },
  ];

  const isTeacherPath = pathname.startsWith("/teacher");
  const effectiveRole = isTeacherPath ? "teacher" : role;
  const navItems = effectiveRole === "student" ? studentNavItems : teacherNavItems;

  const currentName =
    currentUser?.name ||
    (effectiveRole === "student" ? mockStudent.name : mockTeacher.name);
  const currentInitials =
    effectiveRole === "student" ? mockStudent.initials : mockTeacher.initials;
  const currentDetail =
    effectiveRole === "student" ? mockStudent.grade : mockTeacher.roleTitle;
  const currentCode =
    currentUser?.code || (effectiveRole === "student" ? "EST-501" : "DOC-101");

  return (
    <>
      {/* Mobile Drawer Overlay Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-950/70 z-40 lg:hidden backdrop-blur-xs transition-opacity duration-300"
          onClick={() => setIsMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "bg-[#0B2D34] text-white flex flex-col justify-between border-r border-[#123E45] z-40",
          "fixed top-0 bottom-0 left-0 h-full overflow-y-auto transition-transform duration-300 ease-in-out",
          "[&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-[#0A635F] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent",
          // Mobile: w-72, off-canvas unless open
          "w-72 max-w-[85vw]",
          isMobileMenuOpen ? "translate-x-0 shadow-2xl z-50" : "-translate-x-full",
          // Desktop (lg): w-64, always fixed and visible
          "lg:w-64 lg:translate-x-0"
        )}
      >
        {/* Top Brand & Navigation */}
        <div>
          {/* Brand Header */}
          <div className="p-5 sm:p-6 flex items-center justify-between border-b border-[#123E45]/80">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-[#69D7C9] text-[#0B2D34] flex items-center justify-center shadow-md shadow-[#39BEAD]/20 flex-shrink-0">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white leading-none">
                  Nexo
                </h1>
                <p className="text-[11px] text-[#69D7C9]/90 mt-1">
                  Aprende a tu ritmo
                </p>
              </div>
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-[#123E45] transition-colors"
              aria-label="Cerrar menú"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Role Status Tag */}
          <div className="px-5 pt-4 pb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#69D7C9]/80">
              {effectiveRole === "student" ? "MI ESPACIO" : "GESTIÓN DOCENTE"}
            </span>
            <span
              className={cn(
                "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider",
                effectiveRole === "student"
                  ? "bg-[#072428] text-[#69D7C9] border border-[#123E45]"
                  : "bg-amber-950/80 text-amber-300 border border-amber-800/80"
              )}
            >
              {effectiveRole === "student" ? "Alumno" : "Docente"}
            </span>
          </div>

          {/* Navigation Items */}
          <nav className="px-3 py-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" &&
                  item.href !== "/teacher/dashboard" &&
                  pathname.startsWith(item.href + "/"));

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all min-h-[44px]",
                    isActive
                      ? "bg-[#0A635F] text-[#69D7C9] shadow-inner font-semibold"
                      : "text-slate-300 hover:bg-[#123E45]/80 hover:text-white"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-5 w-5 flex-shrink-0",
                      isActive ? "text-[#69D7C9]" : "text-slate-400"
                    )}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom Profile & Logout Area */}
        <div className="p-4 space-y-3 border-t border-[#123E45]/80 bg-[#072428]/60">
          {/* Profile Card */}
          <div className="flex items-center gap-3 p-2 rounded-xl bg-[#072428] border border-[#123E45]">
            <div
              className={cn(
                "h-10 w-10 rounded-full font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-xs",
                effectiveRole === "student"
                  ? "bg-[#69D7C9] text-[#0B2D34]"
                  : "bg-[#f59e0b] text-amber-950"
              )}
            >
              {currentInitials}
            </div>
            <div className="truncate flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">
                {currentName}
              </p>
              <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                <span className="truncate">{currentDetail}</span>
                <span>·</span>
                <span className="font-mono text-[10px] text-[#69D7C9]">
                  {currentCode}
                </span>
              </div>
            </div>
          </div>

          {/* Secure Institutional Badge */}
          <div className="flex items-center justify-between px-1 text-[10px] text-[#69D7C9]/80">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-[#69D7C9]" /> Sesión institucional
            </span>
            <span>5.° Secundaria</span>
          </div>

          {/* Explicit Logout Button */}
          <button
            onClick={() => {
              setIsMobileMenuOpen(false);
              logout();
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-xs font-semibold text-rose-300 bg-rose-950/30 border border-rose-900/40 hover:bg-rose-900/40 hover:text-rose-100 transition-colors min-h-[44px]"
            title="Cerrar sesión"
          >
            <LogOut className="h-4 w-4" />
            <span>Cerrar sesión</span>
          </button>
        </div>
      </aside>
    </>
  );
}
