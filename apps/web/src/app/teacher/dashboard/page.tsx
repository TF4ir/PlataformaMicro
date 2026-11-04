"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  BookOpen,
  Award,
  TrendingUp,
  AlertCircle,
  ChevronRight,
  ShieldCheck,
  Sparkles,
  ClipboardCheck,
  FileQuestion,
  ChevronDown,
  ArrowUpRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  getTeacherDashboard,
  TeacherDashboardResponse,
} from "@/lib/api/teacher";

export default function TeacherDashboardPage() {
  const [data, setData] = useState<TeacherDashboardResponse | null>(null);
  const [selectedSectionId, setSelectedSectionId] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async (sectionId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await getTeacherDashboard(sectionId === "all" ? undefined : sectionId);
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar datos del panel docente";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard(selectedSectionId);
  }, [selectedSectionId]);

  if (loading && !data) {
    return (
      <div className="space-y-8 pb-12 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
        </div>
        <div className="h-72 bg-slate-100 rounded-3xl" />
      </div>
    );
  }

  const teacherName = data?.teacher_name || "Docente";
  const dist = data?.proficiency_distribution || { requiring_reinforcement: 0, in_progress: 0, consolidated: 0 };
  const totalStudentsInDist = dist.requiring_reinforcement + dist.in_progress + dist.consolidated || 1;

  const pctConsolidated = Math.round((dist.consolidated / totalStudentsInDist) * 100);
  const pctInProgress = Math.round((dist.in_progress / totalStudentsInDist) * 100);
  const pctRequiring = Math.round((dist.requiring_reinforcement / totalStudentsInDist) * 100);

  return (
    <div className="space-y-8 pb-12">
      {/* Header with Section Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            PANEL DOCENTE · SEGUIMIENTO PEDAGÓGICO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Bienvenida, {teacherName}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Supervisa el avance conceptual y la dinámica de retención de tus secciones de 5.° de secundaria.
          </p>
        </div>

        {/* Section Filter Dropdown */}
        <div className="relative inline-block">
          <select
            value={selectedSectionId}
            onChange={(e) => setSelectedSectionId(e.target.value)}
            className="appearance-none bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl pl-4 pr-10 py-2.5 shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          >
            <option value="all">Todas las secciones asignadas</option>
            {data?.sections.map((sec) => (
              <option key={sec.id} value={sec.id}>
                {sec.name} ({sec.course_name})
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Top-level KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Estudiantes matriculados</p>
            <div className="h-8 w-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data?.total_students ?? 0}</p>
          <p className="text-xs text-slate-500">{data?.total_sections ?? 0} secciones asignadas</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Cursos asignados</p>
            <div className="h-8 w-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data?.total_courses ?? 0}</p>
          <p className="text-xs text-slate-500">{data?.published_activities ?? 0} actividades publicadas</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Precisión observada</p>
            <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data?.average_accuracy ?? 0}%</p>
          <p className="text-xs text-emerald-600 font-semibold">{data?.total_attempts ?? 0} intentos completados</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Repasos adaptativos</p>
            <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{data?.completed_reviews_count ?? 0}</p>
          <p className="text-xs text-slate-500">
            {data?.active_recommendations_count ?? 0} recomendaciones activas
          </p>
        </Card>
      </div>

      {/* Proficiency Distribution Overview (Captura 20) */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Distribución de nivel de consolidación
            </h2>
            <p className="text-xs text-slate-500">
              Clasificación de estudiantes según su historial de aciertos y probabilidad de retención
            </p>
          </div>
          <Link href="/teacher/students">
            <Button variant="outline" size="sm" className="rounded-xl text-xs gap-1.5">
              Ver directorio de alumnos
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>

        {/* Multi-segmented Progress Bar */}
        <div className="space-y-3">
          <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden flex">
            <div
              style={{ width: `${pctConsolidated}%` }}
              className="bg-emerald-500 h-full transition-all"
              title={`Consolidados: ${dist.consolidated} (${pctConsolidated}%)`}
            />
            <div
              style={{ width: `${pctInProgress}%` }}
              className="bg-amber-400 h-full transition-all"
              title={`En proceso: ${dist.in_progress} (${pctInProgress}%)`}
            />
            <div
              style={{ width: `${pctRequiring}%` }}
              className="bg-rose-400 h-full transition-all"
              title={`Refuerzo sugerido: ${dist.requiring_reinforcement} (${pctRequiring}%)`}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-emerald-50/70 border border-emerald-100">
              <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-emerald-950">
                  Consolidados ({dist.consolidated})
                </p>
                <p className="text-[11px] text-emerald-800">
                  {pctConsolidated}% · Retención &gt; 80%
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-amber-50/70 border border-amber-100">
              <div className="w-3.5 h-3.5 rounded-full bg-amber-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-amber-950">
                  En proceso ({dist.in_progress})
                </p>
                <p className="text-[11px] text-amber-800">
                  {pctInProgress}% · Precisión 60% – 79%
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-rose-50/70 border border-rose-100">
              <div className="w-3.5 h-3.5 rounded-full bg-rose-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-rose-950">
                  Refuerzo sugerido ({dist.requiring_reinforcement})
                </p>
                <p className="text-[11px] text-rose-800">
                  {pctRequiring}% · Precisión &lt; 60%
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Two Column Grid: Students Needing Reinforcement vs Students on Track (Capturas 20 & 21) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Requiring Reinforcement */}
        <Card className="rounded-3xl border-slate-200/80 p-6 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <h3 className="text-lg font-bold text-slate-900">
                Estudiantes con necesidad de refuerzo
              </h3>
            </div>
            <Badge variant="warning" className="text-xs">
              {data?.students_requiring_reinforcement.length ?? 0} detectados
            </Badge>
          </div>

          {data?.students_requiring_reinforcement.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No hay estudiantes que requieran refuerzo urgente en este filtro.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {data?.students_requiring_reinforcement.map((st) => (
                <div key={st.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 truncate">{st.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({st.code || "EST"})</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {st.section_name} · Concepto vulnerable:{" "}
                      <span className="text-rose-700 font-medium">{st.weak_kc_name || "En evaluación"}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md">
                      {st.accuracy}%
                    </span>
                    <Link href={`/teacher/students?search=${encodeURIComponent(st.name)}`}>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400 hover:text-slate-700">
                        <ArrowUpRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Right Column: Students on Track */}
        <Card className="rounded-3xl border-slate-200/80 p-6 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <h3 className="text-lg font-bold text-slate-900">
                Estudiantes con retención consolidada
              </h3>
            </div>
            <Badge variant="success" className="text-xs">
              {data?.students_on_track.length ?? 0} al día
            </Badge>
          </div>

          {data?.students_on_track.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              Aún no hay estudiantes en categoría consolidada para este filtro.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {data?.students_on_track.map((st) => (
                <div key={st.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 truncate">{st.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({st.code || "EST"})</span>
                    </div>
                    <p className="text-[11px] text-slate-500">{st.section_name} · Retención alta</p>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      {st.accuracy}%
                    </span>
                    <Link href={`/teacher/students?search=${encodeURIComponent(st.name)}`}>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400 hover:text-slate-700">
                        <ArrowUpRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-2">
        <Link href="/teacher/activities">
          <Card className="rounded-2xl border-slate-200/80 p-5 bg-white shadow-xs hover:border-teal-300 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                    Cuestionarios
                  </h4>
                  <p className="text-[11px] text-slate-500">Crear y publicar actividades</p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-700" />
            </div>
          </Card>
        </Link>

        <Link href="/teacher/questions">
          <Card className="rounded-2xl border-slate-200/80 p-5 bg-white shadow-xs hover:border-teal-300 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                  <FileQuestion className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                    Banco de preguntas
                  </h4>
                  <p className="text-[11px] text-slate-500">Generación y aprobación M3</p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-700" />
            </div>
          </Card>
        </Link>

        <Link href="/teacher/reports">
          <Card className="rounded-2xl border-slate-200/80 p-5 bg-white shadow-xs hover:border-teal-300 transition-all group">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                    Reportes de retención
                  </h4>
                  <p className="text-[11px] text-slate-500">Curvas de memoria y calor</p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-700" />
            </div>
          </Card>
        </Link>
      </div>
    </div>
  );
}
