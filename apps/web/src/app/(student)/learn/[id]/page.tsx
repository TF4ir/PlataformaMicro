"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Sparkles,
  HelpCircle,
  Clock,
  BookOpen,
  AlertCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PhotosynthesisDiagram } from "@/components/student/photosynthesis-diagram";
import { cn } from "@/lib/utils";
import {
  getMicrocontent,
  recordExposure,
  MicrocontentDetailResponse,
  MicrocontentSectionItem,
} from "@/lib/api/microcontents";
import { selectContentRenderer } from "@/lib/data-provenance";

interface LearnPageProps {
  params: {
    id: string;
  };
}

export default function MicrolearningLessonPage({ params }: LearnPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const recommendationId = searchParams.get("recommendation_id");
  const exposureTypeParam = searchParams.get("exposure_type") as "initial_study" | "review_study" | null;

  const [microcontent, setMicrocontent] = useState<MicrocontentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<number>(1);
  const [submittingExposure, setSubmittingExposure] = useState(false);

  const startTimeRef = useRef<Date>(new Date());
  const activeReadingSecondsRef = useRef<number>(0);

  useEffect(() => {
    let isMounted = true;
    async function loadContent() {
      try {
        setLoading(true);
        setError(null);
        const data = await getMicrocontent(params.id);
        if (isMounted) {
          setMicrocontent(data);
          startTimeRef.current = new Date();
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Error al cargar la microlección";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadContent();
    return () => {
      isMounted = false;
    };
  }, [params.id]);

  // Track active reading time ticker
  useEffect(() => {
    const timer = setInterval(() => {
      activeReadingSecondsRef.current += 1;
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Parse sections from content_body or fallback
  const rawSections: MicrocontentSectionItem[] =
    (microcontent?.content_body?.sections as MicrocontentSectionItem[]) || [];

  const sections: MicrocontentSectionItem[] = rawSections.length > 0 ? rawSections : [
    {
      id: 1,
      navTitle: "Conceptos clave",
      heading: microcontent?.title || "Fundamentos",
      tag: "MICROLECCIÓN",
      lead: (microcontent?.content_body?.summary as string) || "Revisa las ideas esenciales de este componente de conocimiento.",
      durationMinutes:
        microcontent && microcontent.estimated_duration_seconds > 0
          ? Math.max(1, Math.ceil(microcontent.estimated_duration_seconds / 60))
          : 0,
    },
  ];

  const currentSection = sections.find((s) => s.id === activeStep) || sections[0];
  const isLastStep = activeStep === sections.length;

  const handleFinishLesson = async () => {
    if (!microcontent || submittingExposure) return;
    setSubmittingExposure(true);
    try {
      const now = new Date();
      const elapsedSeconds = Math.max(
        1,
        Math.round((now.getTime() - startTimeRef.current.getTime()) / 1000)
      );

      // Generate client-side UUIDs for session and idempotency
      const sessionId = crypto.randomUUID();
      const idempotencyKey = crypto.randomUUID();

      await recordExposure(microcontent.id, {
        started_at: startTimeRef.current.toISOString(),
        completed_at: now.toISOString(),
        duration_seconds: elapsedSeconds,
        active_reading_seconds: activeReadingSecondsRef.current,
        completion_status: "completed",
        exposure_type: exposureTypeParam || (recommendationId ? "review_study" : "initial_study"),
        session_id: sessionId,
        idempotency_key: idempotencyKey,
        recommendation_id: recommendationId || undefined,
      });

      // Navigate to recommendation center or dashboard
      if (recommendationId) {
        router.push("/recommendations?completed=true");
      } else {
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      console.error("Error recording exposure:", err);
      // Still allow navigation
      router.push("/dashboard");
    } finally {
      setSubmittingExposure(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-600">Cargando microlección adaptativa...</p>
        </div>
      </div>
    );
  }

  if (error || !microcontent) {
    return (
      <div className="max-w-md mx-auto my-16 p-8 bg-white border border-slate-200 rounded-3xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-amber-600 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">No se pudo cargar el contenido</h2>
        <p className="text-xs text-slate-500">{error || "Microlección no disponible."}</p>
        <Link href="/dashboard">
          <Button className="bg-[#0A635F] text-white rounded-xl">Regresar al panel</Button>
        </Link>
      </div>
    );
  }

  // Specialised diagrams are selected from explicit metadata, never from the title.
  const contentRenderer = selectContentRenderer({
    content_type: microcontent.content_type,
    content_body: microcontent.content_body,
  });

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-white">
      {/* Left Stepper Sidebar (Desktop) */}
      <aside className="hidden md:flex w-64 border-r border-slate-200 p-6 flex-col justify-between flex-shrink-0 bg-slate-50/50">
        <div className="space-y-6">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Salir
          </Link>

          <div>
            <Badge variant="lavender" className="text-[10px] uppercase font-bold tracking-wider">
              {recommendationId ? "REPASO ADAPTATIVO" : "MICROLECCIÓN"}
            </Badge>
            <h2 className="text-xl font-bold text-slate-900 mt-2">{microcontent.title}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{microcontent.knowledge_component_name}</p>
          </div>

          {/* Stepper items */}
          <nav className="space-y-2 pt-2">
            {sections.map((step) => {
              const isPast = step.id < activeStep;
              const isCurrent = step.id === activeStep;

              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-xs font-semibold transition-all text-left",
                    isCurrent
                      ? "bg-white text-slate-900 shadow-sm border border-slate-200/80"
                      : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                  )}
                >
                  <div
                    className={cn(
                      "h-6 w-6 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0",
                      isPast
                        ? "bg-emerald-100 text-emerald-700"
                        : isCurrent
                        ? "bg-[#0A635F] text-white"
                        : "bg-slate-200 text-slate-600"
                    )}
                  >
                    {isPast ? <Check className="w-3.5 h-3.5" /> : step.id}
                  </div>
                  <span className={cn(isCurrent && "font-bold")}>{step.navTitle}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="text-[11px] text-slate-400">
          Paso {activeStep} de {sections.length}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Focused Header */}
        <header className="h-16 border-b border-slate-200/80 px-4 sm:px-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 min-w-0">
            <Link
              href="/dashboard"
              className="md:hidden inline-flex items-center p-2 -ml-2 text-slate-500 hover:text-slate-900 rounded-lg flex-shrink-0"
              title="Salir"
            >
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div className="text-xs font-semibold text-slate-600 truncate">
              {activeStep} de {sections.length} · {currentSection.navTitle}
            </div>
          </div>

          <div className="flex-1 max-w-xs sm:max-w-xl mx-2">
            <Progress
              value={(activeStep / sections.length) * 100}
              className="h-2"
              indicatorClassName="bg-[#0A635F]"
            />
          </div>

          <div className="text-xs font-medium text-slate-500 flex-shrink-0 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            {currentSection.durationMinutes > 0
              ? `${currentSection.durationMinutes} min`
              : "Duración no reportada"}
          </div>
        </header>

        {/* Scrollable Lesson Body */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 md:px-16 py-6 sm:py-10 max-w-4xl mx-auto w-full space-y-6 sm:space-y-8">
          {/* Main Title & Lead */}
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
              {currentSection.tag || "Concepto clave"}
            </p>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
              {currentSection.heading || microcontent.title}
            </h1>
            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              {currentSection.lead}
            </p>
          </div>

          {/* Specialised diagram selected by content_type / diagram_key */}
          {contentRenderer === "photosynthesis" && <PhotosynthesisDiagram />}

          {/* Formula Callout */}
          {currentSection.formula && (
            <div className="rounded-2xl bg-slate-50 border border-slate-200/80 p-4 sm:p-5 text-center overflow-x-auto">
              <code className="text-xs sm:text-sm md:text-base font-bold text-slate-800 tracking-wide font-mono whitespace-nowrap">
                {currentSection.formula}
              </code>
            </div>
          )}

          {/* Body markdown / paragraphs */}
          {currentSection.body && (
            <div className="prose prose-teal text-slate-700 text-sm leading-relaxed">
              <p>{currentSection.body}</p>
            </div>
          )}

          {/* Analogy Callout Box */}
          {currentSection.analogy && (
            <div className="rounded-2xl bg-[#f0fdfa] border-l-4 border-l-[#0f766e] border border-[#ccfbf1] p-4 sm:p-5 flex items-start gap-3 sm:gap-4">
              <div className="h-9 w-9 rounded-xl bg-teal-100 text-[#0f766e] flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-[#115e59]">
                  {currentSection.analogy.title}
                </h4>
                <p className="text-xs leading-relaxed text-[#134e4a]/90">
                  {currentSection.analogy.text}
                </p>
              </div>
            </div>
          )}

          {/* Key Takeaways */}
          {currentSection.keyTakeaways && currentSection.keyTakeaways.length > 0 && (
            <div className="space-y-4 pt-4">
              <h3 className="text-lg font-bold text-slate-900">
                Qué debes recordar
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {currentSection.keyTakeaways.map((item, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2"
                  >
                    <span className="text-xs font-bold text-teal-700">
                      {item.label || `#${idx + 1}`}
                    </span>
                    <p className="text-xs font-medium text-slate-700 leading-relaxed">
                      {item.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Navigation & Completion Controls */}
          <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {activeStep > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveStep((prev) => prev - 1)}
                  className="rounded-xl text-xs gap-1"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Anterior
                </Button>
              )}
              <span className="text-xs text-slate-500">
                {isLastStep ? "Has completado la lectura" : `Paso ${activeStep} de ${sections.length}`}
              </span>
            </div>

            <div>
              {!isLastStep ? (
                <Button
                  size="lg"
                  onClick={() => setActiveStep((prev) => prev + 1)}
                  className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm min-h-[44px]"
                >
                  Siguiente paso
                  <ChevronRight className="w-4 h-4" />
                </Button>
              ) : (
                <Button
                  size="lg"
                  disabled={submittingExposure}
                  onClick={handleFinishLesson}
                  className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm min-h-[44px]"
                >
                  {submittingExposure ? "Registrando avance..." : "Finalizar microlección"}
                  <Check className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </main>
      </div>

      <button
        aria-label="Ayuda pedagógica"
        className="fixed bottom-6 right-6 h-10 w-10 rounded-full bg-slate-900 text-white flex items-center justify-center shadow-lg hover:bg-slate-800 transition-colors z-30"
      >
        <HelpCircle className="w-5 h-5" />
      </button>
    </div>
  );
}
