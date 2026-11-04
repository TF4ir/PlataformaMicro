"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useParams } from "next/navigation";
import {
  Check,
  X,
  Sparkles,
  HelpCircle,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Loader2,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  learningApi,
  AttemptResultsResponse,
} from "@/lib/api/learning";
import { EmpatheticCallout } from "@/components/student/empathetic-callout";

export default function QuizResultsFeedbackPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const activityId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string);
  const attemptId = searchParams?.get("attempt_id");

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AttemptResultsResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchResults() {
      if (!attemptId) {
        setError("No se especificó un identificador de intento válido.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await learningApi.getAttemptResults(attemptId);
        if (isMounted) {
          setResults(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Error al obtener resultados del intento";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchResults();
    return () => {
      isMounted = false;
    };
  }, [attemptId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-[#0A635F] animate-spin" />
        <p className="text-sm font-medium text-slate-600">Calculando resultados de tu intento...</p>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6">
        <Card className="max-w-md w-full p-8 text-center space-y-5 rounded-3xl border-slate-200 shadow-sm bg-white">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-slate-900">Resultados no disponibles</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              {error || "No pudimos cargar los resultados de este intento."}
            </p>
          </div>
          <Link href="/courses">
            <Button className="w-full bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl mt-2">
              Volver a mis cursos
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const scorePercent = Math.round(results.score);
  const isHighMastery = scorePercent >= 80;
  const isMediumMastery = scorePercent >= 60 && scorePercent < 80;

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between py-10 px-6">
      <main className="max-w-3xl mx-auto w-full space-y-8 my-auto">
        {/* Top Header & Mastery Status */}
        <div className="text-center space-y-3">
          <div
            className={cn(
              "mx-auto h-16 w-16 rounded-full flex items-center justify-center shadow-sm",
              isHighMastery
                ? "bg-[#d1fae5] text-[#059669]"
                : isMediumMastery
                ? "bg-teal-50 text-[#0A635F]"
                : "bg-purple-50 text-purple-700"
            )}
          >
            {isHighMastery ? (
              <Check className="h-8 w-8 stroke-[3]" />
            ) : (
              <Sparkles className="h-8 w-8" />
            )}
          </div>

          <div>
            <Badge
              variant={isHighMastery ? "success" : "lavender"}
              className="px-3.5 py-1 text-[11px] font-bold tracking-wider uppercase"
            >
              {isHighMastery
                ? "EXCELENTE PROGRESO"
                : isMediumMastery
                ? "BUEN AVANCE"
                : "REFUERZO SUGERIDO"}
            </Badge>
          </div>

          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {isHighMastery
              ? `¡Excelente trabajo, ${results.student_name.split(" ")[0]}!`
              : isMediumMastery
              ? `¡Buen esfuerzo, ${results.student_name.split(" ")[0]}!`
              : `¡Buen intento, ${results.student_name.split(" ")[0]}!`}
          </h1>
          <p className="text-sm text-slate-600 max-w-lg mx-auto">
            {results.activity_title} · {results.course_name}
          </p>
        </div>

        {/* Summary Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="rounded-2xl border-slate-200/80 p-5 text-center space-y-1 shadow-xs bg-slate-50/50">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              PUNTUACIÓN
            </p>
            <p className="text-3xl font-black text-slate-900">{scorePercent}%</p>
            <p className="text-xs text-slate-500 font-medium">Nota obtenida</p>
          </Card>

          <Card className="rounded-2xl border-slate-200/80 p-5 text-center space-y-1 shadow-xs bg-slate-50/50">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              RESPUESTAS CORRECTAS
            </p>
            <p className="text-3xl font-black text-[#0A635F]">
              {results.correct_answers} de {results.total_questions}
            </p>
            <p className="text-xs text-slate-500 font-medium">Acertadas</p>
          </Card>

          <Card className="rounded-2xl border-slate-200/80 p-5 text-center space-y-1 shadow-xs bg-slate-50/50">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              ESTADO DEL INTENTO
            </p>
            <p className="text-xl font-black text-slate-800 pt-1">
              {results.completed_at ? "Completado" : "En proceso"}
            </p>
            <p className="text-xs text-slate-500 font-medium">Registrado inmutable</p>
          </Card>
        </div>

        {/* Knowledge Component Breakdown */}
        {results.kc_summaries && results.kc_summaries.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  Dominio por componentes de conocimiento
                </h2>
                <p className="text-xs text-slate-500">
                  Conceptos evaluados en esta actividad formativa
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {results.kc_summaries.map((kc) => {
                const masteryRate = Math.round(kc.mastery_rate);
                const isConsolidated = masteryRate >= 80;
                const isConsolidating = masteryRate >= 50 && masteryRate < 80;

                return (
                  <Card
                    key={kc.knowledge_component_id}
                    className="p-4 rounded-2xl border-slate-200/80 shadow-xs space-y-2 bg-white"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 line-clamp-1">
                        {kc.knowledge_component_name}
                      </span>
                      <Badge
                        variant={
                          isConsolidated
                            ? "success"
                            : isConsolidating
                            ? "outline"
                            : "lavender"
                        }
                        className="text-[10px]"
                      >
                        {isConsolidated
                          ? "Consolidado"
                          : isConsolidating
                          ? "En consolidación"
                          : "Refuerzo sugerido"}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                      <span>
                        {kc.correct_answers} de {kc.total_questions} respuestas acertadas
                      </span>
                      <span className="font-bold text-slate-800">{masteryRate}%</span>
                    </div>

                    <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={cn(
                          "h-1.5 rounded-full transition-all",
                          isConsolidated
                            ? "bg-emerald-500"
                            : isConsolidating
                            ? "bg-teal-600"
                            : "bg-purple-500"
                        )}
                        style={{ width: `${masteryRate}%` }}
                      />
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Detailed Question Review */}
        {results.questions && results.questions.length > 0 && (
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Revisión detallada de preguntas
              </h2>
              <p className="text-xs text-slate-500">
                Retroalimentación y explicaciones pedagógicas de tus respuestas
              </p>
            </div>

            <div className="space-y-4">
              {results.questions.map((q, index) => (
                <Card
                  key={q.question_id}
                  className="p-5 md:p-6 rounded-2xl border-slate-200/80 shadow-xs space-y-4 bg-white"
                >
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-[10px] font-semibold text-slate-600">
                      Pregunta {index + 1}
                    </Badge>
                    <Badge
                      variant={q.is_correct ? "success" : "lavender"}
                      className="text-[10px] font-bold"
                    >
                      {q.is_correct ? "CORRECTA" : "POR CONSOLIDAR"}
                    </Badge>
                  </div>

                  <p className="text-sm font-bold text-slate-900 leading-snug">
                    {q.question_text}
                  </p>

                  {/* Answers Comparison */}
                  <div className="space-y-2 pt-1 text-xs">
                    <div
                      className={cn(
                        "p-3 rounded-xl border flex items-center justify-between",
                        q.is_correct
                          ? "bg-emerald-50/60 border-emerald-200 text-emerald-900"
                          : "bg-rose-50/60 border-rose-200 text-rose-900"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {q.is_correct ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        ) : (
                          <X className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        )}
                        <span>
                          <strong>Tu respuesta:</strong> {q.selected_option_text}
                        </span>
                      </div>
                    </div>

                    {!q.is_correct && q.correct_option_text && (
                      <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200 text-emerald-900 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <span>
                          <strong>Respuesta correcta:</strong> {q.correct_option_text}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Explanation */}
                  {q.explanation && (
                    <div className="pt-2 border-t border-slate-100">
                      <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                        EXPLICACIÓN PEDAGÓGICA
                      </p>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {q.explanation}
                      </p>
                    </div>
                  )}

                  {/* KC Tag */}
                  {q.knowledge_component_name && (
                    <div className="text-[11px] text-teal-700 font-medium">
                      Componente: {q.knowledge_component_name}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        <EmpatheticCallout title="Tus respuestas fortalecen tu aprendizaje">
          Cada interacción que realizas queda registrada para que nuestro sistema pueda planificar
          futuros repasos en el momento óptimo antes de que comience el olvido.
        </EmpatheticCallout>

        {/* Navigation Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link href="/courses" className="w-full sm:w-auto">
            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto rounded-xl px-6 font-semibold text-slate-700"
            >
              Volver a mis cursos
            </Button>
          </Link>

          <Link href="/progress" className="w-full sm:w-auto">
            <Button
              size="lg"
              className="w-full sm:w-auto bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl px-6 gap-2 shadow-sm transition-all"
            >
              Ver mi progreso
              <ChevronRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </main>

      {/* Floating help button */}
      <button
        aria-label="Ayuda"
        className="fixed bottom-6 right-6 h-10 w-10 rounded-full bg-slate-900 text-white flex items-center justify-center shadow-lg hover:bg-slate-800 transition-colors z-30"
      >
        <HelpCircle className="w-5 h-5" />
      </button>
    </div>
  );
}
