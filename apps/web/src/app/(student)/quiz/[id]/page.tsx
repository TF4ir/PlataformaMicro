"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { X, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { mockQuizQuestions } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export default function QuizActivePage() {
  const router = useRouter();
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const question = mockQuizQuestions[0];

  const handleCheckAnswer = () => {
    if (!selectedOption) return;
    router.push("/quiz/rec-fotosintesis/results");
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between">
      {/* Top Green Accent Progress Bar */}
      <div className="w-full bg-slate-100 h-1">
        <div className="bg-[#0A635F] h-1 w-1/3 transition-all duration-500" />
      </div>

      {/* Top Header */}
      <header className="px-8 py-5 flex items-center justify-between border-b border-slate-100 max-w-5xl mx-auto w-full">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
        >
          <X className="w-4 h-4" />
          Salir
        </Link>

        <div className="text-center">
          <h2 className="text-xs font-bold text-slate-900">
            Recuperación breve
          </h2>
          <p className="text-[11px] text-slate-500 font-medium">
            {question.conceptTitle}
          </p>
        </div>

        <div className="text-xs font-semibold text-slate-500">
          Pregunta {question.questionNumber} de {question.totalQuestions}
        </div>
      </header>

      {/* Main Question Area */}
      <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-12 flex flex-col justify-center">
        <div className="space-y-6">
          {/* Badge & Points */}
          <div className="flex items-center justify-between">
            <Badge
              variant="lavender"
              className="text-[10px] font-bold uppercase tracking-wider px-3 py-1"
            >
              SELECCIÓN ÚNICA
            </Badge>
            <span className="text-xs font-semibold text-slate-400">
              {question.scorePoints} punto
            </span>
          </div>

          {/* Question Text */}
          <div className="space-y-2">
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-snug">
              {question.prompt}
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Selecciona una respuesta.
            </p>
          </div>

          {/* Options Cards List */}
          <div className="space-y-3 pt-3">
            {question.options.map((opt) => {
              const isSelected = selectedOption === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => setSelectedOption(opt.id)}
                  className={cn(
                    "w-full flex items-center justify-between p-4 md:p-5 rounded-2xl border text-left transition-all",
                    isSelected
                      ? "border-[#0A635F] bg-[#f0fdfa] shadow-xs ring-1 ring-[#0A635F]"
                      : "border-slate-200/90 bg-white hover:border-slate-300 hover:bg-slate-50/50"
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
                      {opt.label}
                    </div>
                    <span className="text-xs md:text-sm font-medium text-slate-800 leading-relaxed">
                      {opt.text}
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
        </div>
      </main>

      {/* Bottom Bar */}
      <footer className="border-t border-slate-100 px-8 py-5 bg-white">
        <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
          <p className="text-xs text-slate-400">
            {selectedOption
              ? "Opción seleccionada. Puedes comprobar tu respuesta."
              : "Selecciona una opción para continuar"}
          </p>
          <Button
            size="lg"
            disabled={!selectedOption}
            onClick={handleCheckAnswer}
            className={cn(
              "font-semibold rounded-xl px-6 h-11 transition-all",
              selectedOption
                ? "bg-[#0A635F] hover:bg-[#0B2D34] text-white shadow-sm"
                : "bg-slate-200 text-slate-400 cursor-not-allowed"
            )}
          >
            Comprobar respuesta
          </Button>
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
