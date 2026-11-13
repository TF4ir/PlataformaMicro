"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { X, HelpCircle, CheckCircle2, AlertCircle, ArrowRight, Loader2, Sparkles, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  learningApi,
  StudentActivityDetail,
  StudentQuestionItem,
  StartAttemptResponse,
  SubmitAnswerResponse,
} from "@/lib/api/learning";
import { EmpatheticCallout } from "@/components/student/empathetic-callout";

export default function QuizActivePage() {
  const router = useRouter();
  const params = useParams();
  const activityId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string);

  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Activity & Attempt State
  const [activity, setActivity] = useState<StudentActivityDetail | null>(null);
  const [attempt, setAttempt] = useState<StartAttemptResponse | null>(null);
  const [hasStarted, setHasStarted] = useState<boolean>(false);

  // Quiz Interaction State
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [currentFeedback, setCurrentFeedback] = useState<SubmitAnswerResponse | null>(null);

  // Timing
  const questionStartTimeRef = useRef<number>(Date.now());

  // Load activity details on mount
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      if (!activityId) return;
      try {
        setLoading(true);
        setError(null);

        // Fetch activity details
        const act = await learningApi.getStudentActivity(activityId);
        if (!isMounted) return;
        setActivity(act);

        // If there is already an active attempt, fetch or initialize it
        if (act.active_attempt_id) {
          // Attempt already started
          setAttempt({
            attempt_id: act.active_attempt_id,
            activity_id: act.activity_id,
            attempt_number: 1,
            status: "in_progress",
            started_at: new Date().toISOString(),
            questions: act.questions,
          });
          setHasStarted(true);
          questionStartTimeRef.current = Date.now();
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const msg = err instanceof Error ? err.message : "No se pudo cargar la actividad";
        setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [activityId]);

  // Handle starting a fresh attempt
  const handleStartAttempt = async () => {
    if (!activity) return;
    try {
      setIsSubmitting(true);
      setError(null);
      const idempotencyKey = crypto.randomUUID();
      const newAttempt = await learningApi.startAttempt(activity.activity_id, idempotencyKey);
      setAttempt(newAttempt);
      setHasStarted(true);
      setCurrentIndex(0);
      setSelectedOptionId(null);
      setCurrentFeedback(null);
      questionStartTimeRef.current = Date.now();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al iniciar el cuestionario";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Questions from attempt or activity
  const questions: StudentQuestionItem[] = attempt?.questions || activity?.questions || [];
  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;
  const isLastQuestion = currentIndex >= totalQuestions - 1;

  // Handle Option selection
  const handleSelectOption = (optionId: string) => {
    if (currentFeedback) return; // Prevent changing if feedback is showing
    setSelectedOptionId(optionId);
  };

  // Submit Answer for current question
  const handleSubmitAnswer = async () => {
    if (!attempt || !currentQuestion || !selectedOptionId || isSubmitting) return;

    const responseTimeSec = Math.max(1, Math.round((Date.now() - questionStartTimeRef.current) / 1000));
    const idempotencyKey = crypto.randomUUID();

    try {
      setIsSubmitting(true);
      setError(null);

      const resp = await learningApi.submitAnswer(
        attempt.attempt_id,
        {
          question_id: currentQuestion.id,
          selected_option_id: selectedOptionId,
          response_time_seconds: responseTimeSec,
          idempotency_key: idempotencyKey,
        },
        idempotencyKey
      );

      // Check feedback policy
      if (activity?.feedback_policy === "immediate_with_explanation" && resp.feedback) {
        // Show immediate feedback to student
        setCurrentFeedback(resp);
      } else {
        // Move directly to next question or finalize
        if (isLastQuestion) {
          await finalizeAttempt();
        } else {
          moveToNextQuestion();
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al enviar la respuesta";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Transition to next question
  const moveToNextQuestion = () => {
    setCurrentFeedback(null);
    setSelectedOptionId(null);
    setCurrentIndex((prev) => prev + 1);
    questionStartTimeRef.current = Date.now();
  };

  // Finalize attempt
  const finalizeAttempt = async () => {
    if (!attempt) return;
    try {
      setIsSubmitting(true);
      await learningApi.submitAttempt(attempt.attempt_id);
      router.push(`/quiz/${activityId}/results?attempt_id=${attempt.attempt_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al finalizar el intento";
      setError(msg);
      setIsSubmitting(false);
    }
  };

  // 1. Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-[#0A635F] animate-spin" />
        <p className="text-sm font-medium text-slate-600">Cargando actividad de aprendizaje...</p>
      </div>
    );
  }

  // 2. Error State (Not Found / Unassigned / Limit Exceeded)
  if (error && !hasStarted) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6">
        <Card className="max-w-md w-full p-8 text-center space-y-5 rounded-3xl border-slate-200 shadow-sm bg-white">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-slate-900">Actividad no disponible</h2>
            <p className="text-xs text-slate-600 leading-relaxed">{error}</p>
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

  // 3. Pre-Quiz Instructions Landing View
  if (!hasStarted && activity) {
    return (
      <div className="min-h-screen bg-slate-50/50 flex flex-col justify-between py-12 px-6">
        <header className="max-w-2xl mx-auto w-full flex items-center justify-between pb-6">
          <Link
            href="/courses"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <X className="w-4 h-4" />
            Volver a cursos
          </Link>
          <Badge variant="outline" className="text-xs text-teal-800 border-teal-200 bg-teal-50">
            {activity.course_name}
          </Badge>
        </header>

        <main className="max-w-2xl mx-auto w-full my-auto">
          <Card className="p-8 md:p-10 rounded-3xl border-slate-200/80 shadow-xs space-y-6 bg-white">
            <div className="space-y-2">
              <Badge variant="lavender" className="text-[10px] font-bold uppercase tracking-wider px-3 py-1">
                ACTIVIDAD FORMATIVA
              </Badge>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
                {activity.title}
              </h1>
              {activity.description && (
                <p className="text-sm text-slate-600 leading-relaxed pt-1">
                  {activity.description}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-center space-y-1">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Preguntas</p>
                <p className="text-xl font-extrabold text-slate-900">{totalQuestions}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-center space-y-1">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Intentos permitidos</p>
                <p className="text-xl font-extrabold text-slate-900">{activity.max_attempts}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 text-center space-y-1 col-span-2 sm:col-span-1">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Retroalimentación</p>
                <p className="text-xs font-bold text-teal-800 pt-1">
                  {activity.feedback_policy === "immediate_with_explanation"
                    ? "Inmediata paso a paso"
                    : "Al finalizar intento"}
                </p>
              </div>
            </div>

            <EmpatheticCallout title="Aprende a tu propio ritmo">
              Esta sesión te ayuda a identificar fortalezas y reforzar conceptos clave. Tus respuestas nos permiten adaptar
              tus futuros repasos de manera óptima.
            </EmpatheticCallout>

            {error && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-800 font-medium">
                {error}
              </div>
            )}

            <div className="pt-2">
              <Button
                onClick={handleStartAttempt}
                disabled={isSubmitting || !activity.questions || activity.questions.length === 0}
                size="lg"
                className="w-full h-12 bg-[#0A635F] hover:bg-[#0B2D34] text-white font-bold rounded-xl shadow-sm text-sm flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Iniciando intento...
                  </>
                ) : (
                  <>
                    Comenzar cuestionario
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </Card>
        </main>

        <footer className="max-w-2xl mx-auto w-full text-center text-xs text-slate-400 pt-6">
          Plataforma de Microaprendizaje Adaptativo · 5to Secundaria
        </footer>
      </div>
    );
  }

  // 4. Active Quiz Interface
  const progressPercent = totalQuestions > 0 ? Math.round(((currentIndex + 1) / totalQuestions) * 100) : 0;

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between">
      {/* Top Green Accent Progress Bar */}
      <div className="w-full bg-slate-100 h-1.5">
        <div
          className="bg-[#0A635F] h-1.5 transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Top Header */}
      <header className="px-8 py-5 flex items-center justify-between border-b border-slate-100 max-w-5xl mx-auto w-full">
        <Link
          href="/courses"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <X className="w-4 h-4" />
          Salir
        </Link>

        <div className="text-center">
          <h2 className="text-xs font-bold text-slate-900">
            {activity?.title || "Cuestionario de aprendizaje"}
          </h2>
          <p className="text-[11px] text-slate-500 font-medium">
            {activity?.course_name || "Curso no especificado"}
          </p>
        </div>

        <div className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
          Pregunta {currentIndex + 1} de {totalQuestions}
        </div>
      </header>

      {/* Main Question Area */}
      <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-10 flex flex-col justify-center">
        {currentQuestion ? (
          <div className="space-y-6">
            {/* Badge & Points */}
            <div className="flex items-center justify-between">
              <Badge
                variant="lavender"
                className="text-[10px] font-bold uppercase tracking-wider px-3 py-1"
              >
                {currentQuestion.question_type === "multiple_choice"
                  ? "SELECCIÓN MÚLTIPLE"
                  : "SELECCIÓN ÚNICA"}
              </Badge>
              <span className="text-xs font-semibold text-slate-400">
                1 punto
              </span>
            </div>

            {/* Question Text */}
            <div className="space-y-2">
              <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight leading-snug">
                {currentQuestion.question_text}
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                Selecciona la alternativa que consideres correcta:
              </p>
            </div>

            {/* Options Cards List */}
            <div className="space-y-3 pt-2">
              {currentQuestion.options.map((opt, optIdx) => {
                const isSelected = selectedOptionId === opt.id;
                const letter = String.fromCharCode(65 + optIdx); // A, B, C, D...

                return (
                  <button
                    key={opt.id}
                    disabled={!!currentFeedback || isSubmitting}
                    onClick={() => handleSelectOption(opt.id)}
                    className={cn(
                      "w-full flex items-center justify-between p-4 md:p-5 rounded-2xl border text-left transition-all",
                      isSelected
                        ? "border-[#0A635F] bg-[#f0fdfa] shadow-xs ring-1 ring-[#0A635F]"
                        : "border-slate-200/90 bg-white hover:border-slate-300 hover:bg-slate-50/50",
                      currentFeedback && !isSelected && "opacity-60"
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          "h-8 w-8 rounded-xl font-bold text-xs flex items-center justify-center flex-shrink-0 transition-colors",
                          isSelected
                            ? "bg-[#0A635F] text-white"
                            : "bg-slate-100 text-slate-700"
                        )}
                      >
                        {letter}
                      </div>
                      <span className="text-xs md:text-sm font-medium text-slate-800 leading-relaxed">
                        {opt.option_text}
                      </span>
                    </div>

                    {/* Radio Indicator */}
                    <div
                      className={cn(
                        "h-5 w-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors",
                        isSelected
                          ? "border-[#0A635F] bg-[#0A635F]"
                          : "border-slate-300"
                      )}
                    >
                      {isSelected && (
                        <div className="h-2 w-2 rounded-full bg-white" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Step-by-Step Immediate Feedback Card (When Policy Allows) */}
            {currentFeedback && (
              <div
                className={cn(
                  "p-5 rounded-2xl border transition-all space-y-3 animate-in fade-in slide-in-from-top-2",
                  currentFeedback.is_correct
                    ? "bg-[#f0fdf4] border-[#bbf7d0] text-emerald-900"
                    : "bg-[#f5f3ff] border-[#ddd6fe] text-purple-900"
                )}
              >
                <div className="flex items-center gap-2 font-bold text-sm">
                  {currentFeedback.is_correct ? (
                    <>
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      <span>¡Excelente respuesta!</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 text-purple-600" />
                      <span>Concepto por consolidar</span>
                    </>
                  )}
                </div>

                {currentFeedback.feedback?.explanation && (
                  <p className="text-xs leading-relaxed opacity-90">
                    {currentFeedback.feedback.explanation}
                  </p>
                )}
              </div>
            )}

            {/* Error banner if network fails */}
            {error && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 font-medium">
                {error}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500">
            No hay más preguntas en esta actividad.
          </div>
        )}
      </main>

      {/* Bottom Action Footer */}
      <footer className="border-t border-slate-100 px-8 py-5 bg-white">
        <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
          <p className="text-xs text-slate-400">
            {currentFeedback
              ? "Revisa la retroalimentación y continúa cuando estés listo."
              : selectedOptionId
              ? "Opción seleccionada. Puedes confirmar tu respuesta."
              : "Selecciona una opción para continuar"}
          </p>

          {currentFeedback ? (
            <Button
              size="lg"
              disabled={isSubmitting}
              onClick={isLastQuestion ? finalizeAttempt : moveToNextQuestion}
              className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl px-6 h-11 gap-2 shadow-sm transition-all"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Finalizando...
                </>
              ) : isLastQuestion ? (
                <>
                  Finalizar y ver resultados
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  Siguiente pregunta
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          ) : (
            <Button
              size="lg"
              disabled={!selectedOptionId || isSubmitting}
              onClick={handleSubmitAnswer}
              className={cn(
                "font-semibold rounded-xl px-6 h-11 transition-all gap-2",
                selectedOptionId && !isSubmitting
                  ? "bg-[#0A635F] hover:bg-[#0B2D34] text-white shadow-sm"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Registrando respuesta...
                </>
              ) : isLastQuestion && activity?.feedback_policy !== "immediate_with_explanation" ? (
                <>
                  Enviar y finalizar intento
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                "Confirmar respuesta"
              )}
            </Button>
          )}
        </div>
      </footer>

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
