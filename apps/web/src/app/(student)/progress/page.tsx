"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ChevronDown,
  TrendingUp,
  Award,
  CheckCircle,
  Flame,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockStudentAnalytics } from "@/lib/mock-data";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function StudentProgressPage() {
  const [timeRange, setTimeRange] = useState("30");
  const data = mockStudentAnalytics;

  return (
    <div className="space-y-8 pb-12">
      {/* Header with Date Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Mi progreso
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Observa tus avances y decide dónde enfocar tu próximo esfuerzo.
          </p>
        </div>

        <div className="relative inline-block">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="appearance-none bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl pl-4 pr-10 py-2.5 shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          >
            <option value="7">Últimos 7 días</option>
            <option value="30">Últimos 30 días</option>
            <option value="90">Último trimestre</option>
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Completed Activities */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Actividades completadas
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {data.completedActivities}
          </p>
          <p className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
            ↑ {data.completedThisMonth} este mes
          </p>
        </Card>

        {/* Card 2: Observed Accuracy */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Precisión observada
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {data.observedAccuracy}%
          </p>
          <p className="text-xs font-medium text-slate-400">
            En {data.totalResponses} respuestas
          </p>
        </Card>

        {/* Card 3: Consolidated Concepts */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">
            Conceptos consolidados
          </p>
          <p className="text-3xl font-extrabold text-slate-900">
            {data.consolidatedConcepts}
            <span className="text-lg font-normal text-slate-400">
              /{data.totalConcepts}
            </span>
          </p>
          <p className="text-xs font-medium text-slate-500">Ciencias</p>
        </Card>

        {/* Card 4: Streak */}
        <Card className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white space-y-3">
          <p className="text-xs font-semibold text-slate-500">Racha actual</p>
          <p className="text-3xl font-extrabold text-slate-900">
            {data.currentStreakDays}{" "}
            <span className="text-lg font-normal text-slate-400">días</span>
          </p>
          <p className="text-xs font-medium text-slate-400">
            Tu mejor racha: {data.bestStreakDays} días
          </p>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Evolution Chart (7 cols) */}
        <Card className="lg:col-span-7 rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Evolución de tus resultados
              </h2>
              <p className="text-xs text-slate-500">
                Porcentaje de respuestas correctas observadas
              </p>
            </div>
            <Badge
              variant="outline"
              className="text-[10px] font-bold uppercase tracking-wider text-teal-800 bg-teal-50 border-teal-200 self-start sm:self-auto"
            >
              DATOS OBSERVADOS
            </Badge>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.evolutionData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={{ stroke: "#e2e8f0" }}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                />
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  tickFormatter={(val) => `${val}%`}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, "Precisión"]}
                  contentStyle={{
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.05)",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#0f766e"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorAccuracy)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Concept Breakdown Donut (5 cols) */}
        <Card className="lg:col-span-5 rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Estado de conceptos
            </h2>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 py-2">
            {/* Donut Chart */}
            <div className="relative w-44 h-44 flex items-center justify-center flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.conceptStatusBreakdown}
                    innerRadius={52}
                    outerRadius={68}
                    paddingAngle={4}
                    dataKey="count"
                  >
                    {data.conceptStatusBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-2xl font-extrabold text-slate-900">
                  {data.totalConcepts}
                </span>
                <span className="text-[10px] text-slate-400 font-medium">
                  conceptos
                </span>
              </div>
            </div>

            {/* Legend list */}
            <div className="space-y-3">
              {data.conceptStatusBreakdown.map((item) => (
                <div key={item.status} className="flex items-center gap-2 text-xs">
                  <div
                    className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-slate-600 font-medium">{item.status}</span>
                  <span className="text-slate-900 font-bold ml-auto pl-4">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Empathetic Clarification */}
          <div className="rounded-2xl bg-[#f5f3ff] p-4 border border-[#ede9fe] flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-[#7c3aed] flex-shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed text-[#5b21b6]">
              <strong className="font-semibold">Estimación orientativa:</strong>{" "}
              La retención estimada complementa, pero no reemplaza, tus
              resultados reales.
            </div>
          </div>
        </Card>
      </div>

      {/* Historial de Repasos Table */}
      <Card className="rounded-3xl border-slate-200/80 p-6 md:p-8 shadow-xs bg-white space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Historial de repasos
          </h2>
          <p className="text-xs text-slate-500">Tus últimas actividades</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px]">
                <th className="pb-3 pr-4 font-semibold">CONCEPTO</th>
                <th className="pb-3 px-4 font-semibold">FECHA</th>
                <th className="pb-3 px-4 font-semibold">RESULTADO OBSERVADO</th>
                <th className="pb-3 pl-4 font-semibold text-right">ESTADO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.history.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-4 pr-4 font-bold text-slate-900">
                    {row.concept}
                  </td>
                  <td className="py-4 px-4 text-slate-500 font-medium">
                    {row.date}
                  </td>
                  <td className="py-4 px-4 font-semibold text-slate-700">
                    {row.observedResult}
                  </td>
                  <td className="py-4 pl-4 text-right">
                    <Badge
                      variant={row.status === "Consolidado" ? "active" : "lavender"}
                      className="text-[11px] font-semibold"
                    >
                      {row.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
