"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  ChevronDown,
  Sparkles,
  BookOpen,
  Layers,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Eye,
  Send,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  getTeacherCourses,
  TeacherCourseDetail,
} from "@/lib/api/teacher";
import {
  listMicrocontents,
  createMicrocontent,
  publishMicrocontent,
  MicrocontentListItem,
} from "@/lib/api/microcontents";

export default function TeacherCoursesPage() {
  const [activeTab, setActiveTab] = useState<"courses" | "microcontents">("courses");
  const [courses, setCourses] = useState<TeacherCourseDetail[]>([]);
  const [microcontents, setMicrocontents] = useState<MicrocontentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCourseId, setSelectedCourseId] = useState<string>("all");

  // Create Microcontent Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [selectedKCId, setSelectedKCId] = useState("");
  const [newSummary, setNewSummary] = useState("");
  const [newDurationMin, setNewDurationMin] = useState(3);
  const [modalFeedback, setModalFeedback] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [crs, mcs] = await Promise.all([
        getTeacherCourses(),
        listMicrocontents().catch(() => []),
      ]);
      setCourses(crs);
      setMicrocontents(mcs);
      if (crs.length > 0 && crs[0].units.length > 0 && crs[0].units[0].kcs.length > 0) {
        setSelectedKCId(crs[0].units[0].kcs[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar cursos";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateMicrocontent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !selectedKCId) {
      setModalFeedback("Por favor ingresa un título y selecciona un componente de conocimiento.");
      return;
    }

    try {
      setCreating(true);
      setModalFeedback(null);
      const created = await createMicrocontent({
        knowledge_component_id: selectedKCId,
        title: newTitle.trim(),
        content_type: "text_summary",
        estimated_duration_seconds: newDurationMin * 60,
        content_body: {
          summary: newSummary.trim() || `Contenido de repaso para afianzar ${newTitle}`,
          sections: [
            {
              id: 1,
              navTitle: "Conceptos clave",
              heading: newTitle.trim(),
              tag: "Microlección",
              lead: newSummary.trim() || "Revisa las nociones fundamentales de este tema.",
              durationMinutes: newDurationMin,
              keyTakeaways: [
                { label: "Idea principal", text: "Concepto central a recordar para la evaluación." },
              ],
            },
          ],
        },
        is_published: true,
      });

      setIsModalOpen(false);
      setNewTitle("");
      setNewSummary("");
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al guardar microcontenido";
      setModalFeedback(msg);
    } finally {
      setCreating(false);
    }
  };

  const handlePublish = async (id: string) => {
    try {
      await publishMicrocontent(id);
      await loadData();
    } catch (err) {
      console.error("Error publishing microcontent:", err);
    }
  };

  // Flatten all available KCs for dropdowns
  const allKCs = courses.flatMap((c) =>
    c.units.flatMap((u) =>
      u.kcs.map((kc) => ({
        id: kc.id,
        name: `${kc.name} (${c.name} - ${u.title})`,
      }))
    )
  );

  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.code.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const filteredMicrocontents = microcontents.filter((m) => {
    const matchesSearch =
      m.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.knowledge_component_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            CONTENIDO EDUCATIVO & MALLA CURRICULAR
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Gestión de cursos y microcontenidos
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Organiza unidades, componentes de conocimiento (KC) y microlecciones para la política adaptativa.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="lg"
            onClick={() => setIsModalOpen(true)}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            Nuevo microcontenido
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center gap-6 text-sm font-semibold">
          <button
            onClick={() => setActiveTab("courses")}
            className={`pb-2 transition-colors relative ${
              activeTab === "courses" ? "text-teal-800 font-bold" : "text-slate-400 hover:text-slate-700"
            }`}
          >
            Cursos y estructura curricular ({courses.length})
            {activeTab === "courses" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-700" />}
          </button>

          <button
            onClick={() => setActiveTab("microcontents")}
            className={`pb-2 transition-colors relative ${
              activeTab === "microcontents" ? "text-teal-800 font-bold" : "text-slate-400 hover:text-slate-700"
            }`}
          >
            Microcontenidos de repaso ({microcontents.length})
            {activeTab === "microcontents" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-700" />}
          </button>
        </div>

        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/30"
          />
        </div>
      </div>

      {/* Tab 1: Courses & Curricular Tree */}
      {activeTab === "courses" && (
        <div className="space-y-6">
          {loading ? (
            <div className="space-y-4 animate-pulse">
              <div className="h-40 bg-slate-100 rounded-3xl" />
              <div className="h-40 bg-slate-100 rounded-3xl" />
            </div>
          ) : filteredCourses.length === 0 ? (
            <Card className="p-8 text-center rounded-2xl border-dashed">
              <p className="text-xs text-slate-400">No se encontraron cursos asignados.</p>
            </Card>
          ) : (
            filteredCourses.map((c) => (
              <Card key={c.course_id} className="rounded-3xl border-slate-200/80 p-6 md:p-8 bg-white shadow-xs space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="success" className="text-[10px]">
                        {c.code}
                      </Badge>
                      <Badge variant="outline" className="text-[10px]">
                        {c.sections.length} secciones asignadas
                      </Badge>
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900">{c.name}</h2>
                    <p className="text-xs text-slate-500">{c.description || "Asignatura oficial de 5to de secundaria."}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <Link href="/teacher/activities">
                      <Button variant="outline" size="sm" className="rounded-xl text-xs">
                        {c.published_activities_count} Actividades
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Units and KCs Tree */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                    Unidades Temáticas y Componentes de Conocimiento (KC)
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {c.units.map((unit) => (
                      <div key={unit.id} className="p-5 rounded-2xl bg-slate-50 border border-slate-200/70 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-slate-900">
                            Unidad {unit.order_index}: {unit.title}
                          </h4>
                          <span className="text-[11px] text-slate-400 font-medium">
                            {unit.kcs.length} KCs
                          </span>
                        </div>

                        <div className="space-y-2 pt-1">
                          {unit.kcs.map((kc) => (
                            <div
                              key={kc.id}
                              className="p-2.5 rounded-xl bg-white border border-slate-200/60 flex items-center justify-between text-xs"
                            >
                              <div>
                                <p className="font-semibold text-slate-800">{kc.name}</p>
                                <p className="text-[10px] text-slate-400">
                                  Dificultad prior: {kc.difficulty_prior} · {kc.questions_count} preguntas
                                </p>
                              </div>
                              <Badge variant="lavender" className="text-[10px]">
                                {kc.microcontents_count} microcontenidos
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Microcontents Catalog (Captura 22) */}
      {activeTab === "microcontents" && (
        <Card className="rounded-3xl border-slate-200/80 shadow-xs bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px] bg-slate-50/50">
                  <th className="py-4 pl-6 pr-4 font-semibold">TÍTULO DEL MICROCONTENIDO</th>
                  <th className="py-4 px-4 font-semibold">COMPONENTE DE CONOCIMIENTO (KC)</th>
                  <th className="py-4 px-4 font-semibold">FORMATO</th>
                  <th className="py-4 px-4 font-semibold">DURACIÓN ESTIMADA</th>
                  <th className="py-4 px-4 font-semibold">ESTADO</th>
                  <th className="py-4 pr-6 pl-4 text-right font-semibold">ACCIONES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredMicrocontents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No hay microcontenidos registrados aún. Crea uno con el botón superior.
                    </td>
                  </tr>
                ) : (
                  filteredMicrocontents.map((mc) => (
                    <tr key={mc.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 pl-6 pr-4">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center flex-shrink-0">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-bold text-slate-900">{mc.title}</p>
                            <p className="text-[10px] text-slate-400">
                              {mc.course_name ? `${mc.course_name} · ` : ""}{mc.unit_title || ""}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-4 font-semibold text-teal-800">
                        {mc.knowledge_component_name}
                      </td>

                      <td className="py-4 px-4 text-slate-600">
                        <Badge variant="outline" className="text-[10px]">
                          {mc.content_type}
                        </Badge>
                      </td>

                      <td className="py-4 px-4 text-slate-600 flex items-center gap-1.5 pt-5">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {Math.ceil(mc.estimated_duration_seconds / 60)} min
                      </td>

                      <td className="py-4 px-4">
                        <Badge
                          variant={mc.is_published ? "success" : "secondary"}
                          className="text-[10px]"
                        >
                          {mc.is_published ? "Publicado" : "Borrador"}
                        </Badge>
                      </td>

                      <td className="py-4 pr-6 pl-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`/learn/${mc.id}`} target="_blank">
                            <Button variant="ghost" size="sm" className="h-8 text-xs text-teal-700 hover:text-teal-900 gap-1">
                              <Eye className="w-3.5 h-3.5" />
                              Previsualizar
                            </Button>
                          </Link>

                          {!mc.is_published && (
                            <Button
                              size="sm"
                              onClick={() => handlePublish(mc.id)}
                              className="h-8 bg-[#0A635F] text-white text-xs rounded-lg gap-1"
                            >
                              <Send className="w-3 h-3" />
                              Publicar
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Modal: Nuevo Microcontenido */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-xl font-bold text-slate-900">Crear microcontenido</h3>
                <p className="text-xs text-slate-500">Diseñado para sesiones de 3 a 5 minutos</p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalFeedback && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
                {modalFeedback}
              </div>
            )}

            <form onSubmit={handleCreateMicrocontent} className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Título de la lección</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ej. Fotosíntesis: Fase luminosa y pigmentos"
                  className="w-full h-10 px-3 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-600/30"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Componente de Conocimiento (KC)</label>
                <select
                  value={selectedKCId}
                  onChange={(e) => setSelectedKCId(e.target.value)}
                  className="w-full h-10 px-3 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-600/30"
                >
                  {allKCs.map((kc) => (
                    <option key={kc.id} value={kc.id}>
                      {kc.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Duración estimada (minutos)</label>
                <input
                  type="number"
                  min={1}
                  max={15}
                  value={newDurationMin}
                  onChange={(e) => setNewDurationMin(parseInt(e.target.value) || 3)}
                  className="w-full h-10 px-3 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-600/30"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Resumen o concepto central</label>
                <textarea
                  rows={3}
                  value={newSummary}
                  onChange={(e) => setNewSummary(e.target.value)}
                  placeholder="Explica sintéticamente los puntos que el estudiante debe recordar..."
                  className="w-full p-3 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-600/30"
                />
              </div>

              <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl text-xs"
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={creating}
                  className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs font-semibold"
                >
                  {creating ? "Guardando..." : "Crear y publicar"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
