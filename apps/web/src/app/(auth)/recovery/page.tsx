"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  ChevronLeft,
  KeyRound,
  ShieldAlert,
  CheckCircle,
  HelpCircle,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PasswordRecoveryPage() {
  const router = useRouter();
  const [method, setMethod] = useState<"pin" | "backup_code">("pin");
  const [identifier, setIdentifier] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleRecoverySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      setIsSuccess(true);
    }, 700);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col justify-between py-12 px-6">
      <div className="max-w-md mx-auto w-full space-y-6 my-auto">
        {/* Back Link */}
        <div>
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Volver a iniciar sesión
          </Link>
        </div>

        {/* Card */}
        <Card className="rounded-3xl border-slate-200/80 p-8 shadow-xs bg-white space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <div className="h-10 w-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <KeyRound className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Recuperar acceso
            </h1>
            <p className="text-xs text-slate-500 leading-relaxed">
              Por seguridad y protección a menores (Ley N° 29733), la plataforma
              no utiliza correos personales externos. Puedes restablecer tu clave
              con un PIN escolar o tu clave de respaldo.
            </p>
          </div>

          {isSuccess ? (
            <div className="p-6 rounded-2xl bg-[#ecfdf5] border border-[#a7f3d0] text-center space-y-3">
              <div className="h-12 w-12 rounded-full bg-[#d1fae5] text-[#059669] flex items-center justify-center mx-auto">
                <CheckCircle className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-[#065f46]">
                ¡Contraseña actualizada con éxito!
              </h3>
              <p className="text-xs text-[#047857]">
                Ya puedes ingresar a la plataforma con tu nueva contraseña.
              </p>
              <div className="pt-2">
                <Link href="/login" className="block">
                  <Button className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs h-10 transition-all">
                    Ir a iniciar sesión
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              {/* Method Selector Tabs */}
              <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 border border-slate-200/80 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setMethod("pin")}
                  className={`py-2 px-3 rounded-lg transition-all ${
                    method === "pin"
                      ? "bg-white text-slate-900 shadow-2xs"
                      : "text-slate-500 hover:text-slate-900"
                  }`}
                >
                  PIN de Docente (OTP)
                </button>
                <button
                  type="button"
                  onClick={() => setMethod("backup_code")}
                  className={`py-2 px-3 rounded-lg transition-all ${
                    method === "backup_code"
                      ? "bg-white text-slate-900 shadow-2xs"
                      : "text-slate-500 hover:text-slate-900"
                  }`}
                >
                  Clave de Respaldo
                </button>
              </div>

              {/* Recovery Form */}
              <form onSubmit={handleRecoverySubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">
                    Código de estudiante o usuario
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="ej. EST-501 o lucia.mendoza@nexo.edu.pe"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className="w-full h-10 px-3.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">
                    {method === "pin"
                      ? "PIN temporal de 6 dígitos (solicítalo a tu docente)"
                      : "Clave de respaldo institucional (8 dígitos)"}
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={method === "pin" ? 6 : 12}
                    placeholder={method === "pin" ? "123456" : "NX-882194"}
                    value={recoveryCode}
                    onChange={(e) => setRecoveryCode(e.target.value)}
                    className="w-full h-10 px-3.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800 tracking-wider font-mono font-bold"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">
                    Nueva contraseña
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="Al menos 8 caracteres"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full h-10 px-3.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={isLoading || !identifier || !recoveryCode || !newPassword}
                  className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs h-11 shadow-sm mt-2 transition-all"
                >
                  {isLoading ? "Validando código..." : "Restablecer contraseña"}
                </Button>
              </form>

              {/* Informative Help Box */}
              <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200/70 text-[11px] text-amber-900 leading-relaxed space-y-1">
                <p className="font-bold flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
                  ¿Cómo obtener tu PIN de docente?
                </p>
                <p className="text-amber-800/90">
                  En el aula o laboratorio, tu profesor de Ciencias puede presionar
                  "Generar PIN de recuperación" desde su panel de control para
                  habilitarte el cambio de clave al instante.
                </p>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
