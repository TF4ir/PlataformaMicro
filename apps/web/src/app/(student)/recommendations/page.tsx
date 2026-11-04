"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  BookOpen,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  getStudentRecommendations,
  getStudentRetention,
  evaluateRecommendations,
  RecommendationItemResponse,
  StudentRetentionSummaryResponse,
} from "@/lib/api/recommendations";

export default function StudentRecommendationsPage() {
  const [recommendations, setRecommendations] = useState<RecommendationItemResponse[]>([]);
  const [retentionProfile, setRetentionProfile] = useState<StudentRetentionSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [includeCompleted, setIncludeCompleted] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const loadData = async (showCompleted = includeCompleted) => {
    try {
      setLoading(true);
      const [recs, ret] = await Promise.all([
        getStudentRecommendations(showCompleted),
        getStudentRetention(0.650).catch(() => null),
      ]);
      setRecommendations(recs);
      setRetentionProfile(ret);
    } catch (err: unknown) {
      console.error("Error loading recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(includeCompleted);
  }, [includeCompleted]);

  const handleEvaluate = async () => {
    try {
      setEvaluating(true);
      setFeedbackMessage(null);
      const res = await evaluateRecommendations(0.650);
      setFeedbackMessage(
        res.recommendations_created > 0
          ? `Se identificaron ${res.recommendations_created} nuevos microcontenidos recomendados según tu curva de retención.`
          : "Tu estado de retención está consolidado o en periodo de enfriamiento. No se requieren nuevos repasos en este momento."
      );
      await loadData(includeCompleted);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al evaluar recomendaciones";
      setFeedbackMessage(msg);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="lavender" className="text-xs px-3 py-0.5">
              ADAPTACIÓN PEDAGÓGICA
            </Badge>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-2">
            Recomendaciones de repaso espaciado
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Programadas por el motor temporal predictivo para anticipar el olvido y afianzar tu retención.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={handleEvaluate}
            disabled={evaluating}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? "animate-spin" : ""}`} />
            {evaluating ? "Evaluando..." : "Actualizar diagnóstico"}
          </Button>
        </div>
      </div>

      {feedbackMessage && (
        <div className="rounded-2xl bg-teal-50 border border-teal-200 p-4 text-xs text-teal-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600 flex-shrink-0" />
            <span>{feedbackMessage}</span>
          </div>
          <button onClick={() => setFeedbackMessage(null)} className="text-slate-400 hover:text-slate-600 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-4 text-xs font-semibold">
          <button
            onClick={() => setIncludeCompleted(false)}
            className={`pb-2 transition-colors relative ${
              !includeCompleted ? "text-teal-800 font-bold" : "text-slate-400 hover:text-slate-600"
            }`}
          >
            Pendientes ({recommendations.filter((r) => r.is_pending).length})
            {!includeCompleted && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-700" />}
          </button>
          <button
            onClick={() => setIncludeCompleted(true)}
            className={`pb-2 transition-colors relative ${
              includeCompleted ? "text-teal-800 font-bold" : "text-slate-400 hover:text-slate-600"
            }`}
          >
            Todas (incluye completadas)
            {includeCompleted && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-700" />}
          </button>
        </div>
      </div>

      {/* Recommendations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-pulse">
          <div className="h-44 bg-slate-100 rounded-3xl" />
          <div className="h-44 bg-slate-100 rounded-3xl" />
        </div>
      ) : recommendations.length === 0 ? (
        <Card className="p-12 text-center rounded-3xl border-dashed border-slate-200">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">¡No tienes repasos pendientes!</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            Has repasado todos los temas programados. Continúa con tus clases o consulta el progreso para ver tu nivel de consolidación.
          </p>
          <div className="pt-4">
            <Link href="/progress">
              <Button variant="outline" className="rounded-xl text-xs">
                Ver mi progreso
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {recommendations.map((rec) => {
            const minutes = Math.ceil(rec.microcontent.estimated_duration_seconds / 60);
            return (
              <Card
                key={rec.id}
                className={`rounded-3xl border p-6 shadow-xs flex flex-col justify-between transition-all ${
                  rec.is_pending
                    ? "border-slate-200/90 bg-white hover:border-teal-300 hover:shadow-sm"
                    : "border-slate-100 bg-slate-50/70 opacity-80"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Badge
                      variant={rec.is_pending ? "warning" : "success"}
                      className="text-[10px] uppercase font-bold tracking-wider"
                    >
                      {rec.is_pending ? "Repaso sugerido" : "Completado"}
                    </Badge>
                    <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {minutes} min
                    </span>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-teal-800 uppercase tracking-wider">
                      {rec.knowledge_component_name}
                    </p>
                    <h3 className="text-lg font-bold text-slate-900 mt-1">
                      {rec.microcontent.title}
                    </h3>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">
                    {rec.decision_reason}
                  </p>

                  <div className="text-[11px] text-slate-400">
                    Método:{" "}
                    <span className="font-semibold text-slate-600">
                      {rec.selection_method === "predictive_model"
                        ? "Modelo predictivo DAS3H"
                        : "Regla adaptativa pedagógica"}
                    </span>
                  </div>
                </div>

                <div className="pt-5 mt-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    {rec.scheduled_for
                      ? `Programado: ${new Date(rec.scheduled_for).toLocaleDateString("es-PE")}`
                      : "Disponible ahora"}
                  </span>

                  <Link href={`/learn/${rec.microcontent.id}?recommendation_id=${rec.id}`}>
                    <Button
                      size="sm"
                      className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs gap-1"
                    >
                      {rec.is_pending ? "Iniciar repaso" : "Volver a leer"}
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Retention Diagnostic Summary if available */}
      {retentionProfile && retentionProfile.kcs.length > 0 && (
        <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Diagnóstico de retención temporal estimada
              </h2>
              <p className="text-xs text-slate-500">
                Probabilidades P(Recall) proyectadas a diferentes horizontes temporales
              </p>
            </div>
            <Badge variant="outline" className="text-xs">
              Modelo: {retentionProfile.kcs[0]?.model_name || "DAS3H"}
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {retentionProfile.kcs.map((kc) => (
              <div
                key={kc.knowledge_component_id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200/60 space-y-2"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900 truncate">{kc.knowledge_component_name}</span>
                  <span
                    className={`font-extrabold ${
                      kc.current_recall_probability >= 0.8
                        ? "text-emerald-700"
                        : kc.current_recall_probability >= 0.65
                        ? "text-amber-700"
                        : "text-rose-700"
                    }`}
                  >
                    {Math.round(kc.current_recall_probability * 100)}%
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Riesgo de olvido: {Math.round(kc.current_forgetting_risk * 100)}%
                </div>
                <div className="text-[10px] text-slate-400">
                  Interacciones previas: {kc.total_retrieval_attempts}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
