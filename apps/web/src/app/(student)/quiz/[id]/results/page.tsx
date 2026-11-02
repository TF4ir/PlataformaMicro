"use client";

import React from "react";
import Link from "next/link";
import { Check, Sparkles, HelpCircle, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { mockStudent, mockQuizQuestions } from "@/lib/mock-data";

export default function QuizResultsFeedbackPage() {
  const question = mockQuizQuestions[0];
  const correctOption =
    question.options.find((o) => o.id === question.correctOptionId) ||
    question.options[1];

  return (
    <div className="min-h-screen bg-white flex flex-col justify-between py-10 px-6">
      <main className="max-w-2xl mx-auto w-full space-y-8 my-auto">
        {/* Top Success Icon & Badge */}
        <div className="text-center space-y-3">
          <div className="mx-auto h-16 w-16 rounded-full bg-[#d1fae5] text-[#059669] flex items-center justify-center shadow-sm">
            <Check className="h-8 w-8 stroke-[3]" />
          </div>

          <div>
            <Badge
              variant="success"
              className="px-3.5 py-1 text-[11px] font-bold tracking-wider uppercase bg-[#ecfdf5] text-[#059669] border border-[#a7f3d0]"
            >
              RESPUESTA CORRECTA
            </Badge>
          </div>

          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            ¡Muy bien, {mockStudent.name.split(" ")[0]}!
          </h1>
          <p className="text-sm text-slate-600">
            Identificaste la función principal de la luz en la fotosíntesis.
          </p>
        </div>

        {/* Detailed Feedback Card */}
        <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 space-y-6 shadow-xs bg-white">
          {/* User Answer Row */}
          <div className="flex items-center justify-between p-4 rounded-2xl bg-[#f0fdf4] border border-[#bbf7d0]">
            <div className="flex items-center gap-3.5">
              <div className="h-8 w-8 rounded-xl bg-[#dcfce7] text-[#15803d] font-bold text-xs flex items-center justify-center flex-shrink-0">
                {correctOption.label}
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  TU RESPUESTA
                </p>
                <p className="text-xs md:text-sm font-semibold text-slate-900 mt-0.5">
                  {correctOption.text}
                </p>
              </div>
            </div>
            <Check className="w-5 h-5 text-[#15803d] flex-shrink-0 ml-2" />
          </div>

          {/* Explanation Section */}
          <div className="space-y-2">
            <h3 className="text-sm font-bold text-slate-900">
              ¿Por qué es correcta?
            </h3>
            <p className="text-xs leading-relaxed text-slate-600">
              {question.explanation}
            </p>
          </div>

          {/* Reminder Box */}
          <div className="rounded-2xl bg-[#f5f3ff] p-4 border border-[#ede9fe] flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-[#7c3aed] flex-shrink-0 mt-0.5" />
            <p className="text-xs text-[#5b21b6] font-medium leading-relaxed">
              <strong className="font-semibold">Recuerda:</strong> {question.reminderNote.replace("Recuerda: ", "")}
            </p>
          </div>
        </Card>

        {/* Summary Metrics (2 Columns) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Session Result */}
          <Card className="rounded-2xl border-slate-200/80 p-5 text-center space-y-1 shadow-xs">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              RESULTADO DE LA SESIÓN
            </p>
            <p className="text-2xl font-extrabold text-slate-900">3 de 3</p>
            <p className="text-xs text-slate-500 font-medium">
              respuestas correctas
            </p>
          </Card>

          {/* Concept Progress */}
          <Card className="rounded-2xl border-slate-200/80 p-5 text-center space-y-1 shadow-xs">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              PROGRESO DEL CONCEPTO
            </p>
            <p className="text-2xl font-extrabold text-teal-800">
              En consolidación
            </p>
            <p className="text-xs text-slate-500 font-medium">
              Basado en tus respuestas observadas
            </p>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Link href="/courses" className="w-full sm:w-auto">
            <Button
              variant="outline"
              size="lg"
              className="w-full sm:w-auto rounded-xl px-6 font-semibold text-slate-700"
            >
              Volver al curso
            </Button>
          </Link>

          <Link href="/progress" className="w-full sm:w-auto">
            <Button
              size="lg"
              className="w-full sm:w-auto bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl px-6 gap-2 shadow-sm transition-all"
            >
              Ver progreso actualizado
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
