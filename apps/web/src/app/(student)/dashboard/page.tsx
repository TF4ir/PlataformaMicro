"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  BarChart3,
  Sparkles,
  FileText,
  ChevronRight,
  AlertCircle,
  BookOpen,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { studentLearningApi, StudentDashboardResponse } from "@/lib/api/learning";

export default function StudentDashboardPage() {
  const [dashboardData, setDashboardData] = useState<StudentDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);
        const res = await studentLearningApi.getDashboard();
        if (isMounted) {
          setDashboardData(res);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Error al cargar el panel de aprendizaje";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadDashboard();
    return () => {
      isMounted = false;
    };
  }, []);

  const todayStr = new Intl.DateTimeFormat("es-PE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date()).toUpperCase();

  if (loading) {
    return (
      <div className="space-y-8 pb-12 animate-pulse">
        <div className="space-y-2">
          <div className="h-4 w-32 bg-slate-200 rounded" />
          <div className="h-8 w-64 bg-slate-200 rounded" />
          <div className="h-4 w-96 bg-slate-100 rounded" />
        </div>
        <div className="h-56 bg-slate-200 rounded-3xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
        </div>
      </div>
    );
  }

  const studentName = dashboardData?.student_name || "Estudiante";
  const upcomingReviews = dashboardData?.upcoming_reviews || [];
  const primaryReview = upcomingReviews[0];
  const analytics = dashboardData?.analytics;
  const courses = dashboardData?.enrolled_courses || [];
  const recentActivities = dashboardData?.recent_activities || [];

  return (
    <div className="space-y-8 pb-12">
      {/* Header Greeting */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
          {todayStr}
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Hola, {studentName.split(" ")[0]}
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          {primaryReview
            ? "Tienes repasos adaptativos recomendados para consolidar tu aprendizaje a largo plazo."
            : "Estás al día con tus actividades. Explora tus cursos o refuerza nuevos temas."}
        </p>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>
            No se pudo sincronizar la telemetría en tiempo real ({error}). Mostrando datos almacenados localmente.
          </span>
        </div>
      )}

      {/* Hero Adaptive Card */}
      {primaryReview ? (
        <div
          className="relative overflow-hidden rounded-3xl p-8 md:p-10 text-white shadow-lg"
          style={{
            background:
              "radial-gradient(circle at 85% 50%, rgba(57, 190, 173, 0.22), transparent 45%), linear-gradient(145deg, #0B2D34 0%, #123E45 54%, #0A635F 100%)",
          }}
        >
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
              <div className="absolute top-2 left-6 w-12 h-6 bg-[#69D7C9]/40 rounded-full blur-[1px] transform -rotate-45" />
              <div className="absolute bottom-4 right-10 w-14 h-6 bg-[#34d399]/40 rounded-full blur-[1px] transform rotate-12" />
            </div>
          </div>

          <div className="max-w-xl relative z-10 space-y-4">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#0B2D34]/80 backdrop-blur-sm px-3.5 py-1 text-xs font-medium text-[#69D7C9] border border-[#65D7C9]/30">
              <Sparkles className="w-3.5 h-3.5 text-[#69D7C9]" />
              {primaryReview.is_urgent ? "Momento óptimo para repasar" : "Refuerzo recomendado"}
            </span>

            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
              Refuerza {primaryReview.knowledge_component_name}
            </h2>

            <p className="text-teal-100/90 text-sm leading-relaxed">
              Un repaso breve de 3 a 5 minutos consolidará tus conexiones conceptuales y evitará el decaimiento natural de la retención.
            </p>

            <div className="flex flex-wrap items-center gap-4 text-xs text-teal-200/90 pt-1">
              <div className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                <span>{primaryReview.estimated_minutes} minutos estimados</span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileText className="w-4 h-4" />
                <span>{primaryReview.course_name}</span>
              </div>
            </div>

            <div className="pt-2">
              <Link href={primaryReview.recommendation_id ? `/recommendations/${primaryReview.recommendation_id}` : `/recommendations`}>
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
      ) : (
        <div className="rounded-3xl p-8 bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-100 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <Badge variant="success" className="text-xs px-3 py-1">
              Retención Óptima
            </Badge>
            <h2 className="text-2xl font-bold text-slate-900">
              ¡Estás al día con tus temas!
            </h2>
            <p className="text-slate-600 text-sm max-w-lg">
              No tienes conceptos en riesgo de olvido hoy. Puedes repasar tus cursos o resolver actividades formativas disponibles.
            </p>
          </div>
          <Link href="/courses">
            <Button className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl">
              Explorar cursos
            </Button>
          </Link>
        </div>
      )}

      {/* Tu Panorama (Weekly Stats) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Tu panorama</h2>
          <p className="text-xs text-slate-500">Métricas reales de interacción y aprendizaje</p>
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
                  {analytics?.weekly_learning_minutes ?? 0} min
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Tiempo de microaprendizaje
                </p>
              </div>
              <p className="text-xs font-semibold text-teal-700">
                {analytics?.completed_activities_count ?? 0} actividades completadas
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
                  {analytics?.consolidated_concepts_count ?? 0}
                  <span className="text-lg font-normal text-slate-400">
                    /{analytics?.total_concepts_count ?? 0}
                  </span>
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Conceptos consolidados
                </p>
              </div>
              <p className="text-xs font-medium text-slate-500">
                {analytics?.reviewed_concepts_count ?? 0} repasados oportunamente
              </p>
            </div>
          </Card>

          {/* Stat 3: Observed Accuracy */}
          <Card className="rounded-2xl border-slate-200/70 p-6 shadow-xs">
            <div className="flex flex-col justify-between h-full space-y-4">
              <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-extrabold text-slate-900">
                  {analytics?.observed_accuracy_percentage ?? 0}%
                </p>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Precisión observada
                </p>
              </div>
              <div className="w-full">
                <Progress
                  value={analytics?.observed_accuracy_percentage ?? 0}
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
              <p className="text-xs text-slate-500">Cursos matriculados este ciclo</p>
            </div>
            <Link
              href="/courses"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1"
            >
              Ver todos <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {courses.length === 0 ? (
            <Card className="p-8 text-center rounded-2xl border-dashed border-slate-200">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">Sin cursos asignados aún</p>
              <p className="text-xs text-slate-400 mt-1">Tu docente o tutor te asignará a tu sección correspondiente.</p>
            </Card>
          ) : (
            courses.map((course) => (
              <Link key={course.course_id} href={`/courses`} className="block group">
                <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs hover:border-teal-300 hover:shadow-sm transition-all mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-[#edf8f5] flex items-center justify-center flex-shrink-0 border border-[#d1fae5]/60">
                      <BookOpen className="w-7 h-7 text-teal-700" />
                    </div>

                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-center gap-2">
                        <Badge variant="success" className="text-[10px] px-2 py-0.5">
                          {course.section_name}
                        </Badge>
                        {course.active_activities_count > 0 && (
                          <Badge variant="warning" className="text-[10px] px-2 py-0.5">
                            {course.active_activities_count} actividades activas
                          </Badge>
                        )}
                      </div>
                      <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                        {course.course_name}
                      </h3>
                      <p className="text-xs text-slate-500">
                        {course.units_count} unidades · {course.kcs_count} componentes de conocimiento
                      </p>
                      <div className="pt-1 flex items-center gap-3">
                        <div className="flex-1">
                          <Progress value={course.progress_percentage} className="h-1.5" />
                        </div>
                        <span className="text-xs font-bold text-slate-700">{course.progress_percentage}%</span>
                      </div>
                    </div>

                    <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>

        {/* Próximos Repasos (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Próximos repasos</h2>
              <p className="text-xs text-slate-500">Planificados por espaciamiento temporal</p>
            </div>
            <Link
              href="/recommendations"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1"
            >
              Ver plan <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs divide-y divide-slate-100">
            {upcomingReviews.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                No tienes repasos pendientes por ahora.
              </div>
            ) : (
              upcomingReviews.map((rev, idx) => (
                <div key={rev.recommendation_id || idx} className="py-3 first:pt-1 last:pb-1 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-12 w-12 rounded-xl bg-amber-50 text-amber-900 flex flex-col items-center justify-center flex-shrink-0 border border-amber-200/60">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-amber-700">
                        {rev.is_urgent ? "HOY" : "PRÓX"}
                      </span>
                      <span className="text-xs font-extrabold leading-none">{rev.estimated_minutes}m</span>
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-bold text-slate-900 truncate">{rev.knowledge_component_name}</h4>
                      <p className="text-xs text-slate-500 truncate">{rev.course_name} · Repaso espaciado</p>
                    </div>
                  </div>
                  <Badge
                    variant={rev.is_urgent ? "warning" : "secondary"}
                    className="text-[10px] font-semibold flex-shrink-0"
                  >
                    {rev.priority_label}
                  </Badge>
                </div>
              ))
            )}
          </Card>
        </div>
      </div>

      {/* Actividades Asignadas Recientes */}
      {recentActivities.length > 0 && (
        <div className="space-y-4 pt-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Cuestionarios y actividades</h2>
              <p className="text-xs text-slate-500">Evaluaciones formativas y de retención asignadas por tu docente</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentActivities.map((act) => (
              <Card key={act.activity_id} className="rounded-2xl border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-[10px]">
                      {act.course_name}
                    </Badge>
                    <Badge
                      variant={act.latest_attempt_status === "completed" ? "success" : "lavender"}
                      className="text-[10px]"
                    >
                      {act.latest_attempt_status === "completed" ? `Completado (${act.latest_score}%)` : "Pendiente"}
                    </Badge>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">{act.title}</h3>
                  <p className="text-xs text-slate-500 line-clamp-2">{act.description || "Actividad asignada a tu sección."}</p>
                </div>

                <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    {act.time_limit_minutes ? `${act.time_limit_minutes} min` : "Sin límite de tiempo"}
                  </span>
                  <Link href={`/quiz/${act.activity_id}`}>
                    <Button size="sm" className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-lg text-xs">
                      {act.attempts_count > 0 ? "Repetir intento" : "Iniciar cuestionario"}
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
