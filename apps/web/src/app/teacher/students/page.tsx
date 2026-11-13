"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Search,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronDown,
  AlertCircle,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  getTeacherStudents,
  TeacherStudentRecord,
} from "@/lib/api/teacher";
import { MASTERY_THRESHOLDS } from "@/lib/data-provenance";

export default function TeacherStudentsPage() {
  const [students, setStudents] = useState<TeacherStudentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSection, setSelectedSection] = useState("all");

  const loadStudents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTeacherStudents(
        selectedSection === "all" ? undefined : selectedSection,
        searchTerm.trim() || undefined
      );
      setStudents(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar la nómina de estudiantes";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudents();
  }, [selectedSection]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadStudents();
  };

  // Unique sections for filter
  const uniqueSections = Array.from(
    new Map(students.map((s) => [s.section_id, s.section_name])).entries()
  );

  const consolidatedCount = students.filter((s) => s.status === "Consolidado").length;
  const inProgressCount = students.filter((s) => s.status === "En proceso").length;
  const supportCount = students.filter((s) => s.status === "Refuerzo sugerido").length;
  // Counters derived from a failed query are unknown, not zero.
  const countersUnavailable = Boolean(error);
  const countText = (value: number) =>
    countersUnavailable ? "—" : String(value);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
          SEGUIMIENTO DE ESTUDIANTES
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
          Nómina y rendimiento de estudiantes
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Supervisa la precisión observada, el estado de consolidación y las
          recomendaciones pendientes por estudiante.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card className="rounded-2xl border-slate-200/80 p-4 bg-white shadow-xs space-y-1">
          <p className="text-xs font-semibold text-slate-500">Total en sección</p>
          <p className="text-2xl font-extrabold text-slate-900">{countText(students.length)}</p>
          <p className="text-[11px] text-slate-400">Registros de perfil</p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-4 bg-white shadow-xs space-y-1">
          <p className="text-xs font-semibold text-slate-500">Consolidados</p>
          <p className="text-2xl font-extrabold text-emerald-700">{countText(consolidatedCount)}</p>
          <p className="text-[11px] text-emerald-600 font-medium">
            Precisión ≥ {MASTERY_THRESHOLDS.consolidated}%
          </p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-4 bg-white shadow-xs space-y-1">
          <p className="text-xs font-semibold text-slate-500">En proceso</p>
          <p className="text-2xl font-extrabold text-amber-600">{countText(inProgressCount)}</p>
          <p className="text-[11px] text-amber-600 font-medium">
            Precisión {MASTERY_THRESHOLDS.inProgress}% –{" "}
            {MASTERY_THRESHOLDS.consolidated - 1}%
          </p>
        </Card>

        <Card className="rounded-2xl border-slate-200/80 p-4 bg-white shadow-xs space-y-1">
          <p className="text-xs font-semibold text-slate-500">Refuerzo sugerido</p>
          <p className="text-2xl font-extrabold text-rose-600">{countText(supportCount)}</p>
          <p className="text-[11px] text-rose-600 font-medium">Prioridad de repaso</p>
        </Card>
      </div>

      {/* Filter Row: Search & Section Dropdown (Captura 21) */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full max-w-sm">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por nombre o código..."
            className="w-full h-10 pl-10 pr-4 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800 placeholder:text-slate-400"
          />
        </form>

        <div className="relative w-full sm:w-auto">
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="w-full sm:w-auto appearance-none bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl pl-4 pr-10 py-2.5 shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          >
            <option value="all">Todas las secciones</option>
            {uniqueSections.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* Students Table Card */}
      <Card className="rounded-3xl border-slate-200/80 shadow-xs bg-white overflow-hidden">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Cargando nómina de estudiantes...
          </div>
        ) : students.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            {error
              ? "No se pudo consultar la nómina: la solicitud falló."
              : "No se encontraron estudiantes para los criterios seleccionados."}
          </div>
        ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px] bg-slate-50/50">
                <th className="py-4 pl-6 pr-4 font-semibold">ESTUDIANTE</th>
                <th className="py-4 px-4 font-semibold">SECCIÓN</th>
                <th className="py-4 px-4 font-semibold">ACTIVIDADES</th>
                <th className="py-4 px-4 font-semibold">PRECISIÓN OBSERVADA</th>
                <th className="py-4 px-4 font-semibold">ESTADO</th>
                <th className="py-4 px-4 font-semibold">RECOMENDACIONES</th>
                <th className="py-4 pr-6 pl-4 text-right font-semibold">ÚLTIMA ACTIVIDAD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.map((student) => (
                  <tr key={student.student_id} className="hover:bg-slate-50/60 transition-colors">
                    {/* Student Pseudonym + Code */}
                    <td className="py-4 pl-6 pr-4">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xs">
                          {student.full_name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{student.full_name}</p>
                          <p className="text-[10px] text-slate-400 font-mono">
                            {student.student_code || "EST"}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Section */}
                    <td className="py-4 px-4 font-medium text-slate-600">
                      {student.section_name}
                    </td>

                    {/* Completed Activities */}
                    <td className="py-4 px-4 font-medium text-slate-700 font-mono">
                      {student.completed_activities} cuestionarios ({student.total_answers} rpts)
                    </td>

                    {/* Observed Accuracy */}
                    <td className="py-4 px-4">
                      {student.observed_accuracy !== null ? (
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800">
                            {student.observed_accuracy}%
                          </span>
                          <div className="w-16">
                            <Progress value={student.observed_accuracy} className="h-1.5" />
                          </div>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-500">
                          Sin evidencia suficiente
                        </span>
                      )}
                    </td>

                    {/* Status Badge */}
                    <td className="py-4 px-4">
                      <Badge
                        variant={
                          student.status === "Consolidado"
                            ? "success"
                            : student.status === "Refuerzo sugerido"
                            ? "warning"
                            : "secondary"
                        }
                        className="text-[10px]"
                      >
                        {student.status}
                      </Badge>
                    </td>

                    {/* Active Recommendations */}
                    <td className="py-4 px-4">
                      {student.active_recommendations_count > 0 ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md">
                          <Sparkles className="w-3 h-3 text-amber-600" />
                          {student.active_recommendations_count} pendiente(s)
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">Sin pendientes</span>
                      )}
                    </td>

                    {/* Last Active */}
                    <td className="py-4 pr-6 pl-4 text-right text-slate-400 text-[11px]">
                      {student.last_active_at
                        ? new Date(student.last_active_at).toLocaleDateString("es-PE", {
                            day: "numeric",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "Sin actividad reciente"}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        )}
      </Card>
    </div>
  );
}
