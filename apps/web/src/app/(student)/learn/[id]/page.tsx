"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Check, Sparkles, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PhotosynthesisDiagram } from "@/components/student/photosynthesis-diagram";
import { mockMicrocontentSections } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export default function MicrolearningLessonPage() {
  const [activeStep, setActiveStep] = useState<number>(2); // Step 2 "El proceso" by default as in screenshot
  const sections = mockMicrocontentSections;
  const currentSection = sections.find((s) => s.id === activeStep) || sections[1];

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
              MICROLECCIÓN
            </Badge>
            <h2 className="text-xl font-bold text-slate-900 mt-2">Fotosíntesis</h2>
            <p className="text-xs text-slate-500 mt-0.5">Nutrición y metabolismo</p>
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

          <div className="text-xs font-medium text-slate-500 flex-shrink-0">
            {currentSection.durationMinutes} min
          </div>
        </header>

        {/* Scrollable Lesson Body */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-8 md:px-16 py-6 sm:py-10 max-w-4xl mx-auto w-full space-y-6 sm:space-y-8">
          {/* Main Title & Lead */}
          <div className="space-y-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
              {currentSection.tag}
            </p>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
              {currentSection.heading}
            </h1>
            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              {currentSection.lead}
            </p>
          </div>

          {/* Interactive Biochemical Process Diagram */}
          <PhotosynthesisDiagram />

          {/* Chemical Equation Box */}
          {currentSection.formula && (
            <div className="rounded-2xl bg-slate-50 border border-slate-200/80 p-4 sm:p-5 text-center overflow-x-auto">
              <code className="text-xs sm:text-sm md:text-base font-bold text-slate-800 tracking-wide font-mono whitespace-nowrap">
                {currentSection.formula}
              </code>
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
                  {currentSection.analogy.body}
                </p>
              </div>
            </div>
          )}

          {/* "Qué debes recordar" Recap Cards */}
          {currentSection.keyTakeaways && (
            <div className="space-y-4 pt-4">
              <h3 className="text-lg font-bold text-slate-900">
                Qué debes recordar
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {currentSection.keyTakeaways.map((item) => (
                  <div
                    key={item.number}
                    className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-2"
                  >
                    <span className="text-xs font-bold text-teal-700">
                      {item.number}
                    </span>
                    <p className="text-xs font-medium text-slate-700 leading-relaxed">
                      {item.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottom CTA to Transition to Quiz */}
          <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <p className="text-xs text-slate-500">
              Ya revisaste las ideas esenciales
            </p>
            <Link href="/quiz/rec-fotosintesis">
              <Button
                size="lg"
                className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm min-h-[44px] transition-all"
              >
                Comenzar cuestionario
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </main>
      </div>

      {/* Floating help button */}
      <button
        aria-label="Ayuda pedagógica"
        className="fixed bottom-6 right-6 h-10 w-10 rounded-full bg-slate-900 text-white flex items-center justify-center shadow-lg hover:bg-slate-800 transition-colors z-30"
      >
        <HelpCircle className="w-5 h-5" />
      </button>
    </div>
  );
}
