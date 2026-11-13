"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Award,
  CheckCircle,
  Clock,
  AlertCircle,
  Sparkles,
  ChevronRight,
  BookOpen,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  studentLearningApi,
  StudentProgressDetailResponse,
} from "@/lib/api/learning";
import {
  MASTERY_THRESHOLDS,
  UNAVAILABLE_TEXT,
  formatMetricWithMeta,
} from "@/lib/data-provenance";

function kcStatusBadge(status: string): {
  label: string;
  variant: "success" | "warning" | "secondary";
} {
  switch (status) {
    case "consolidated":
    case "Consolidado":
      return { label: "Consolidado", variant: "success" };
    case "in_progress":
    case "En proceso":
      return { label: "En proceso", variant: "secondary" };
    case "requiring_reinforcement":
    case "Refuerzo sugerido":
      return { label: "Refuerzo sugerido", variant: "warning" };
    default:
      return { label: "Sin evidencia suficiente", variant: "secondary" };
  }
}

export default function StudentProgressPage() {
  const [progressData, setProgressData] = useState<StudentProgressDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadProgress() {
      try {
        setLoading(true);
        setError(null);
        const data = await studentLearningApi.getProgress();
        if (isMounted) {
          setProgressData(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Error al cargar la telemetría de progreso";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadProgress();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 pb-12 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
          <div className="h-32 bg-slate-100 rounded-2xl" />
        </div>
        <div className="h-64 bg-slate-100 rounded-3xl" />
      </div>
    );
  }

  const analytics = progressData?.analytics;
  const evolution = progressData?.evolution || [];
  const kcBreakdown = progressData?.kc_breakdown || [];
  const activityHistory = progressData?.activity_history || [];

  const metricMeta = analytics?.metric_meta;
  const completedActivitiesText = analytics
    ? formatMetricWithMeta(
        metricMeta?.completed_activities_count,
        analytics.completed_activities_count
      )
    : UNAVAILABLE_TEXT;
  const accuracyText = analytics
    ? formatMetricWithMeta(
        metricMeta?.observed_accuracy_percentage,
        analytics.observed_accuracy_percentage,
        { unit: "%", decimals: 1 }
      )
    : UNAVAILABLE_TEXT;
  const accuracyIsObserved =
    metricMeta?.observed_accuracy_percentage.status === "observed" &&
    typeof analytics?.observed_accuracy_percentage === "number";
  const consolidatedText = analytics
    ? formatMetricWithMeta(
        metricMeta?.consolidated_concepts_count,
        analytics.consolidated_concepts_count
      )
    : UNAVAILABLE_TEXT;
  const totalConceptsText = analytics
    ? formatMetricWithMeta(
        metricMeta?.total_concepts_count,
        analytics.total_concepts_count
      )
    : UNAVAILABLE_TEXT;
  const conceptsAreObserved =
    metricMeta?.consolidated_concepts_count.status === "observed" &&
    metricMeta?.total_concepts_count.status === "observed";
  const weeklyMinutesText = analytics
    ? formatMetricWithMeta(
        metricMeta?.weekly_learning_minutes,
        analytics.weekly_learning_minutes,
        { unit: "min" }
      )
    : UNAVAILABLE_TEXT;
  // A failed request must not be rendered as an empty-but-successful dataset.
  const dataUnavailable = Boolean(error) && !progressData;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Mi progreso y retención
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Telemetría objetiva: precisión observada de tus respuestas y estado de
            tus componentes de conocimiento.
          </p>
        </div>
        <Link href="/recommendations">
          <Button variant="outline" className="rounded-xl text-xs gap-1.5 border-teal-200 text-teal-800 hover:bg-teal-50">
            <Sparkles className="w-4 h-4 text-teal-600" />
            Ver recomendaciones adaptativas
          </Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 4 Stat Cards (Objective Telemetry - No fabricated streaks) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Completed Activities */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Actividades completadas
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {completedActivitiesText}
          </p>
          <p className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5" />
            Cuestionarios evaluados
          </p>
        </Card>

        {/* Card 2: Observed Accuracy */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Precisión observada
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {accuracyText}
          </p>
          <p className="text-xs font-medium text-slate-400">
            {accuracyIsObserved
              ? `En ${analytics?.total_answers ?? 0} respuestas analizadas`
              : "Aún no hay respuestas observadas"}
          </p>
        </Card>

        {/* Card 3: Consolidated Concepts */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Conceptos consolidados
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {conceptsAreObserved ? (
              <>
                {consolidatedText}
                <span className="text-lg font-normal text-slate-400">
                  /{totalConceptsText}
                </span>
              </>
            ) : (
              <span className="text-lg font-semibold text-slate-600">
                {consolidatedText}
              </span>
            )}
          </p>
          <p className="text-xs font-medium text-teal-700">
            Umbral configurado: ≥ {MASTERY_THRESHOLDS.consolidated}% de precisión
          </p>
        </Card>

        {/* Card 4: Dedicated Learning Time */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Tiempo de microestudio
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {weeklyMinutesText}
          </p>
          <p className="text-xs font-medium text-slate-400 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-teal-600" />
            Lectura activa y repasos
          </p>
        </Card>
      </div>

      {/* Evolution Chart */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Evolución de precisión en cuestionarios
          </h2>
          <p className="text-xs text-slate-500">
            Puntaje observado en tus actividades evaluadas cronológicamente
          </p>
        </div>

        {evolution.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            <TrendingUp className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            {dataUnavailable
              ? "No se pudo consultar la evolución: la solicitud falló. No se asume un historial vacío."
              : "No hay suficientes evaluaciones completadas para graficar la evolución. Resuelve tus cuestionarios pendientes para observar tu progreso."}
          </div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={evolution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="accuracyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0A635F" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0A635F" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, "Precisión"]}
                  labelFormatter={(_label, payload) => payload?.[0]?.payload?.activity_title || _label}
                />
                <Area
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#0A635F"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#accuracyGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      {/* Knowledge Component Breakdown: Differentiating Observed Accuracy vs Estimated Retention */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Estado de componentes de conocimiento (KC)
          </h2>
          <p className="text-xs text-slate-500">
            Respuestas observadas y, solo cuando existe un modelo validado, la
            estimación de retención correspondiente.
          </p>
        </div>

        {kcBreakdown.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            {dataUnavailable
              ? "No se pudo consultar el estado de tus componentes: la solicitud falló."
              : "No se han registrado componentes de conocimiento en este periodo."}
          </div>
        ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px] bg-slate-50/50">
                <th className="py-3 px-4 font-semibold">TEMA / CONCEPTO</th>
                <th className="py-3 px-4 font-semibold">UNIDAD</th>
                <th className="py-3 px-4 font-semibold">RESPUESTAS (N)</th>
                <th className="py-3 px-4 font-semibold">PRECISIÓN OBSERVADA</th>
                <th className="py-3 px-4 font-semibold">RETENCIÓN ESTIMADA</th>
                <th className="py-3 px-4 text-right font-semibold">ESTADO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {kcBreakdown.map((kc) => (
                  <tr key={kc.kc_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {kc.kc_name}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {kc.unit_title}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {kc.total_answers}
                    </td>
                    <td className="py-3.5 px-4">
                      {kc.observed_accuracy !== null ? (
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-800">
                            {kc.observed_accuracy}%
                          </span>
                          <div className="w-16">
                            <Progress value={kc.observed_accuracy} className="h-1.5" />
                          </div>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-500">
                          Sin evidencia suficiente
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {kc.is_cold_start ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                          Fase inicial (requiere más respuestas)
                        </span>
                      ) : (
                        <span className="font-semibold text-teal-800">
                          {kc.estimated_retention !== null ? `${kc.estimated_retention}%` : "—"}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Badge
                        variant={kcStatusBadge(kc.status).variant}
                        className="text-[10px]"
                      >
                        {kcStatusBadge(kc.status).label}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        )}
      </Card>

      {/* Completed Activities History */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Historial de cuestionarios completados
          </h2>
          <p className="text-xs text-slate-500">
            Registro cronológico inmutable de intentos y retroalimentación
          </p>
        </div>

        {activityHistory.length === 0 ? (
          <p className="text-xs text-slate-400 py-4">
            {dataUnavailable
              ? "No se pudo consultar tu historial: la solicitud falló."
              : "Aún no has completado cuestionarios en tus cursos."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px]">
                  <th className="py-3 px-4 font-semibold">CUESTIONARIO</th>
                  <th className="py-3 px-4 font-semibold">CURSO</th>
                  <th className="py-3 px-4 font-semibold">FECHA</th>
                  <th className="py-3 px-4 font-semibold">PUNTAJE</th>
                  <th className="py-3 px-4 text-right font-semibold">ACCIONES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activityHistory.map((item) => (
                  <tr key={item.attempt_id} className="hover:bg-slate-50/60">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {item.activity_title}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">{item.course_name}</td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {new Date(item.completed_at).toLocaleDateString("es-PE")}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-bold text-slate-900">{item.score}%</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link href={`/quiz/${item.activity_id}/results?attempt_id=${item.attempt_id}`}>
                        <Button variant="ghost" size="sm" className="text-xs text-teal-700 hover:text-teal-900">
                          Revisar respuestas
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
