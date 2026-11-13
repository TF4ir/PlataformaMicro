"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Sparkles,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ChevronRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  BookOpen,
  Users,
  Check,
  LogIn,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRole } from "@/lib/role-context";
import { normalizeRole, portalRoleFor } from "@/lib/auth/authorization";
import { UserRole } from "@/types/ui";
import { cn } from "@/lib/utils";
import { SolarSystemOrbit } from "@/components/auth/solar-system-orbit";

function LoginFormContent() {
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect") || undefined;
  const { login } = useRole();

  const isDemoAllowed =
    process.env.NODE_ENV !== "production" &&
    process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH === "true";

  // Active role portal selection
  const [selectedRole, setSelectedRole] = useState<UserRole>("student");
  const [mobileTab, setMobileTab] = useState<"login" | "about">("login");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // If redirect query was pointing to /teacher, set default tab to teacher
  useEffect(() => {
    if (redirectParam?.startsWith("/teacher")) {
      setSelectedRole("teacher");
    }
  }, [redirectParam]);

  const handleRoleTabChange = (role: UserRole) => {
    setSelectedRole(role);
    setErrorMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    const cleanIdentifier = identifier.trim().toLowerCase();

    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();

      const emailToUse = cleanIdentifier.includes("@")
        ? cleanIdentifier
        : `${cleanIdentifier}@nexo.edu.pe`;

      const { data: authData, error: authError } =
        await supabase.auth.signInWithPassword({
          email: emailToUse,
          password: password,
        });

      if (authError) {
        setErrorMessage(
          authError.message === "Invalid login credentials"
            ? "Credenciales incorrectas. Verifica tu correo institucional y contraseña."
            : `Error de inicio de sesión: ${authError.message}`
        );
        setIsLoading(false);
        return;
      }

      // Supabase authenticated successfully. The role MUST come from the
      // authoritative profiles table, never from client metadata/cookies.
      const { data: profile, error: profileError } = await supabase
        .from("profiles")
        .select("id, full_name, role, student_code")
        .eq("id", authData.user.id)
        .maybeSingle();

      const verifiedRole = normalizeRole(profile?.role);
      const userRole = portalRoleFor(verifiedRole);

      if (profileError || !profile || !verifiedRole || !userRole) {
        await supabase.auth.signOut();
        setErrorMessage(
          "Tu cuenta no tiene un perfil institucional habilitado. Contacta a coordinación para regularizar tu acceso."
        );
        setIsLoading(false);
        return;
      }

      // Privilege check: ensure user logged into the matching portal
      if (userRole !== selectedRole) {
        await supabase.auth.signOut();
        setErrorMessage(
          `Acceso denegado: Tu perfil institucional está registrado como ${
            userRole === "teacher" ? "Docente" : "Estudiante"
          }. Por favor, selecciona la opción '${
            userRole === "teacher" ? "Docente" : "Estudiante"
          }'.`
        );
        setIsLoading(false);
        return;
      }

      login(
        {
          id: profile.id,
          name: profile.full_name || "Usuario Nexo",
          email: authData.user.email || "",
          role: userRole,
          code: profile.student_code || undefined,
        },
        redirectParam
      );
    } catch (err: any) {
      setErrorMessage(
        err?.message || "Ocurrió un error inesperado al conectar con el servidor."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Quick Demo Access helper
  const fillCredentials = (type: UserRole) => {
    setSelectedRole(type);
    setErrorMessage(null);
    if (type === "student") {
      setIdentifier("lucia.mendoza@nexo.edu.pe");
      setPassword("Nexo2026!");
    } else {
      setIdentifier("ana.garcia@nexo.edu.pe");
      setPassword("Nexo2026!");
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:grid lg:grid-cols-12 bg-white relative">
      {/* MOBILE TOP BAR & SEGMENT CONTROL (< lg) */}
      <header className="lg:hidden w-full bg-[#0B2D34] text-white px-4 pt-3.5 pb-2.5 border-b border-[#123E45] sticky top-0 z-50 shadow-md">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-[#69D7C9] text-[#0B2D34] flex items-center justify-center font-bold shadow-md shadow-[#39BEAD]/20">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <span className="text-sm font-extrabold tracking-tight text-white block leading-none">
                Nexo
              </span>
              <span className="text-[10px] text-[#69D7C9]/90 block mt-0.5">
                Aprende a tu ritmo
              </span>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#123E45] text-[#69D7C9] border border-[#39BEAD]/30">
            5° Secundaria
          </span>
        </div>

        {/* Mobile 2-Segment Control (Iniciar Sesión / Conoce Nexo) */}
        <div className="grid grid-cols-2 p-1 bg-[#123E45]/90 rounded-xl border border-[#39BEAD]/20">
          <button
            type="button"
            onClick={() => setMobileTab("login")}
            className={cn(
              "py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5",
              mobileTab === "login"
                ? "bg-[#69D7C9] text-[#0B2D34] shadow-sm font-bold"
                : "text-teal-200/80 hover:text-white"
            )}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Iniciar Sesión</span>
          </button>
          <button
            type="button"
            onClick={() => setMobileTab("about")}
            className={cn(
              "py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5",
              mobileTab === "about"
                ? "bg-[#69D7C9] text-[#0B2D34] shadow-sm font-bold"
                : "text-teal-200/80 hover:text-white"
            )}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Conoce Nexo</span>
          </button>
        </div>
      </header>

      {/* LEFT PANEL: Branding, Value Proposition & Solar System Animation (6 cols on lg) */}
      <div
        className={cn(
          "lg:col-span-6 xl:col-span-6 text-white p-6 sm:p-10 lg:p-14 flex-col justify-between relative overflow-hidden min-h-[560px] lg:min-h-screen",
          mobileTab === "about" ? "flex" : "hidden lg:flex"
        )}
        style={{
          background:
            "radial-gradient(circle at 75% 48%, rgba(57, 190, 173, 0.20), transparent 30%), linear-gradient(145deg, #0B2D34 0%, #123E45 54%, #0A635F 100%)",
        }}
      >
        {/* Subtle engineering coordinate grid overlay */}
        <div
          className="absolute inset-0 pointer-events-none opacity-25"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(105, 215, 201, 0.25) 1px, transparent 1px), linear-gradient(to bottom, rgba(105, 215, 201, 0.25) 1px, transparent 1px)",
            backgroundSize: "44px 44px",
          }}
        />

        {/* Desktop Brand Header */}
        <div className="hidden lg:flex items-center gap-3 relative z-20">
          <div className="h-10 w-10 rounded-2xl bg-[#69D7C9] text-[#0B2D34] flex items-center justify-center shadow-lg shadow-[#39BEAD]/20 flex-shrink-0">
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

        {/* Central Solar System Orbital Graphic */}
        <div className="relative my-6 lg:my-0 lg:absolute lg:right-[-140px] sm:right-[-120px] xl:right-[-120px] lg:top-[64%] lg:-translate-y-1/2 z-10 opacity-90 lg:opacity-100 pointer-events-none flex justify-center scale-[0.80] sm:scale-95 lg:scale-105 xl:scale-110">
          <SolarSystemOrbit />
        </div>

        {/* Core Value Headline (Unbreakable line rhythm with #69D7C9 turquoise accent) */}
        <div className="mt-2 mb-auto sm:mt-6 lg:mt-10 relative z-30 max-w-xl space-y-5">
          {/* Tag Pill */}
          <div className="inline-flex items-center gap-2 rounded-full bg-[#0B2D34]/90 px-3.5 py-1.5 text-xs font-semibold tracking-wider text-[#69D7C9] border border-[#65D7C9]/40 backdrop-blur-md shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#69D7C9]" />
            <span>APRENDIZAJE QUE SE ADAPTA</span>
          </div>

          {/* Unbreakable 3-Line Title: "Lo importante no es" stays strictly on 1 line */}
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-[40px] xl:text-[48px] 2xl:text-[54px] font-extrabold tracking-tight text-white leading-[1.12]">
            <span className="whitespace-nowrap">Lo importante no es</span> <br />
            <span className="whitespace-nowrap">estudiar más.</span> <br />
            <span className="whitespace-nowrap text-[#69D7C9] drop-shadow-[0_2px_16px_rgba(105,215,201,0.30)]">
              Es recordar mejor.
            </span>
          </h2>

          {/* Subheading - Warm, clean, readable */}
          <p className="text-sm sm:text-base lg:text-[17px] leading-relaxed text-teal-100/90 max-w-lg pt-1 font-normal">
            Sesiones breves, recomendaciones oportunas y progreso claro para
            convertir cada repaso en aprendizaje duradero.
          </p>
        </div>

        {/* Bottom Social Proof / Community Evidence */}
        <div className="flex items-center gap-3 pt-6 relative z-20 border-t border-[#123E45]/80">
          <div className="flex -space-x-2">
            <div className="h-7 w-7 rounded-full bg-[#f59e0b] text-amber-950 font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0B2D34]">
              LM
            </div>
            <div className="h-7 w-7 rounded-full bg-[#69D7C9] text-[#0B2D34] font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0B2D34]">
              DS
            </div>
            <div className="h-7 w-7 rounded-full bg-[#c084fc] text-purple-950 font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0B2D34]">
              AG
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-white">
              Una experiencia para toda la comunidad
            </p>
            <p className="text-[11px] text-teal-200/70">
              Estudiantes y docentes avanzan con la misma evidencia.
            </p>
          </div>
        </div>

        {/* Mobile Action to Switch to Login Form */}
        <div className="lg:hidden pt-5 pb-2 relative z-30">
          <Button
            type="button"
            onClick={() => setMobileTab("login")}
            className="w-full bg-[#69D7C9] hover:bg-[#65D7C9] text-[#0B2D34] font-bold rounded-xl h-12 shadow-lg shadow-[#39BEAD]/30 gap-2 text-sm"
          >
            <span>Ir a Iniciar Sesión</span>
            <ArrowRight className="w-4 h-4 stroke-[2.5]" />
          </Button>
        </div>
      </div>

      {/* RIGHT PANEL: Login Form (6 cols on lg) */}
      <div
        className={cn(
          "lg:col-span-6 xl:col-span-6 flex flex-col justify-center items-center p-6 sm:p-10 lg:p-16 bg-white relative min-h-[calc(100vh-120px)] lg:min-h-screen",
          mobileTab === "login" ? "flex" : "hidden lg:flex"
        )}
      >
        <div className="w-full max-w-md space-y-6 sm:space-y-7">
          {/* Form Header */}
          <div className="space-y-1.5">
            <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
              TE DAMOS LA BIENVENIDA
            </p>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Ingresa a tu espacio
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Elige tu perfil para continuar con tu experiencia.
            </p>
          </div>

          {/* Role Cards: Estudiante vs Docente (Matching 11-Login-animation.png) */}
          <div className="grid grid-cols-2 gap-3">
            {/* Estudiante Card */}
            <div
              onClick={() => handleRoleTabChange("student")}
              className={cn(
                "p-3.5 rounded-2xl border-2 transition-all cursor-pointer flex items-center justify-between",
                selectedRole === "student"
                  ? "border-[#0A635F] bg-[#f0fdfa]/40 shadow-xs"
                  : "border-slate-200/90 bg-white hover:border-slate-300"
              )}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div
                  className={cn(
                    "h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors",
                    selectedRole === "student"
                      ? "bg-teal-100/80 text-[#0A635F]"
                      : "bg-slate-100 text-slate-500"
                  )}
                >
                  <BookOpen className="w-4 h-4" />
                </div>
                <div className="truncate">
                  <h3 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
                    Estudiante
                  </h3>
                  <p className="text-[11px] text-slate-500 truncate">
                    Aprender y repasar
                  </p>
                </div>
              </div>

              {/* Selection Check Circle */}
              <div
                className={cn(
                  "h-5 w-5 rounded-full flex items-center justify-center flex-shrink-0 ml-1 transition-colors",
                  selectedRole === "student"
                    ? "bg-[#0A635F] text-white"
                    : "border-2 border-slate-300"
                )}
              >
                {selectedRole === "student" && <Check className="w-3 h-3 stroke-[3]" />}
              </div>
            </div>

            {/* Docente Card */}
            <div
              onClick={() => handleRoleTabChange("teacher")}
              className={cn(
                "p-3.5 rounded-2xl border-2 transition-all cursor-pointer flex items-center justify-between",
                selectedRole === "teacher"
                  ? "border-[#0A635F] bg-[#f0fdfa]/40 shadow-xs"
                  : "border-slate-200/90 bg-white hover:border-slate-300"
              )}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div
                  className={cn(
                    "h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors",
                    selectedRole === "teacher"
                      ? "bg-teal-100/80 text-[#0A635F]"
                      : "bg-slate-100 text-slate-500"
                  )}
                >
                  <Users className="w-4 h-4" />
                </div>
                <div className="truncate">
                  <h3 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
                    Docente
                  </h3>
                  <p className="text-[11px] text-slate-500 truncate">
                    Gestionar y analizar
                  </p>
                </div>
              </div>

              {/* Selection Check Circle */}
              <div
                className={cn(
                  "h-5 w-5 rounded-full flex items-center justify-center flex-shrink-0 ml-1 transition-colors",
                  selectedRole === "teacher"
                    ? "bg-[#0A635F] text-white"
                    : "border-2 border-slate-300"
                )}
              >
                {selectedRole === "teacher" && <Check className="w-3 h-3 stroke-[3]" />}
              </div>
            </div>
          </div>

          {/* Quick Demo Pre-fill helper (Strictly hidden in production or when demo auth is disabled) */}
          {isDemoAllowed && (
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between gap-2">
              <span className="text-[10px] uppercase font-bold text-slate-400">
                ACCESO DEMO 1-CLIC:
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => fillCredentials("student")}
                  className={cn(
                    "py-1 px-2.5 rounded-lg text-xs font-semibold transition-all border",
                    selectedRole === "student"
                      ? "bg-teal-50 border-teal-300 text-teal-800"
                      : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                  )}
                >
                  🎓 Lucía
                </button>
                <button
                  type="button"
                  onClick={() => fillCredentials("teacher")}
                  className={cn(
                    "py-1 px-2.5 rounded-lg text-xs font-semibold transition-all border",
                    selectedRole === "teacher"
                      ? "bg-amber-50 border-amber-300 text-amber-900"
                      : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                  )}
                >
                  👩‍🏫 Ana
                </button>
              </div>
            </div>
          )}

          {/* Error Message Box */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-800 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span className="leading-relaxed">{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Identifier input */}
            <div className="space-y-1.5">
              <label
                htmlFor="identifier"
                className="text-xs font-semibold text-slate-700 block"
              >
                Correo institucional
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="identifier"
                  type="text"
                  required
                  value={identifier}
                  onChange={(e) => {
                    setIdentifier(e.target.value);
                    if (errorMessage) setErrorMessage(null);
                  }}
                  placeholder={
                    selectedRole === "student"
                      ? "lucia@nexo.edu"
                      : "ana@nexo.edu"
                  }
                  className="w-full h-11 pl-10 pr-4 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 focus:border-teal-600 text-slate-800 transition-all placeholder:text-slate-400 shadow-2xs"
                />
              </div>
            </div>

            {/* Password input */}
            <div className="space-y-1.5">
              <label
                htmlFor="password"
                className="text-xs font-semibold text-slate-700 block"
              >
                Contraseña
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errorMessage) setErrorMessage(null);
                  }}
                  placeholder="••••••••"
                  className="w-full h-11 pl-10 pr-10 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 focus:border-teal-600 text-slate-800 transition-all shadow-2xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                  aria-label={showPassword ? "Ocultar contraseña" : "Ver contraseña"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember me & Forgot password row */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-600 select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-300 text-[#0A635F] focus:ring-teal-500 h-4 w-4"
                />
                <span>Recordarme</span>
              </label>

              <Link
                href="/recovery"
                className="text-xs font-semibold text-[#0A635F] hover:text-[#0B2D34] hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </Link>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading || !identifier || !password}
              size="lg"
              className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl h-12 gap-2 shadow-sm transition-all text-sm mt-2"
            >
              {isLoading ? (
                "Validando credenciales..."
              ) : (
                <>
                  <span>
                    Ingresar como{" "}
                    {selectedRole === "student" ? "estudiante" : "docente"}
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Institutional note */}
          <div className="space-y-3 pt-2 text-center">
            <p className="text-xs text-slate-500 flex items-center justify-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-slate-400" />
              Acceso protegido para tu comunidad educativa
            </p>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Al continuar, aceptas los{" "}
              <span className="text-teal-700 underline cursor-pointer">
                Términos de uso
              </span>{" "}
              y la{" "}
              <span className="text-teal-700 underline cursor-pointer">
                Política de privacidad
              </span>
              .
            </p>
          </div>

          {/* Mobile presentation discovery link */}
          <div className="lg:hidden pt-1 text-center">
            <button
              type="button"
              onClick={() => setMobileTab("about")}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#0A635F] hover:text-[#0B2D34] transition-colors py-1.5 px-3 rounded-lg hover:bg-teal-50"
            >
              <span>¿Cómo funciona el repaso adaptativo?</span>
              <span className="text-[#39BEAD] font-bold">Ver presentación →</span>
            </button>
          </div>
        </div>

        {/* Floating help question button (bottom right) */}
        <button
          aria-label="Ayuda"
          className="fixed bottom-5 right-5 h-9 w-9 rounded-full bg-slate-900 text-white flex items-center justify-center shadow-lg hover:bg-slate-800 transition-colors z-30 text-xs font-bold"
        >
          ?
        </button>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#072422] flex items-center justify-center text-teal-200 text-sm font-semibold">
          Cargando portal institucional...
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}
