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
import {
  INSUFFICIENT_TEXT,
  MASTERY_THRESHOLDS,
  UNAVAILABLE_TEXT,
  formatMetricValue,
} from "@/lib/data-provenance";

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
  const dist = {
    requiring_reinforcement: data?.proficiency_distribution.requiring_reinforcement ?? 0,
    in_progress: data?.proficiency_distribution.in_progress ?? 0,
    consolidated: data?.proficiency_distribution.consolidated ?? 0,
    insufficient_evidence:
      data?.proficiency_distribution.insufficient_evidence ?? 0,
  };
  const totalStudentsInDist =
    dist.requiring_reinforcement +
    dist.in_progress +
    dist.consolidated +
    dist.insufficient_evidence;

  const percentageOf = (count: number) =>
    totalStudentsInDist > 0 ? Math.round((count / totalStudentsInDist) * 100) : 0;

  const pctConsolidated = percentageOf(dist.consolidated);
  const pctInProgress = percentageOf(dist.in_progress);
  const pctRequiring = percentageOf(dist.requiring_reinforcement);
  const pctInsufficient = percentageOf(dist.insufficient_evidence);
  // With no loaded dashboard the distribution is unknown, not a row of zeros.
  const distText = (count: number) => (data ? String(count) : "—");
  const pctText = (pct: number) => (data ? `${pct}%` : "—");

  const averageAccuracyText = data
    ? formatMetricValue(data.average_accuracy, {
        unit: "%",
        decimals: 1,
        insufficient: data.average_accuracy === null,
      })
    : UNAVAILABLE_TEXT;

  const formatStudentAccuracy = (accuracy: number | null) =>
    formatMetricValue(accuracy, {
      unit: "%",
      decimals: 1,
      insufficient: accuracy === null,
    });

  return (
    <div className="space-y-8 pb-12">
      {/* Header with Section Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            PANEL DOCENTE · SEGUIMIENTO PEDAGÓGICO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Hola, {teacherName}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Supervisa la precisión observada y el estado de consolidación de tus
            secciones de secundaria.
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
          <p className="text-3xl font-extrabold text-slate-900">
            {data ? data.total_students : UNAVAILABLE_TEXT}
          </p>
          <p className="text-xs text-slate-500">
            {data ? `${data.total_sections} secciones asignadas` : UNAVAILABLE_TEXT}
          </p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Cursos asignados</p>
            <div className="h-8 w-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">
            {data ? data.total_courses : UNAVAILABLE_TEXT}
          </p>
          <p className="text-xs text-slate-500">
            {data ? `${data.published_activities} actividades publicadas` : UNAVAILABLE_TEXT}
          </p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Precisión observada</p>
            <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{averageAccuracyText}</p>
          <p className="text-xs text-emerald-600 font-semibold">
            {data ? `${data.total_attempts} intentos completados` : UNAVAILABLE_TEXT}
          </p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-500">Repasos adaptativos</p>
            <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">
            {data ? data.completed_reviews_count : UNAVAILABLE_TEXT}
          </p>
          <p className="text-xs text-slate-500">
            {data
              ? `${data.active_recommendations_count} recomendaciones activas`
              : UNAVAILABLE_TEXT}
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
              Clasificación de estudiantes según su precisión observada en eventos
              de respuesta. Cada estudiante aparece en una sola categoría.
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
            <div
              style={{ width: `${pctInsufficient}%` }}
              className="bg-slate-300 h-full transition-all"
              title={`Sin evidencia suficiente: ${dist.insufficient_evidence} (${pctInsufficient}%)`}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            <div className="flex items-center gap-3 p-3 rounded-2xl bg-emerald-50/70 border border-emerald-100">
              <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-emerald-950">
                  Consolidados ({distText(dist.consolidated)})
                </p>
                <p className="text-[11px] text-emerald-800">
                  {pctText(pctConsolidated)} · Precisión ≥ {MASTERY_THRESHOLDS.consolidated}%
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-amber-50/70 border border-amber-100">
              <div className="w-3.5 h-3.5 rounded-full bg-amber-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-amber-950">
                  En proceso ({distText(dist.in_progress)})
                </p>
                <p className="text-[11px] text-amber-800">
                  {pctText(pctInProgress)} · Precisión {MASTERY_THRESHOLDS.inProgress}% –{" "}
                  {MASTERY_THRESHOLDS.consolidated - 1}%
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-rose-50/70 border border-rose-100">
              <div className="w-3.5 h-3.5 rounded-full bg-rose-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-rose-950">
                  Refuerzo sugerido ({distText(dist.requiring_reinforcement)})
                </p>
                <p className="text-[11px] text-rose-800">
                  {pctText(pctRequiring)} · Precisión &lt; {MASTERY_THRESHOLDS.inProgress}%
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="w-3.5 h-3.5 rounded-full bg-slate-300 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold text-slate-800">
                  Sin evidencia suficiente ({distText(dist.insufficient_evidence)})
                </p>
                <p className="text-[11px] text-slate-600">
                  {pctText(pctInsufficient)} · {INSUFFICIENT_TEXT}
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
              {data ? `${data.students_requiring_reinforcement.length} detectados` : "—"}
            </Badge>
          </div>

          {!data ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No se pudo consultar la lista: la solicitud falló.
            </div>
          ) : data.students_requiring_reinforcement.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No hay estudiantes que requieran refuerzo urgente en este filtro.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {data.students_requiring_reinforcement.map((st) => (
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
                      {formatStudentAccuracy(st.accuracy)}
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
                Estudiantes con precisión consolidada
              </h3>
            </div>
            <Badge variant="success" className="text-xs">
              {data ? `${data.students_on_track.length} consolidados` : "—"}
            </Badge>
          </div>

          {!data ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No se pudo consultar la lista: la solicitud falló.
            </div>
          ) : data.students_on_track.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              Aún no hay estudiantes en categoría consolidada para este filtro.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {data.students_on_track.map((st) => (
                <div key={st.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 truncate">{st.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({st.code || "EST"})</span>
                    </div>
                    <p className="text-[11px] text-slate-500">{st.section_name} · Precisión consolidada</p>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      {formatStudentAccuracy(st.accuracy)}
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
                    Reportes de aprendizaje
                  </h4>
                  <p className="text-[11px] text-slate-500">Precisión y mapa de calor</p>
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
