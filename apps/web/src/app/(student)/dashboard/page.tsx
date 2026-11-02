"use client";

import React from "react";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  BarChart3,
  Sparkles,
  FileText,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { mockStudent, mockStudentAnalytics } from "@/lib/mock-data";

export default function StudentDashboardPage() {
  return (
    <div className="space-y-8 pb-12">
      {/* Header Greeting */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
          LUNES, 20 DE MAYO
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Hola, {mockStudent.name.split(" ")[0]}
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Tienes una sesión breve preparada para mantener frescos tus aprendizajes.
        </p>
      </div>

      {/* Hero Adaptive Card */}
      <div
        className="relative overflow-hidden rounded-3xl p-8 md:p-10 text-white shadow-lg"
        style={{
          background:
            "radial-gradient(circle at 85% 50%, rgba(57, 190, 173, 0.22), transparent 45%), linear-gradient(145deg, #0B2D34 0%, #123E45 54%, #0A635F 100%)",
        }}
      >
        {/* Decorative Circular Ripples */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2 hidden lg:flex items-center justify-center pointer-events-none">
          <div className="relative flex items-center justify-center">
            <div className="w-64 h-64 rounded-full border border-[#65D7C9]/20 flex items-center justify-center">
              <div className="w-48 h-48 rounded-full border border-[#65D7C9]/30 flex items-center justify-center">
                <div className="w-32 h-32 rounded-full border border-[#65D7C9]/40 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-[#fde68a] text-amber-900 flex items-center justify-center shadow-lg shadow-amber-500/20">
                    <Sparkles className="w-8 h-8 text-amber-700 animate-pulse" />
                  </div>
                </div>
              </div>
            </div>
            {/* Soft decorative ambient leaves */}
            <div className="absolute top-2 left-6 w-12 h-6 bg-[#69D7C9]/40 rounded-full blur-[1px] transform -rotate-45" />
            <div className="absolute bottom-4 right-10 w-14 h-6 bg-[#34d399]/40 rounded-full blur-[1px] transform rotate-12" />
          </div>
        </div>

        <div className="max-w-xl relative z-10 space-y-4">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#0B2D34]/80 backdrop-blur-sm px-3.5 py-1 text-xs font-medium text-[#69D7C9] border border-[#65D7C9]/30">
            <Sparkles className="w-3.5 h-3.5 text-[#69D7C9]" />
            Recomendado para hoy
          </span>

          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Refuerza la fotosíntesis
          </h2>

          <p className="text-teal-100/90 text-sm leading-relaxed">
            Un repaso breve ahora puede ayudarte a recordar mejor este concepto
            en tu próxima evaluación.
          </p>

          <div className="flex flex-wrap items-center gap-4 text-xs text-teal-200/90 pt-1">
            <div className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              <span>8 minutos</span>
            </div>
            <div className="flex items-center gap-1.5">
              <FileText className="w-4 h-4" />
              <span>Microlección + 3 preguntas</span>
            </div>
          </div>

          <div className="pt-2">
            <Link href="/recommendations/rec-fotosintesis">
              <Button
                size="lg"
                className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-md transition-all"
              >
                Comenzar repaso
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Tu Panorama (Weekly Stats) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Tu panorama</h2>
          <p className="text-xs text-slate-500">Avance de esta semana</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Stat 1: Learning time */}
          <Card className="rounded-2xl border-slate-200/70 p-6 shadow-xs">
            <div className="flex flex-col justify-between h-full space-y-4">
              <div className="h-10 w-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-900">
                  {mockStudentAnalytics.weeklyLearningMinutes} min
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Tiempo de aprendizaje
                </p>
              </div>
              <p className="text-xs font-semibold text-emerald-600">
                ↑ {mockStudentAnalytics.weeklyDeltaPercentage}% vs. semana anterior
              </p>
            </div>
          </Card>

          {/* Stat 2: Reviewed concepts */}
          <Card className="rounded-2xl border-slate-200/70 p-6 shadow-xs">
            <div className="flex flex-col justify-between h-full space-y-4">
              <div className="h-10 w-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-900">
                  {mockStudentAnalytics.reviewedConceptsCount}
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Conceptos repasados
                </p>
              </div>
              <p className="text-xs font-medium text-slate-500">
                Meta semanal: {mockStudentAnalytics.weeklyTargetCount}
              </p>
            </div>
          </Card>

          {/* Stat 3: Overall progress */}
          <Card className="rounded-2xl border-slate-200/70 p-6 shadow-xs">
            <div className="flex flex-col justify-between h-full space-y-4">
              <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-900">
                  {mockStudentAnalytics.overallProgress}%
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Progreso general
                </p>
              </div>
              <div className="w-full">
                <Progress
                  value={mockStudentAnalytics.overallProgress}
                  className="h-2 bg-slate-100"
                  indicatorClassName="bg-gradient-to-r from-amber-500 to-teal-600"
                />
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Two Column Section: Mis Cursos & Próximos Repasos */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Mis Cursos (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Mis cursos</h2>
              <p className="text-xs text-slate-500">Continúa donde lo dejaste</p>
            </div>
            <Link
              href="/courses"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1"
            >
              Ver todos <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <Link href="/courses" className="block group">
            <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs hover:border-teal-300 hover:shadow-sm transition-all">
              <div className="flex items-center gap-4">
                {/* Course Graphic Thumbnail */}
                <div className="w-20 h-20 rounded-2xl bg-[#edf8f5] flex items-center justify-center flex-shrink-0 border border-[#d1fae5]/60 relative overflow-hidden">
                  <div className="w-10 h-10 rounded-full border-2 border-emerald-500/40 flex items-center justify-center">
                    <div className="w-4 h-4 rounded-full bg-amber-400" />
                  </div>
                  <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-purple-500" />
                  <div className="absolute bottom-2 left-2 w-2 h-2 rounded-full bg-teal-600" />
                </div>

                <div className="flex-1 min-w-0 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <Badge variant="success" className="text-[10px] px-2 py-0.5">
                      EN CURSO
                    </Badge>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                    Ciencias
                  </h3>
                  <p className="text-xs text-slate-500">
                    3 de 4 unidades · 18 conceptos
                  </p>
                  <div className="pt-1 flex items-center gap-3">
                    <div className="flex-1">
                      <Progress value={72} className="h-1.5" />
                    </div>
                    <span className="text-xs font-bold text-slate-700">72%</span>
                  </div>
                </div>

                <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
              </div>
            </Card>
          </Link>
        </div>

        {/* Próximos Repasos (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Próximos repasos</h2>
            <p className="text-xs text-slate-500">Organizados según tu aprendizaje</p>
          </div>

          <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs divide-y divide-slate-100">
            {/* Repaso 1: Fotosíntesis */}
            <div className="py-3 first:pt-1 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-amber-50 text-amber-900 flex flex-col items-center justify-center flex-shrink-0 border border-amber-200/60">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-amber-700">
                    HOY
                  </span>
                  <span className="text-sm font-extrabold leading-none">20</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Fotosíntesis</h4>
                  <p className="text-xs text-slate-500">Ciencias · 8 min</p>
                </div>
              </div>
              <Badge variant="warning" className="text-[10px] font-semibold bg-[#fef3c7] text-[#92400e]">
                Prioridad
              </Badge>
            </div>

            {/* Repaso 2: Respiración celular */}
            <div className="py-3 last:pb-1 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-slate-50 text-slate-700 flex flex-col items-center justify-center flex-shrink-0 border border-slate-200/60">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                    MIÉ
                  </span>
                  <span className="text-sm font-extrabold leading-none">22</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">
                    Respiración celular
                  </h4>
                  <p className="text-xs text-slate-500">Ciencias · 6 min</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
