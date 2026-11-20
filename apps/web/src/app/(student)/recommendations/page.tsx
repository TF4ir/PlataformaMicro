"use client";

import React, { useEffect, useState, useCallback } from "react";
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
  BrainCircuit,
  Lock,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ApiClientError } from "@/lib/api/client";
import {
  getStudentRecommendations,
  getStudentRetention,
  evaluateRecommendations,
  RecommendationItemResponse,
  StudentRetentionSummaryResponse,
} from "@/lib/api/recommendations";

interface RetentionErrorState {
  message: string;
  isAuthError: boolean;
  status?: number;
}

export default function StudentRecommendationsPage() {
  const [recommendations, setRecommendations] = useState<RecommendationItemResponse[]>([]);
  const [retentionProfile, setRetentionProfile] = useState<StudentRetentionSummaryResponse | null>(null);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [loadingRetention, setLoadingRetention] = useState(true);
  const [retentionError, setRetentionError] = useState<RetentionErrorState | null>(null);
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [includeCompleted, setIncludeCompleted] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const loadRetention = useCallback(async (signal?: AbortSignal) => {
    try {
      setLoadingRetention(true);
      setRetentionError(null);
      const data = await getStudentRetention(0.650, undefined, { signal });
      setRetentionProfile(data);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      const isAuth =
        (err instanceof ApiClientError && err.status === 401) ||
        (err instanceof Error &&
          /401|no está autenticada|sesión expirada|token|unauthorized/i.test(err.message));
      const status = err instanceof ApiClientError ? err.status : undefined;
      const message =
        err instanceof Error
          ? err.message
          : "Error al consultar el diagnóstico de retención.";
      setRetentionError({ message, isAuthError: isAuth, status });
      setRetentionProfile(null);
    } finally {
      setLoadingRetention(false);
    }
  }, []);

  const loadRecommendations = useCallback(
    async (showCompleted = includeCompleted, signal?: AbortSignal) => {
      try {
        setLoadingRecs(true);
        setRecommendationsError(null);
        const recs = await getStudentRecommendations(showCompleted, { signal });
        setRecommendations(recs);
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }
        const msg =
          err instanceof Error
            ? err.message
            : "Error al cargar las recomendaciones pedagógicas.";
        setRecommendationsError(msg);
      } finally {
        setLoadingRecs(false);
      }
    },
    [includeCompleted]
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadRecommendations(includeCompleted, controller.signal);
    void loadRetention(controller.signal);
    return () => {
      controller.abort();
    };
  }, [includeCompleted, loadRecommendations, loadRetention]);

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
      await Promise.all([loadRecommendations(includeCompleted), loadRetention()]);
    } catch (err: unknown) {
      const isAuth =
        (err instanceof ApiClientError && err.status === 401) ||
        (err instanceof Error &&
          /401|no está autenticada|sesión expirada|token|unauthorized/i.test(err.message));
      if (isAuth) {
        setRetentionError({
          message: "Tu sesión ha expirado. Por favor inicia sesión nuevamente.",
          isAuthError: true,
          status: 401,
        });
      }
      const msg = err instanceof Error ? err.message : "Error al evaluar recomendaciones";
      setFeedbackMessage(msg);
    } finally {
      setEvaluating(false);
    }
  };

  const formatLastInteraction = (isoString: string | null) => {
    if (!isoString) return "Sin interacciones registradas";
    try {
      return new Intl.DateTimeFormat("es-PE", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }).format(new Date(isoString));
    } catch {
      return isoString;
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
          <button
            onClick={() => setFeedbackMessage(null)}
            className="text-slate-400 hover:text-slate-600 font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* Recommendations Section */}
      <div className="space-y-4">
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

        {/* Recommendations Error State */}
        {recommendationsError && (
          <Card className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>{recommendationsError}</span>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => loadRecommendations(includeCompleted)}
              className="text-xs h-7"
            >
              Reintentar
            </Button>
          </Card>
        )}

        {/* Recommendations Grid */}
        {loadingRecs ? (
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
      </div>

      {/* Retention Diagnostic Section */}
      <div className="space-y-4 pt-6 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-teal-700" />
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Diagnóstico de retención temporal estimada
              </h2>
              <p className="text-xs text-slate-500">
                Probabilidades P(Recall) proyectadas por el motor adaptativo según tu historial de práctica.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => loadRetention()}
            disabled={loadingRetention}
            className="rounded-xl text-xs gap-1 h-8"
          >
            <RefreshCw className={`w-3 h-3 ${loadingRetention ? "animate-spin" : ""}`} />
            Actualizar
          </Button>
        </div>

        {/* 1. Loading State */}
        {loadingRetention && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
            <div className="h-32 bg-slate-100 rounded-2xl p-4 border border-slate-200/60" />
            <div className="h-32 bg-slate-100 rounded-2xl p-4 border border-slate-200/60" />
            <div className="h-32 bg-slate-100 rounded-2xl p-4 border border-slate-200/60" />
          </div>
        )}

        {/* 2. Error State: 401 Unauthorized / Session Expired */}
        {!loadingRetention && retentionError?.isAuthError && (
          <Card className="p-8 rounded-3xl border border-amber-200 bg-amber-50/50 text-center space-y-3">
            <Lock className="w-10 h-10 text-amber-600 mx-auto" />
            <h3 className="text-base font-bold text-slate-800">
              Sesión requerida para consultar estimaciones de retención
            </h3>
            <p className="text-xs text-slate-600 max-w-md mx-auto">
              Tu sesión de estudiante no está activa o ha expirado. Por seguridad de tus datos académicos,
              el motor predictivo requiere autenticación válida mediante credenciales verificadas.
            </p>
            <div className="pt-2">
              <Link href="/login?redirect=/recommendations">
                <Button className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs">
                  Iniciar sesión nuevamente
                </Button>
              </Link>
            </div>
          </Card>
        )}

        {/* 3. Error State: General Connectivity / Server Failure */}
        {!loadingRetention && retentionError && !retentionError.isAuthError && (
          <Card className="p-8 rounded-3xl border border-rose-200 bg-rose-50/50 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
            <h3 className="text-base font-bold text-slate-800">
              Servicio de diagnóstico no disponible temporalmente
            </h3>
            <p className="text-xs text-slate-600 max-w-md mx-auto">
              {retentionError.message ||
                "No fue posible conectar con el servicio predictivo en AWS Lambda. Por favor verifica tu conexión o reintenta."}
            </p>
            <div className="pt-2">
              <Button
                variant="outline"
                onClick={() => loadRetention()}
                className="rounded-xl text-xs gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Reintentar consulta
              </Button>
            </div>
          </Card>
        )}

        {/* 4. Empty State: Authenticated but No KC Records Yet */}
        {!loadingRetention && !retentionError && retentionProfile && retentionProfile.kcs.length === 0 && (
          <Card className="p-10 rounded-3xl border-dashed border-slate-200 text-center space-y-3">
            <BookOpen className="w-10 h-10 text-teal-600 mx-auto" />
            <h3 className="text-base font-bold text-slate-800">
              Sin curvas de retención calculadas todavía
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Para estimar tus probabilidades de recuerdo y programar repasos oportunos, el motor DAS3H
              necesita registros de práctica formativa. ¡Completa cuestionarios o lecturas para iniciar tu seguimiento!
            </p>
            <div className="pt-2">
              <Link href="/courses">
                <Button variant="outline" className="rounded-xl text-xs">
                  Explorar mis cursos
                </Button>
              </Link>
            </div>
          </Card>
        )}

        {/* 5. Data State: Active Retention Profile with Knowledge Components */}
        {!loadingRetention && !retentionError && retentionProfile && retentionProfile.kcs.length > 0 && (
          <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
              <div>
                <p className="text-xs font-semibold text-slate-500">
                  Estado del modelo predictivo:
                </p>
                <p className="text-xs font-bold text-slate-800 mt-0.5">
                  {retentionProfile.status === "empirical_model_ready"
                    ? "Modelo empírico DAS3H activo"
                    : retentionProfile.status === "cold_start"
                    ? "Fase inicial de observación (Cold Start)"
                    : retentionProfile.status === "insufficient_empirical_data"
                    ? "Reglas pedagógicas adaptativas (Esperando calibración empírica)"
                    : "Diagnóstico pedagógico adaptativo"}
                </p>
              </div>
              <Badge variant="outline" className="text-xs self-start sm:self-auto">
                Modelo: {retentionProfile.kcs[0]?.model_name || "DAS3H"} {retentionProfile.kcs[0]?.model_version ? `v${retentionProfile.kcs[0].model_version}` : ""}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
              {retentionProfile.kcs.map((kc) => {
                const recallPercent = Math.round(kc.current_recall_probability * 100);
                const isConsolidated = kc.current_recall_probability >= 0.8;
                const isGood = kc.current_recall_probability >= 0.65;

                const statusLabel = isConsolidated
                  ? "Retención consolidada"
                  : isGood
                  ? "Concepto afianzado"
                  : "Momento ideal para repasar";

                const badgeVariant = isConsolidated
                  ? "success"
                  : isGood
                  ? "secondary"
                  : "warning";

                const percentColor = isConsolidated
                  ? "text-emerald-700"
                  : isGood
                  ? "text-teal-700"
                  : "text-amber-700";

                return (
                  <div
                    key={kc.knowledge_component_id}
                    className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/70 space-y-3 flex flex-col justify-between hover:border-teal-300 transition-colors"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-bold text-slate-900 text-sm leading-snug line-clamp-2">
                          {kc.knowledge_component_name}
                        </span>
                        <span className={`text-lg font-extrabold ${percentColor}`}>
                          {recallPercent}%
                        </span>
                      </div>

                      <div className="pt-2">
                        <Badge variant={badgeVariant} className="text-[10px] font-semibold">
                          {statusLabel}
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-1 text-[11px] text-slate-500 border-t border-slate-200/60 pt-2">
                      <div className="flex justify-between">
                        <span>Refuerzo sugerido:</span>
                        <span className="font-semibold text-slate-700">
                          {Math.round(kc.current_forgetting_risk * 100)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Prácticas previas:</span>
                        <span className="font-semibold text-slate-700">
                          {kc.total_retrieval_attempts}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Último contacto:</span>
                        <span className="font-semibold text-slate-700">
                          {formatLastInteraction(kc.last_interaction_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
