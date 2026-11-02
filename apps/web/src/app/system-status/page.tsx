"use client";

import React from "react";
import {
  Server,
  Cpu,
  Shield,
  Activity,
  CheckCircle,
  Clock,
  RefreshCw,
  Lock,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { mockSystemStatus } from "@/lib/mock-data";

export default function SystemStatusPage() {
  const status = mockSystemStatus;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
            TELEMETRÍA & ARQUITECTURA
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Estados del sistema
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Supervisión operativa de cold-start (blitz.cloud), servicio de inferencia
            FastAPI y aislamiento multi-tenant en Supabase.
          </p>
        </div>

        <Button
          variant="outline"
          className="rounded-xl text-xs font-semibold gap-2 self-start sm:self-auto"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Actualizar telemetría
        </Button>
      </div>

      {/* Main Status Hero */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-3.5 w-3.5 rounded-full bg-emerald-500 animate-ping" />
            <h2 className="text-xl font-bold text-slate-900">
              Todos los subsistemas operativos
            </h2>
          </div>
          <Badge variant="active" className="text-xs px-3 py-1">
            Salud: 100%
          </Badge>
        </div>

        {/* 4 Pillars of the Architecture */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 pt-2">
          {/* Pillar 1: blitz.cloud Inactive / Cold-Start Engine */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Server className="w-5 h-5 text-teal-700" />
              <Badge variant="active" className="text-[10px]">
                Activo
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">blitz.cloud API</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Contenedor Linux/amd64
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between">
                <span>Latencia inferencia:</span>
                <strong className="text-slate-900">{status.inferenceLatencyMs} ms</strong>
              </p>
              <p className="flex justify-between">
                <span>Riesgo de cold start:</span>
                <span className="text-emerald-700 font-semibold">0 s (Caliente)</span>
              </p>
            </div>
          </div>

          {/* Pillar 2: Predictive Model / Adaptive Fallback */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Cpu className="w-5 h-5 text-purple-700" />
              <Badge variant="lavender" className="text-[10px]">
                DAS3H
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Motor Adaptativo</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Ventanas temporales logarítmicas
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between">
                <span>Política activa:</span>
                <strong className="text-slate-900">DAS3H Candidate</strong>
              </p>
              <p className="flex justify-between">
                <span>Modo de fallback:</span>
                <span className="text-slate-500">Reglas disponible</span>
              </p>
            </div>
          </div>

          {/* Pillar 3: Supabase PostgreSQL & RLS */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Lock className="w-5 h-5 text-emerald-700" />
              <Badge variant="active" className="text-[10px]">
                RLS Enforced
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Supabase DB</p>
              <p className="text-xs text-slate-500 mt-0.5">
                PostgreSQL 15+ Append-Only
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between">
                <span>Multi-tenancy:</span>
                <strong className="text-slate-900">auth.uid() estricto</strong>
              </p>
              <p className="flex justify-between">
                <span>answer_events:</span>
                <span className="text-emerald-700 font-semibold">Inmutable</span>
              </p>
            </div>
          </div>

          {/* Pillar 4: Ley 29733 Protection of Minors */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Shield className="w-5 h-5 text-sky-700" />
              <Badge variant="outline" className="text-[10px] bg-sky-50 text-sky-800 border-sky-200">
                Auditado
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Privacidad Menores</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Ley N° 29733 (5.° secundaria)
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between">
                <span>Seudonimización:</span>
                <strong className="text-slate-900">100% activa</strong>
              </p>
              <p className="flex justify-between">
                <span>Exposición de PII:</span>
                <span className="text-emerald-700 font-semibold">Cero</span>
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
