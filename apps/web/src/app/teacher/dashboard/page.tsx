"use client";

import React from "react";
import Link from "next/link";
import {
  Users,
  BookOpen,
  Award,
  TrendingUp,
  AlertCircle,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { mockTeacher, mockCourses } from "@/lib/mock-data";

export default function TeacherDashboardPage() {
  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
          PANEL DOCENTE
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Bienvenida, {mockTeacher.name}
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Supervisa el avance conceptual y la dinámica de retención de tus
          secciones de 5.° de secundaria.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Estudiantes activos</p>
            <div className="h-8 w-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">84</p>
          <p className="text-xs text-slate-500">3 secciones de 5.° año</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Cursos asignados</p>
            <div className="h-8 w-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">1</p>
          <p className="text-xs text-slate-500">Ciencias (1 en borrador)</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Precisión promedio</p>
            <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">79.4%</p>
          <p className="text-xs text-emerald-600 font-semibold">↑ 4.2% vs. mes anterior</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Conceptos en repaso</p>
            <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">7</p>
          <p className="text-xs text-slate-500">Fotosíntesis prioritario</p>
        </Card>
      </div>

      {/* Course Overview Quick Action */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Curso activo: Ciencias (5.° de secundaria)
            </h2>
            <p className="text-xs text-slate-500">
              4 unidades programadas · 18 componentes de conocimiento (KC)
            </p>
          </div>
          <Link href="/teacher/courses">
            <Button
              variant="outline"
              className="rounded-xl text-xs font-semibold gap-1.5"
            >
              Ver gestión completa
              <ChevronRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>

        {/* Section breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs font-bold">
              <span>Sección 5.° A</span>
              <span className="text-emerald-700">83% precisión</span>
            </div>
            <p className="text-[11px] text-slate-500">28 estudiantes · 92% participación</p>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs font-bold">
              <span>Sección 5.° B</span>
              <span className="text-emerald-700">78% precisión</span>
            </div>
            <p className="text-[11px] text-slate-500">29 estudiantes · 88% participación</p>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs font-bold">
              <span>Sección 5.° C</span>
              <span className="text-emerald-700">76% precisión</span>
            </div>
            <p className="text-[11px] text-slate-500">27 estudiantes · 85% participación</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
