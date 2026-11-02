"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  Download,
  Calendar,
  Sparkles,
  BarChart3,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  BarChart,
  Bar,
} from "recharts";

const retentionDecayData = [
  { day: "Día 0", fotosintesis: 100, respiracion: 100, genetica: 100 },
  { day: "Día 1", fotosintesis: 89, respiracion: 86, genetica: 92 },
  { day: "Día 3", fotosintesis: 78, respiracion: 71, genetica: 84 },
  { day: "Día 5", fotosintesis: 74, respiracion: 63, genetica: 79 },
  { day: "Día 7", fotosintesis: 71, respiracion: 58, genetica: 75 },
  { day: "Día 14", fotosintesis: 68, respiracion: 52, genetica: 71 },
];

const sectionPerformanceData = [
  { section: "5.° A", microaprendizajes: 184, retencionPromedio: 82 },
  { section: "5.° B", microaprendizajes: 162, retencionPromedio: 76 },
  { section: "5.° C", microaprendizajes: 149, retencionPromedio: 79 },
];

export default function TeacherReportsPage() {
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleExportData = () => {
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
            INVESTIGACIÓN & MODELADO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Reportes y Curvas de Retención
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Dinámica probabilística de consolidación de memoria a largo plazo y evaluación cuasiexperimental.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="lg"
            onClick={handleExportData}
            variant="outline"
            className="rounded-xl text-xs gap-2 border-slate-200 hover:border-teal-400 bg-white shadow-2xs"
          >
            <Download className="w-4 h-4 text-teal-700" />
            {downloadSuccess ? "¡Exportado (CSV)!" : "Exportar dataset seudonimizado"}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <p className="text-xs font-semibold text-slate-500">Tasa de retención diferida (7 días)</p>
          <p className="text-3xl font-extrabold text-slate-900">71.4%</p>
          <p className="text-xs text-emerald-600 font-semibold">↑ +14.8% vs. baseline sin repasos</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <p className="text-xs font-semibold text-slate-500">Eventos de práctica registrados</p>
          <p className="text-3xl font-extrabold text-slate-900">1,248</p>
          <p className="text-xs text-slate-500">Registros append-only inmutables</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-2">
          <p className="text-xs font-semibold text-slate-500">Calibración probabilística (Brier)</p>
          <p className="text-3xl font-extrabold text-slate-900">0.142</p>
          <p className="text-xs text-teal-700 font-semibold">Modelo DAS3H en evaluación</p>
        </Card>
      </div>

      {/* Main Retention Decay Chart */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Curvas empíricas de decaimiento por Componente de Conocimiento (KC)
            </h2>
            <p className="text-xs text-slate-500">
              Estimación $P(R=1)$ a lo largo del tiempo transcurrido desde la última micropráctica
            </p>
          </div>
          <Badge
            variant="outline"
            className="text-[10px] font-bold uppercase tracking-wider text-teal-800 bg-teal-50 border-teal-200 self-start sm:self-auto"
          >
            MODELO TEMPORAL
          </Badge>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={retentionDecayData}
              margin={{ top: 10, right: 20, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="day"
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                tick={{ fill: "#64748b", fontSize: 11 }}
              />
              <YAxis
                domain={[40, 100]}
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                tick={{ fill: "#64748b", fontSize: 11 }}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderRadius: "12px",
                  border: "1px solid #e2e8f0",
                  fontSize: "12px",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <Line
                type="monotone"
                dataKey="fotosintesis"
                name="Fotosíntesis (KC-01)"
                stroke="#0f766e"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#0f766e" }}
              />
              <Line
                type="monotone"
                dataKey="respiracion"
                name="Respiración Celular (KC-02)"
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#f59e0b" }}
              />
              <Line
                type="monotone"
                dataKey="genetica"
                name="Genética Mendeliana (KC-03)"
                stroke="#8b5cf6"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#8b5cf6" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Section Comparison */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Adherencia a repasos adaptativos por sección de 5.° de secundaria
          </h2>
          <p className="text-xs text-slate-500">
            Cantidad de microaprendizajes completados y nivel de retención promedio
          </p>
        </div>

        <div className="h-64 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sectionPerformanceData}
              margin={{ top: 10, right: 20, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="section"
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                tick={{ fill: "#64748b", fontSize: 11 }}
              />
              <YAxis
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                tick={{ fill: "#64748b", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderRadius: "12px",
                  border: "1px solid #e2e8f0",
                  fontSize: "12px",
                }}
              />
              <Bar
                dataKey="microaprendizajes"
                name="Microaprendizajes completados"
                fill="#0f766e"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
