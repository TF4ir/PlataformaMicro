"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sparkles, ChevronRight, BookOpen, Clock, CheckCircle2, ArrowRight, Loader2, Award } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { learningApi, StudentActivityListItem, StudentCourseItem } from "@/lib/api/learning";

export default function CoursesPage() {
  const [filter, setFilter] = useState<"todos" | "en_curso" | "completados">("todos");
  const [activities, setActivities] = useState<StudentActivityListItem[]>([]);
  const [loadingActivities, setLoadingActivities] = useState<boolean>(true);
  const [courses, setCourses] = useState<StudentCourseItem[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoadingActivities(true);
        setLoadingCourses(true);
        const [acts, crs] = await Promise.all([
          learningApi.listStudentActivities().catch((err) => {
            console.warn("Could not fetch student activities from backend, defaulting to empty:", err);
            return [];
          }),
          learningApi.listStudentCourses().catch((err) => {
            console.warn("Could not fetch student courses from backend, defaulting to empty:", err);
            return [];
          }),
        ]);
        if (isMounted) {
          setActivities(acts);
          setCourses(crs);
        }
      } catch (err) {
        console.warn("Could not fetch student data:", err);
      } finally {
        if (isMounted) {
          setLoadingActivities(false);
          setLoadingCourses(false);
        }
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredActivities = activities.filter((act) => {
    if (filter === "todos") return true;
    if (filter === "en_curso") {
      return act.latest_attempt_status === "in_progress" || (act.can_attempt && act.attempts_count === 0);
    }
    if (filter === "completados") {
      return act.latest_attempt_status === "completed" || act.attempts_count > 0;
    }
    return true;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
          APRENDIZAJE
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Mis cursos y actividades
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Explora tus cursos asignados y cuestionarios formativos disponibles.
        </p>
      </div>

      {/* Filter Tabs & Counter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80">
          <button
            onClick={() => setFilter("todos")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "todos"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter("en_curso")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "en_curso"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            En curso / Pendientes
          </button>
          <button
            onClick={() => setFilter("completados")}
            className={cn(
              "px-4 py-1.5 text-xs font-semibold rounded-lg transition-all",
              filter === "completados"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            )}
          >
            Completados
          </button>
        </div>

        <p className="text-xs font-medium text-slate-500">
          {filteredActivities.length} {filteredActivities.length === 1 ? "actividad encontrada" : "actividades encontradas"}
        </p>
      </div>

      {/* Assigned Activities Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Cuestionarios asignados</h2>
            <p className="text-xs text-slate-500">
              Evaluaciones creadas y publicadas por tus docentes para tu sección
            </p>
          </div>
        </div>

        {loadingActivities ? (
          <div className="p-8 rounded-2xl border border-slate-200/80 bg-white flex items-center justify-center gap-3 text-slate-500 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-teal-700" />
            Cargando cuestionarios de tu sección...
          </div>
        ) : filteredActivities.length === 0 ? (
          <Card className="p-8 rounded-3xl border-slate-200/80 text-center space-y-2 bg-slate-50/50">
            <BookOpen className="w-8 h-8 text-slate-400 mx-auto" />
            <h3 className="text-sm font-bold text-slate-800">No hay cuestionarios en este filtro</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Tus docentes publicarán cuestionarios formativos a medida que avancen en el plan de estudios.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredActivities.map((act) => {
              const isCompleted = act.latest_attempt_status === "completed";
              const isInProgress = act.latest_attempt_status === "in_progress";

              return (
                <Card
                  key={act.activity_id}
                  className="rounded-3xl border-slate-200/80 p-6 shadow-xs hover:border-teal-300 hover:shadow-sm transition-all flex flex-col justify-between space-y-5 bg-white"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] text-teal-800 bg-teal-50 border-teal-200">
                          {act.course_name}
                        </Badge>
                        <span className="text-[10px] text-slate-500 font-medium">
                          {act.section_name}
                        </span>
                      </div>

                      {isCompleted ? (
                        <Badge variant="success" className="text-[10px]">
                          Completado
                        </Badge>
                      ) : isInProgress ? (
                        <Badge variant="active" className="text-[10px] bg-amber-50 text-amber-800 border-amber-200">
                          En curso
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] text-slate-600">
                          Disponible
                        </Badge>
                      )}
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-slate-900 leading-snug">
                        {act.title}
                      </h3>
                      {act.description && (
                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                          {act.description}
                        </p>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
                      <div className="flex items-center gap-1">
                        <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                        <span>Intentos: {act.attempts_count}/{act.max_attempts}</span>
                      </div>
                      {act.time_limit_minutes && (
                        <div className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>{act.time_limit_minutes} min</span>
                        </div>
                      )}
                      {act.latest_score !== null && act.latest_score !== undefined && (
                        <div className="flex items-center gap-1 text-emerald-700 font-bold">
                          <Award className="w-3.5 h-3.5" />
                          <span>Nota: {Math.round(act.latest_score)}%</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 font-medium">
                      {act.feedback_policy === "immediate_with_explanation"
                        ? "Retroalimentación paso a paso"
                        : "Retroalimentación al finalizar"}
                    </span>

                    {isCompleted && act.latest_attempt_id ? (
                      <Link href={`/quiz/${act.activity_id}/results?attempt_id=${act.latest_attempt_id}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-xl font-semibold text-xs border-teal-200 text-teal-800 hover:bg-teal-50 gap-1.5"
                        >
                          Ver resultados
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    ) : act.can_attempt || isInProgress ? (
                      <Link href={`/quiz/${act.activity_id}`}>
                        <Button
                          size="sm"
                          className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs gap-1.5 shadow-xs"
                        >
                          {isInProgress ? "Continuar intento" : "Iniciar cuestionario"}
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    ) : (
                      <span className="text-xs text-slate-400 font-medium">
                        Intentos agotados
                      </span>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Enrolled Courses Section */}
      <div className="space-y-4 pt-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Mis cursos matriculados</h2>
          <p className="text-xs text-slate-500">
            Asignaturas y secciones escolares en las que te encuentras formalmente inscrito
          </p>
        </div>

        {loadingCourses ? (
          <div className="p-8 rounded-2xl border border-slate-200/80 bg-white flex items-center justify-center gap-3 text-slate-500 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-teal-700" />
            Cargando tus cursos matriculados...
          </div>
        ) : courses.length === 0 ? (
          <Card className="p-8 rounded-3xl border-slate-200/80 text-center space-y-2 bg-slate-50/50">
            <BookOpen className="w-8 h-8 text-slate-400 mx-auto" />
            <h3 className="text-sm font-bold text-slate-800">No tienes cursos matriculados</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Comunícate con tu docente o administración escolar para verificar tu matrícula en las secciones correspondientes.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {courses.map((course) => (
              <Card
                key={`${course.course_id}-${course.section_id}`}
                className="rounded-3xl border-slate-200/80 p-6 shadow-xs hover:border-teal-300 hover:shadow-sm transition-all flex flex-col justify-between space-y-4 bg-white"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="outline" className="text-[10px] text-teal-800 bg-teal-50 border-teal-200 font-mono">
                      {course.course_code || "CURSO"}
                    </Badge>
                    <Badge variant="active" className="text-[10px] bg-emerald-50 text-emerald-800 border-emerald-200">
                      {course.section_name}
                    </Badge>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-slate-900 leading-snug">
                      {course.course_name}
                    </h3>
                    {course.description && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {course.description}
                      </p>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span className="text-[11px] font-medium text-slate-400">
                    Sección: {course.section_name}
                  </span>
                  <div className="flex items-center gap-1 font-semibold text-teal-800">
                    <span>Inscrito</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Adaptive Pedagogical Assurance */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs space-y-4 bg-white mt-6">
        <div className="flex flex-col sm:flex-row items-start gap-4">
          <div className="h-10 w-10 shrink-0 rounded-xl bg-purple-100 text-[#7c3aed] flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900 leading-snug">
              Tu aprendizaje se adapta contigo
            </h3>
            <p className="text-xs leading-relaxed text-slate-600">
              Las recomendaciones y cuestionarios se ajustan dinámicamente a medida que respondes preguntas y avanzas en tus cursos.
              Los datos combinan tus evidencias observadas con el plan pedagógico diseñado por tus docentes.
            </p>
            <div className="pt-2">
              <Link
                href="/progress"
                className="text-xs font-bold text-teal-700 hover:text-teal-800 inline-flex items-center gap-1 group"
              >
                Ver mi progreso pedagógico
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
