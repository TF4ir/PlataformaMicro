"use client";

import React from "react";
import { CheckCircle2, Clock, AlertCircle, Ban, Layers } from "lucide-react";
import { Card } from "@/components/ui/card";

interface MetricsCardsProps {
  canonicalCount: number;
  pendingDraftsCount: number;
  activeJobsCount: number;
  rejectedCount: number;
}

export function MetricsCards({
  canonicalCount,
  pendingDraftsCount,
  activeJobsCount,
  rejectedCount,
}: MetricsCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {/* 1. Publicadas / Canónicas */}
      <Card className="p-4 sm:p-5 rounded-2xl border-slate-200/80 bg-white shadow-2xs hover:shadow-xs transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Banco institucional
          </span>
          <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <h4 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {canonicalCount}
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Preguntas aprobadas y calibradas
          </p>
        </div>
      </Card>

      {/* 2. Pendientes de revisión */}
      <Card className="p-4 sm:p-5 rounded-2xl border-amber-200/80 bg-amber-50/20 shadow-2xs hover:shadow-xs transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700">
            Por revisar
          </span>
          <div className="w-8 h-8 rounded-xl bg-amber-100/70 text-amber-700 flex items-center justify-center">
            <Clock className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <h4 className="text-2xl sm:text-3xl font-extrabold text-amber-900 tracking-tight">
            {pendingDraftsCount}
          </h4>
          <p className="text-[11px] text-amber-700/80 mt-0.5">
            Borradores en cuarentena humana
          </p>
        </div>
      </Card>

      {/* 3. Trabajos activos */}
      <Card className="p-4 sm:p-5 rounded-2xl border-teal-200/80 bg-teal-50/20 shadow-2xs hover:shadow-xs transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-teal-700">
            En procesamiento
          </span>
          <div className="w-8 h-8 rounded-xl bg-teal-100/70 text-teal-700 flex items-center justify-center">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <h4 className="text-2xl sm:text-3xl font-extrabold text-teal-900 tracking-tight">
            {activeJobsCount}
          </h4>
          <p className="text-[11px] text-teal-700/80 mt-0.5">
            Materiales en pipeline LLM
          </p>
        </div>
      </Card>

      {/* 4. Descartadas */}
      <Card className="p-4 sm:p-5 rounded-2xl border-slate-200/80 bg-white shadow-2xs hover:shadow-xs transition-shadow">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Descartadas
          </span>
          <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <Ban className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3">
          <h4 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {rejectedCount}
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Reactivos con motivo de descarte
          </p>
        </div>
      </Card>
    </div>
  );
}
