"use client";

import React from "react";
import Link from "next/link";
import {
  ChevronLeft,
  KeyRound,
  Info,
  MessageSquare,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const STEPS = [
  {
    icon: MessageSquare,
    title: "Contacta a tu docente o coordinación",
    description:
      "Escribe por el canal institucional que ya utilizas con tu institución educativa.",
  },
  {
    icon: UserCheck,
    title: "Verifica tu identidad",
    description:
      "La persona responsable confirmará tu identidad con los datos de matrícula antes de ayudarte.",
  },
  {
    icon: ShieldCheck,
    title: "Recibe indicaciones",
    description:
      "Cuando el restablecimiento esté habilitado para tu cuenta, coordinación te indicará el siguiente paso.",
  },
];

export default function PasswordRecoveryPage() {
  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col justify-between py-12 px-6">
      <div className="max-w-lg mx-auto w-full space-y-6 my-auto">
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
              Esta pantalla no restablece contraseñas automáticamente. Para
              proteger tu cuenta, el cambio de acceso se coordina con tu
              institución educativa.
            </p>
          </div>

          {/* Honest status notice */}
          <div
            role="status"
            className="rounded-2xl bg-amber-50 border border-amber-200/80 p-4 space-y-1.5"
          >
            <p className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-amber-700 flex-shrink-0" />
              Restablecimiento automático no disponible
            </p>
            <p className="text-[11px] text-amber-900/90 leading-relaxed">
              La plataforma todavía no expone un flujo verificado de recuperación
              por correo o PIN. Esta pantalla no envía mensajes ni simula cambios
              de contraseña.
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.title}
                  className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50/60 p-3.5"
                >
                  <div className="h-8 w-8 rounded-xl bg-white border border-slate-200 text-teal-700 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-slate-900">
                      {index + 1}. {step.title}
                    </p>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-1">
            <Link href="/login" className="block">
              <Button className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs h-11 transition-all">
                Volver a iniciar sesión
              </Button>
            </Link>
          </div>
        </Card>

        <p className="text-[11px] text-slate-400 text-center leading-relaxed">
          Si ya tienes una contraseña vigente, puedes iniciar sesión normalmente.
          No compartas tu contraseña con otras personas.
        </p>
      </div>
    </div>
  );
}
