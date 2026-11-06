"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Download,
  Calendar,
  Sparkles,
  BarChart3,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Brain,
  ChevronDown,
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
  BarChart,
  Bar,
} from "recharts";
import {
  getTeacherReports,
  TeacherReportsResponse,
} from "@/lib/api/teacher";

export default function TeacherReportsPage() {
  const [reports, setReports] = useState<TeacherReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadReports() {
      try {
        setLoading(true);
        setError(null);
        const data = await getTeacherReports();
        if (isMounted) {
          setReports(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Error al cargar reportes";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadReports();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleExportCSV = () => {
    if (!reports) return;
    try {
      // Build clean pseudonymized CSV
      const rows = [
        ["student_code_pseudo", "section", "kc_name", "observed_accuracy", "status"].join(","),
      ];
      for (const st of reports.mastery_heatmap.rows) {
        for (const [kcId, data] of Object.entries(st.kcs)) {
          const kcObj = reports.mastery_heatmap.kcs.find((k) => k.id === kcId);
          const kcName = kcObj ? kcObj.name : kcId;
          rows.push(
            [
              `"${st.student_code || st.student_name}"`,
              `"${st.section_name}"`,
              `"${kcName}"`,
              data.accuracy,
              `"${data.status}"`,
            ].join(",")
          );
        }
      }
      const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `telemetria_retencion_seudonimizada_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3500);
    } catch (err) {
      console.error("Export error:", err);
    }
  };

  if (loading && !reports) {
    return (
      <div className="space-y-8 pb-12 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded" />
        <div className="h-32 bg-slate-100 rounded-3xl" />
        <div className="h-64 bg-slate-100 rounded-3xl" />
        <div className="h-64 bg-slate-100 rounded-3xl" />
      </div>
    );
  }

  const aiInsight = reports?.ai_insight;
  const sectionsSummary = reports?.sections_summary || [];
  const heatmap = reports?.mastery_heatmap;
  const kcOverview = reports?.kc_performance_overview || [];
  const trajectory = reports?.retention_growth_trajectory || [];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            INVESTIGACIÓN & MODELADO PREDICTIVO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Reportes: Resultados observados y seguimiento de retención
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Telemetría objetiva para el seguimiento de la memoria a largo plazo y la evaluación cuasiexperimental.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="lg"
            onClick={handleExportCSV}
            variant="outline"
            className="rounded-xl text-xs gap-2 border-slate-200 hover:border-teal-400 bg-white shadow-2xs"
          >
            <Download className="w-4 h-4 text-teal-700" />
            {downloadSuccess ? "¡Dataset descargado!" : "Exportar dataset seudonimizado"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AI Insight Card (Captura 23) */}
      {aiInsight && (
        <div className="rounded-3xl p-6 md:p-8 bg-gradient-to-r from-teal-900 via-[#0B2D34] to-[#123E45] text-white shadow-md relative overflow-hidden">
          <div className="max-w-2xl relative z-10 space-y-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 backdrop-blur-sm px-3.5 py-1 text-xs font-medium text-[#69D7C9] border border-[#65D7C9]/30">
              <Sparkles className="w-3.5 h-3.5 text-[#69D7C9]" />
              Insight de Aprendizaje Asistido
            </span>

            <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white">
              {aiInsight.title}
            </h2>

            <p className="text-teal-100/90 text-xs md:text-sm leading-relaxed">
              {aiInsight.message}
            </p>

            {aiInsight.recommended_focus_kc && (
              <div className="pt-2 flex items-center gap-3">
                <Link href="/teacher/activities">
                  <Button className="bg-[#69D7C9] hover:bg-[#52c4b5] text-[#0B2D34] font-bold text-xs rounded-xl shadow-xs">
                    Programar repaso de refuerzo ({aiInsight.recommended_focus_kc})
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sections Telemetry Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {sectionsSummary.map((sec) => (
          <Card key={sec.section_id} className="rounded-2xl border-slate-200/80 p-5 bg-white shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-500">{sec.section_name}</p>
              <Badge variant="outline" className="text-[10px]">
                {sec.students_count} alumnos
              </Badge>
            </div>
            <p className="text-2xl font-extrabold text-slate-900">{sec.average_score}%</p>
            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
              <span>{sec.completed_attempts} cuestionarios evaluados</span>
              <span className="text-teal-700 font-semibold">{sec.reviews_completed} repasos</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Student Mastery Heat Map (Captura 23) */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white shadow-xs space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Student Mastery Heat Map (Componentes de Conocimiento)
          </h2>
          <p className="text-xs text-slate-500">
            Visualización matricial de la precisión observada por estudiante y concepto evaluado
          </p>
        </div>

        {heatmap && heatmap.rows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-center border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-bold text-[10px] uppercase">
                  <th className="py-3 px-4 text-left font-semibold">Estudiante</th>
                  <th className="py-3 px-3 text-left font-semibold">Sección</th>
                  {heatmap.kcs.map((kc) => (
                    <th key={kc.id} className="py-3 px-3 font-semibold min-w-[110px]">
                      {kc.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {heatmap.rows.map((row) => (
                  <tr key={row.student_id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-4 text-left font-semibold text-slate-900">
                      {row.student_name}{" "}
                      <span className="text-[10px] text-slate-400 font-mono">({row.student_code || "EST"})</span>
                    </td>
                    <td className="py-3 px-3 text-left text-slate-500">{row.section_name}</td>
                    {heatmap.kcs.map((kc) => {
                      const cell = row.kcs[kc.id];
                      if (!cell) {
                        return (
                          <td key={kc.id} className="py-3 px-3 text-slate-300">
                            —
                          </td>
                        );
                      }
                      const acc = cell.accuracy;
                      let bgClass = "bg-emerald-50 text-emerald-800 border-emerald-200";
                      if (acc < 60) {
                        bgClass = "bg-rose-50 text-rose-800 border-rose-200";
                      } else if (acc < 80) {
                        bgClass = "bg-amber-50 text-amber-800 border-amber-200";
                      }
                      return (
                        <td key={kc.id} className="py-2 px-2">
                          <span className={`inline-block w-16 py-1 rounded-lg border font-bold text-xs ${bgClass}`}>
                            {acc}%
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-slate-400">
            No hay suficientes respuestas registradas para generar el mapa de calor.
          </div>
        )}
      </Card>

      {/* Two Column Visual Charts (Captura 23) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chart 1: Class Performance Overview */}
        <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white shadow-xs space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Class Performance Overview
            </h2>
            <p className="text-xs text-slate-500">
              Precisión observada por Componente de Conocimiento (KC)
            </p>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={kcOverview} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="kc_name" tick={{ fontSize: 11, fill: "#64748b" }} interval={0} angle={-15} textAnchor="end" />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip formatter={(val: any) => [`${val}%`, "Precisión promedio"]} />
                <Bar dataKey="average_accuracy" fill="#0A635F" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Chart 2: Observed Weekly Retention Trajectory */}
        <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white shadow-xs space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Trayectoria de retención observada
            </h2>
            <p className="text-xs text-slate-500">
              Precisión semanal calculada sobre answer_events. Sin proyecciones
              hasta validar el modelo predictivo.
            </p>
          </div>

          {trajectory.every((point) => point.historical_observed === null) ? (
            <div className="h-72 flex flex-col items-center justify-center text-center gap-2 rounded-2xl bg-slate-50 border border-dashed border-slate-200 px-6">
              <BarChart3 className="w-8 h-8 text-slate-400" />
              <p className="text-sm font-semibold text-slate-800">
                Aún no hay evidencia semanal
              </p>
              <p className="text-xs text-slate-500 max-w-sm">
                Cuando los estudiantes respondan actividades, aquí aparecerá la
                precisión observada por semana.
              </p>
            </div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trajectory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip
                    formatter={(value) => [
                      value === null || value === undefined ? "Sin datos" : `${value}%`,
                      "Precisión observada",
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="historical_observed"
                    name="Precisión observada"
                    stroke="#0A635F"
                    strokeWidth={2.5}
                    dot={{ r: 4 }}
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="text-[11px] text-slate-500 leading-relaxed">
            La curva de olvido proyectada se habilitará cuando exista un modelo
            entrenado y validado (DAS3H/PFA/BKT). Este reporte no presenta
            valores predictivos inventados.
          </p>
        </Card>
      </div>
    </div>
  );
}
