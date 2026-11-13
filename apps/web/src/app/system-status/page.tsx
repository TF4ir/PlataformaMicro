"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Server,
  Cpu,
  Shield,
  Activity,
  Clock,
  RefreshCw,
  Lock,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api/client";
import { SystemStatusData } from "@/types/ui";
import {
  NOT_MEASURED_TEXT,
  UNAVAILABLE_TEXT,
  UNVERIFIED_TEXT,
  formatLatency,
  formatVerificationTimestamp,
} from "@/lib/data-provenance";

const INITIAL_STATUS: SystemStatusData = {
  apiStatus: "unavailable",
  coldStartEstimatedSeconds: null,
  activeModel: null,
  inferenceLatencyMs: null,
  supabaseRlsStatus: "unverified",
  pseudonymizationStatus: "unverified",
  lastHeartbeat: null,
};

export default function SystemStatusPage() {
  const [status, setStatus] = useState<SystemStatusData>(INITIAL_STATUS);
  const [isChecking, setIsChecking] = useState(false);

  const loadStatus = useCallback(async () => {
    setIsChecking(true);
    const startedAt = performance.now();

    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 10000);
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        signal: controller.signal,
        cache: "no-store",
      });
      window.clearTimeout(timeout);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const measuredLatency = performance.now() - startedAt;

      setStatus({
        apiStatus: "healthy",
        coldStartEstimatedSeconds: null,
        // The health endpoint does not report the active model.
        activeModel: null,
        inferenceLatencyMs: measuredLatency,
        supabaseRlsStatus: "unverified",
        pseudonymizationStatus: "unverified",
        lastHeartbeat: new Date().toISOString(),
      });
    } catch {
      setStatus({
        apiStatus: "unavailable",
        coldStartEstimatedSeconds: null,
        activeModel: null,
        inferenceLatencyMs: null,
        supabaseRlsStatus: "unverified",
        pseudonymizationStatus: "unverified",
        lastHeartbeat: new Date().toISOString(),
      });
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const isHealthy = status.apiStatus === "healthy";
  const latencyText = formatLatency(status.inferenceLatencyMs, {
    measured: isHealthy,
  });
  const lastCheckText = formatVerificationTimestamp(status.lastHeartbeat);
  const modelText = status.activeModel
    ? status.activeModel
    : "No reportado por el servicio";

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
            TELEMETRÍA & ARQUITECTURA
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Estado del sistema
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Estado medido del servicio de inferencia y verificación explícita de
            los controles de seguridad.
          </p>
        </div>

        <Button
          variant="outline"
          className="rounded-xl text-xs font-semibold gap-2 self-start sm:self-auto"
          onClick={() => void loadStatus()}
          disabled={isChecking}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? "animate-spin" : ""}`} />
          {isChecking ? "Verificando…" : "Verificar ahora"}
        </Button>
      </div>

      {/* Main Status Hero */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`h-3.5 w-3.5 rounded-full ${
                isHealthy ? "bg-emerald-500" : "bg-slate-400"
              }`}
            />
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                {isHealthy
                  ? "Servicio de inferencia respondió"
                  : "Servicio de inferencia no disponible"}
              </h2>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Última verificación: {lastCheckText}
              </p>
            </div>
          </div>
          <Badge
            variant={isHealthy ? "active" : "outline"}
            className="text-xs px-3 py-1"
          >
            {isHealthy ? "API: OK" : "API: sin conexión"}
          </Badge>
        </div>

        <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4 text-[11px] text-slate-600 leading-relaxed">
          La fecha y hora de verificación corresponden al último intento de
          consulta desde este navegador. Si la consulta falla, no se muestra una
          latencia estimada.
        </div>

        {/* 4 Pillars of the Architecture */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 pt-2">
          {/* Pillar 1: blitz.cloud Inactive / Cold-Start Engine */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Server className="w-5 h-5 text-teal-700" />
              <Badge variant={isHealthy ? "active" : "outline"} className="text-[10px]">
                {isHealthy ? "Respondió" : "Sin conexión"}
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
                <span>Latencia medida:</span>
                <strong className="text-slate-900">{latencyText}</strong>
              </p>
              <p className="flex justify-between">
                <span>Cold start:</span>
                <span className="text-slate-500">
                  {status.coldStartEstimatedSeconds !== null
                    ? `${status.coldStartEstimatedSeconds} s`
                    : "No reportado"}
                </span>
              </p>
              <p className="flex justify-between">
                <span>Estado del servicio:</span>
                <span
                  className={
                    isHealthy
                      ? "text-emerald-700 font-semibold"
                      : "text-slate-600 font-semibold"
                  }
                >
                  {isHealthy ? "En línea" : "No disponible"}
                </span>
              </p>
            </div>
          </div>

          {/* Pillar 2: Predictive Model / Adaptive Fallback */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Cpu className="w-5 h-5 text-purple-700" />
              <Badge variant="outline" className="text-[10px]">
                No reportado
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Motor adaptativo</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Inferencia y política de repaso
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between gap-2">
                <span>Modelo activo:</span>
                <span className="text-slate-700 font-semibold text-right">
                  {modelText}
                </span>
              </p>
              <p className="flex justify-between gap-2">
                <span>Política:</span>
                <span className="text-slate-500 text-right">
                  No reportada por el servicio
                </span>
              </p>
            </div>
          </div>

          {/* Pillar 3: Supabase PostgreSQL & RLS */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Lock className="w-5 h-5 text-emerald-700" />
              <Badge variant="outline" className="text-[10px]">
                {UNVERIFIED_TEXT}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Supabase DB</p>
              <p className="text-xs text-slate-500 mt-0.5">
                PostgreSQL 15+ con RLS
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between gap-2">
                <span>RLS:</span>
                <span className="text-slate-600 font-semibold text-right">
                  {UNVERIFIED_TEXT}
                </span>
              </p>
              <p className="flex justify-between gap-2">
                <span>Multi-tenancy:</span>
                <span className="text-slate-600 text-right">
                  {UNVERIFIED_TEXT}
                </span>
              </p>
              <p className="flex justify-between gap-2">
                <span>answer_events:</span>
                <span className="text-slate-600 text-right">
                  Inserción definida en esquema
                </span>
              </p>
            </div>
          </div>

          {/* Pillar 4: Protection of Minors */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <Shield className="w-5 h-5 text-sky-700" />
              <Badge variant="outline" className="text-[10px]">
                {UNVERIFIED_TEXT}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Privacidad de menores</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Protección de datos personales
              </p>
            </div>
            <div className="pt-2 text-[11px] text-slate-600 space-y-1 border-t border-slate-200/60">
              <p className="flex justify-between gap-2">
                <span>Seudonimización:</span>
                <span className="text-slate-600 font-semibold text-right">
                  {UNVERIFIED_TEXT}
                </span>
              </p>
              <p className="flex justify-between gap-2">
                <span>Exposición de PII:</span>
                <span className="text-slate-600 text-right">
                  {UNVERIFIED_TEXT}
                </span>
              </p>
              <p className="flex justify-between gap-2">
                <span>Certificación:</span>
                <span className="text-slate-600 text-right">
                  No emitida
                </span>
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] text-slate-500 border-t border-slate-100 pt-4">
          <span className="inline-flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-teal-700" />
            Latencia: {latencyText}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-teal-700" />
            {lastCheckText}
          </span>
          <span>
            {status.inferenceLatencyMs === null
              ? `Sin medición: ${NOT_MEASURED_TEXT}`
              : `Medición local del navegador`}
          </span>
          <span className="text-slate-400">{UNAVAILABLE_TEXT} para datos no consultados.</span>
        </div>
      </Card>
    </div>
  );
}
