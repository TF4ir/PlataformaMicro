"use client";

import React, { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RejectReasonDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
  questionStem: string;
}

const PRESET_REASONS = [
  "Fuera de alcance curricular para 5.° de secundaria",
  "Enunciado o alternativas ambiguas",
  "Error conceptual o alucinación del modelo",
  "Alternativas redundantes o no plausibles",
  "Nivel de dificultad inadecuado",
];

export function RejectReasonDialog({
  isOpen,
  onClose,
  onConfirm,
  questionStem,
}: RejectReasonDialogProps) {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onConfirm(reason.trim());
      onClose();
    } catch (err) {
      console.error("Error al descartar:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5 text-rose-600">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="font-bold text-slate-900 text-base">Descartar borrador de pregunta</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-500 line-clamp-2 italic bg-slate-50 p-2.5 rounded-lg border border-slate-100">
          &quot;{questionStem}&quot;
        </p>

        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-700">
            Motivos frecuentes (haz clic para autocompletar):
          </label>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_REASONS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setReason(p)}
                className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 border border-slate-200 transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">
              Motivo o justificación pedagógica (opcional pero recomendado):
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Explica por qué este reactivo debe ser descartado..."
              className="w-full text-xs p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500 focus:outline-none resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-xl"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isSubmitting}
              className="bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-xl"
            >
              {isSubmitting ? "Descartando..." : "Confirmar descarte"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
