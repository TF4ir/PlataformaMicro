"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ClipboardCheck,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  BookOpen,
  Check,
  AlertCircle,
  RotateCw,
  BarChart3,
  Users,
  ChevronRight,
  X,
  ArrowUpDown,
  FileQuestion,
  HelpCircle,
  Eye,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  learningApi,
  ActivityListItem,
  ActivityDetailResponse,
  ActivityResultsResponse,
  ActivityCreatePayload,
  ActivityStatus,
  ActivityType,
  CourseSectionItem,
  FeedbackPolicy,
} from "@/lib/api/learning";
import {
  contentGenerationApi,
  CourseItem,
  CanonicalQuestionItem,
} from "@/lib/api/content-generation";

export default function TeacherActivitiesPage() {
  const [activities, setActivities] = useState<ActivityListItem[]>([]);
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [selectedResultsActivity, setSelectedResultsActivity] = useState<ActivityResultsResponse | null>(null);
  const [isLoadingResults, setIsLoadingResults] = useState<boolean>(false);

  // Show transient toast notification
  const showToast = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  // 1. Initial Load: Courses
  useEffect(() => {
    async function loadCourses() {
      try {
        const courseList = await contentGenerationApi.getCourses();
        setCourses(courseList);
        if (courseList.length > 0) {
          setSelectedCourseId(courseList[0].id);
        }
      } catch (err) {
        console.error("Error loading courses:", err);
      }
    }
    loadCourses();
  }, []);

  // 2. Load Activities
  const loadActivities = useCallback(async () => {
    setIsLoading(true);
    try {
      const filterStatus = statusFilter !== "all" ? (statusFilter as ActivityStatus) : undefined;
      const data = await learningApi.listTeacherActivities(
        selectedCourseId || undefined,
        filterStatus
      );
      setActivities(data);
    } catch (err: any) {
      console.error("Error loading activities:", err);
      showToast("error", err.message || "Error al cargar cuestionarios.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedCourseId, statusFilter]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  // Publish handler
  const handlePublish = async (activityId: string) => {
    try {
      await learningApi.publishActivity(activityId);
      showToast("success", "¡Cuestionario publicado exitosamente!");
      await loadActivities();
    } catch (err: any) {
      showToast("error", err.message || "No se pudo publicar la actividad.");
    }
  };

  // View results handler
  const handleViewResults = async (activityId: string) => {
    setIsLoadingResults(true);
    try {
      const results = await learningApi.getActivityResults(activityId);
      setSelectedResultsActivity(results);
    } catch (err: any) {
      showToast("error", err.message || "Error al cargar analítica de resultados.");
    } finally {
      setIsLoadingResults(false);
    }
  };

  // Filtered activities list
  const filteredActivities = activities.filter((act) => {
    const matchesSearch =
      act.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      act.course_name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-2xl shadow-lg border text-xs font-semibold animate-in slide-in-from-bottom duration-200 ${
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          {notification.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600" />
          )}
          {notification.message}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            EVALUACIONES FORMATIVAS Y RETENCIÓN
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Gestión de cuestionarios y actividades
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Crea actividades con preguntas aprobadas en M3, asígnalas a tus secciones y supervisa el registro de respuestas.
          </p>
        </div>

        <div>
          <Button
            size="lg"
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            Nuevo cuestionario
          </Button>
        </div>
      </div>

      {/* Filter Row: Course, Status Tabs & Search */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Course selector & Status pills */}
        <div className="flex flex-wrap items-center gap-3">
          {courses.length > 0 && (
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              className="bg-white border border-slate-200 text-slate-800 text-xs font-semibold rounded-xl px-3.5 py-2 shadow-xs focus:outline-none focus:ring-2 focus:ring-teal-600/30"
            >
              <option value="">Todos los cursos</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}

          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80">
            {["all", "draft", "published", "closed"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3.5 py-1 text-xs font-semibold rounded-lg transition-all capitalize ${
                  statusFilter === st
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {st === "all" ? "Todos" : st === "draft" ? "Borradores" : st === "published" ? "Publicados" : "Cerrados"}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Search */}
        <div className="relative w-full lg:w-72">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por título..."
            className="w-full h-9 pl-10 pr-4 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800 placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Activities Table Card */}
      <Card className="rounded-3xl border-slate-200/80 shadow-xs bg-white overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
            <RotateCw className="w-4 h-4 animate-spin text-teal-600" />
            Cargando cuestionarios...
          </div>
        ) : filteredActivities.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mx-auto">
              <ClipboardCheck className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800">No se encontraron cuestionarios</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Aún no has creado cuestionarios para este filtro. Crea uno utilizando preguntas del banco canónico.
            </p>
            <Button
              size="sm"
              onClick={() => setIsCreateModalOpen(true)}
              className="bg-[#0A635F] text-white rounded-xl text-xs gap-1.5 mt-2"
            >
              <Plus className="w-3.5 h-3.5" />
              Crear primer cuestionario
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase font-bold tracking-wider text-[10px] bg-slate-50/50">
                  <th className="py-4 pl-6 pr-4 font-semibold">CUESTIONARIO</th>
                  <th className="py-4 px-4 font-semibold">ESTADO</th>
                  <th className="py-4 px-4 font-semibold">CURSO / SECCIONES</th>
                  <th className="py-4 px-4 font-semibold">PREGUNTAS</th>
                  <th className="py-4 px-4 font-semibold">RETROALIMENTACIÓN</th>
                  <th className="py-4 px-4 font-semibold">INTENTOS</th>
                  <th className="py-4 pr-6 pl-4 text-right font-semibold">ACCIONES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredActivities.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-50/60 transition-colors">
                    {/* Title & Description */}
                    <td className="py-4 pl-6 pr-4 max-w-xs">
                      <p className="font-bold text-slate-900 line-clamp-1">{act.title}</p>
                      {act.description && (
                        <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{act.description}</p>
                      )}
                    </td>

                    {/* Status Badge */}
                    <td className="py-4 px-4">
                      {act.status === "published" ? (
                        <Badge variant="active" className="text-[10px] bg-emerald-100 text-emerald-800 border-emerald-200">
                          PUBLICADO
                        </Badge>
                      ) : act.status === "draft" ? (
                        <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-800 border-amber-200">
                          BORRADOR
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] bg-slate-100 text-slate-600 border-slate-200">
                          CERRADO
                        </Badge>
                      )}
                    </td>

                    {/* Course & Sections */}
                    <td className="py-4 px-4">
                      <p className="font-semibold text-slate-800">{act.course_name}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {act.sections.map((s) => s.section_name).join(", ") || `${act.sections_count} secciones`}
                      </p>
                    </td>

                    {/* Question Count */}
                    <td className="py-4 px-4 font-semibold text-slate-700">
                      {act.questions_count} reactivos
                    </td>

                    {/* Feedback Policy */}
                    <td className="py-4 px-4 text-[11px] text-slate-600">
                      {act.feedback_policy === "immediate_with_explanation"
                        ? "Inmediata c/ explicación"
                        : "Al finalizar intento"}
                    </td>

                    {/* Attempts count */}
                    <td className="py-4 px-4">
                      <span className="font-bold text-slate-900">{act.attempts_count}</span>
                      <span className="text-[11px] text-slate-400 ml-1">intentos</span>
                    </td>

                    {/* Actions */}
                    <td className="py-4 pr-6 pl-4 text-right space-x-2">
                      {act.status === "draft" && (
                        <Button
                          size="sm"
                          onClick={() => handlePublish(act.id)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold px-3 py-1 shadow-xs"
                        >
                          Publicar
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleViewResults(act.id)}
                        disabled={isLoadingResults}
                        className="rounded-xl text-xs font-semibold gap-1.5"
                      >
                        <BarChart3 className="w-3.5 h-3.5 text-teal-700" />
                        Analítica
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal 1: Create Questionnaire */}
      {isCreateModalOpen && (
        <CreateActivityModal
          courses={courses}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={() => {
            setIsCreateModalOpen(false);
            showToast("success", "¡Cuestionario creado exitosamente!");
            loadActivities();
          }}
        />
      )}

      {/* Modal 2: Activity Analytical Results */}
      {selectedResultsActivity && (
        <ActivityResultsModal
          data={selectedResultsActivity}
          onClose={() => setSelectedResultsActivity(null)}
        />
      )}
    </div>
  );
}

// ----------------------------------------------------------------------------
// Create Activity Modal Component
// ----------------------------------------------------------------------------

function CreateActivityModal({
  courses,
  onClose,
  onSuccess,
}: {
  courses: CourseItem[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [courseId, setCourseId] = useState(courses[0]?.id || "");
  const [feedbackPolicy, setFeedbackPolicy] = useState<FeedbackPolicy>("immediate_with_explanation");
  const [maxAttempts, setMaxAttempts] = useState(1);
  const [timeLimitMinutes, setTimeLimitMinutes] = useState<number | undefined>(undefined);

  // Available sections & Canonical questions
  const [availableQuestions, setAvailableQuestions] = useState<CanonicalQuestionItem[]>([]);
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<string[]>([]);
  const [availableSections, setAvailableSections] = useState<CourseSectionItem[]>([]);
  const [sectionIds, setSectionIds] = useState<string[]>([]);
  const [isLoadingBank, setIsLoadingBank] = useState(false);
  const [isLoadingSections, setIsLoadingSections] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Load canonical questions and course sections
  useEffect(() => {
    if (!courseId) return;
    async function loadBankAndSections() {
      setIsLoadingBank(true);
      setIsLoadingSections(true);
      try {
        const [questions, sections] = await Promise.all([
          contentGenerationApi.getCanonicalQuestions(courseId),
          learningApi.getCourseSections(courseId).catch(() => []),
        ]);
        setAvailableQuestions(questions);
        setAvailableSections(sections);
        if (sections.length > 0) {
          setSectionIds(sections.map((s) => s.id));
        } else {
          setSectionIds([]);
        }
      } catch (err) {
        console.error("Error loading canonical questions bank and sections:", err);
      } finally {
        setIsLoadingBank(false);
        setIsLoadingSections(false);
      }
    }
    loadBankAndSections();
  }, [courseId]);


  const toggleQuestionSelection = (qId: string) => {
    setSelectedQuestionIds((prev) =>
      prev.includes(qId) ? prev.filter((id) => id !== qId) : [...prev, qId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!title.trim()) {
      setFormError("Debes especificar un título para el cuestionario.");
      return;
    }
    if (selectedQuestionIds.length === 0) {
      setFormError("Debes seleccionar al menos una pregunta del banco institucional.");
      return;
    }
    if (sectionIds.length === 0) {
      setFormError("Debes asignar al menos una sección destinataria.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: ActivityCreatePayload = {
        title: title.trim(),
        description: description.trim() || null,
        course_id: courseId,
        section_ids: sectionIds,
        question_ids: selectedQuestionIds,
        activity_type: "formative",
        feedback_policy: feedbackPolicy,
        max_attempts: maxAttempts,
        time_limit_minutes: timeLimitMinutes || null,
      };

      await learningApi.createActivity(payload);
      onSuccess();
    } catch (err: any) {
      setFormError(err.message || "Error al crear la actividad educativa.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Crear nuevo cuestionario</h2>
            <p className="text-xs text-slate-500">
              Selecciona preguntas aprobadas en el banco institucional y asigna secciones destinatarias.
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {formError && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          {/* Title & Course */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Título de la actividad *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ej. Concepto central de la actividad"
                className="w-full text-xs h-10 px-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-900"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Curso *</label>
              <select
                value={courseId}
                onChange={(e) => setCourseId(e.target.value)}
                className="w-full text-xs h-10 px-3.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-900 font-medium"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Instrucciones para el estudiante (opcional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Lee atentamente cada reactivo antes de marcar tu respuesta..."
              rows={2}
              className="w-full text-xs p-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-900"
            />
          </div>

          {/* Config: Feedback & Attempts */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Política de retroalimentación</label>
              <select
                value={feedbackPolicy}
                onChange={(e) => setFeedbackPolicy(e.target.value as FeedbackPolicy)}
                className="w-full text-xs h-10 px-3.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-900 font-medium"
              >
                <option value="immediate_with_explanation">Inmediata (pregunta a pregunta)</option>
                <option value="upon_completion">Al completar el intento</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Límite de intentos</label>
              <select
                value={maxAttempts}
                onChange={(e) => setMaxAttempts(Number(e.target.value))}
                className="w-full text-xs h-10 px-3.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-900 font-medium"
              >
                <option value={1}>1 intento</option>
                <option value={2}>2 intentos</option>
                <option value={3}>3 intentos</option>
              </select>
            </div>
          </div>

          {/* Target Sections */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700">Secciones destinatarias *</label>
            {isLoadingSections ? (
              <div className="p-3 text-center text-xs text-slate-400">
                <RotateCw className="w-3.5 h-3.5 animate-spin mx-auto text-teal-600 mb-1" />
                Cargando secciones...
              </div>
            ) : availableSections.length === 0 ? (
              <p className="text-xs text-slate-400 border border-dashed rounded-xl p-3 text-center">
                No hay secciones registradas para este curso.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {availableSections.map((sec) => {
                  const isChecked = sectionIds.includes(sec.id);
                  return (
                    <label
                      key={sec.id}
                      className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border text-xs font-medium cursor-pointer transition-all ${
                        isChecked
                          ? "bg-teal-50 border-teal-600 text-teal-900 ring-1 ring-teal-600/30"
                          : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          setSectionIds((prev) =>
                            prev.includes(sec.id)
                              ? prev.filter((id) => id !== sec.id)
                              : [...prev, sec.id]
                          );
                        }}
                        className="rounded text-teal-600 focus:ring-teal-500 border-slate-300"
                      />
                      <span>{sec.name}</span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>

          {/* Questions selection from Institutional Bank */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-xs font-bold text-slate-900">
                  Seleccionar reactivos del banco institucional ({selectedQuestionIds.length} seleccionados)
                </label>
                <p className="text-[11px] text-slate-500">
                  Solo se muestran preguntas canónicas aprobadas en M3 asociadas a sus Componentes de Conocimiento (KC).
                </p>
              </div>
            </div>

            {isLoadingBank ? (
              <div className="p-6 text-center text-xs text-slate-400">
                <RotateCw className="w-4 h-4 animate-spin mx-auto text-teal-600 mb-1" />
                Cargando banco institucional...
              </div>
            ) : availableQuestions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 border border-dashed rounded-2xl">
                No hay preguntas aprobadas en este curso. Visita el Banco de Preguntas para aprobar borradores.
              </div>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {availableQuestions.map((q) => {
                  const isChecked = selectedQuestionIds.includes(q.id);
                  return (
                    <div
                      key={q.id}
                      onClick={() => toggleQuestionSelection(q.id)}
                      className={`p-3.5 rounded-2xl border text-xs cursor-pointer transition-all flex items-start gap-3 ${
                        isChecked
                          ? "border-teal-600 bg-teal-50/40 ring-1 ring-teal-600"
                          : "border-slate-200 hover:border-slate-300 bg-white"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-1 h-4 w-4 rounded text-teal-600 focus:ring-teal-500 border-slate-300"
                      />
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-[10px] bg-teal-50 text-teal-800 border-teal-200">
                            {q.knowledge_component_name}
                          </Badge>
                          <span className="text-[10px] text-slate-400 font-medium">
                            Dificultad: {q.difficulty.toFixed(2)}
                          </span>
                        </div>
                        <p className="font-semibold text-slate-900 leading-snug">{q.question_text}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </form>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onClose} className="rounded-xl text-xs">
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs font-semibold px-5"
          >
            {isSubmitting ? "Guardando..." : "Guardar en borrador"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------
// Activity Analytical Results Modal Component (M4.4 Teacher View)
// ----------------------------------------------------------------------------

function ActivityResultsModal({
  data,
  onClose,
}: {
  data: ActivityResultsResponse;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"kc" | "questions" | "sections" | "students">("kc");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] bg-teal-50 text-teal-800 border-teal-200">
                {data.course_name}
              </Badge>
              <h2 className="text-lg font-bold text-slate-900">{data.activity_title}</h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Resultados observados en el historial de interacciones inmutables.
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Top KPI Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs bg-slate-50/50 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">PARTICIPACIÓN</p>
              <p className="text-2xl font-extrabold text-slate-900">{data.participation_rate}%</p>
              <p className="text-[11px] text-slate-500">
                {data.completed_attempts} de {data.total_enrolled} alumnos
              </p>
            </Card>

            <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs bg-slate-50/50 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">PUNTAJE PROMEDIO</p>
              <p className="text-2xl font-extrabold text-teal-800">{data.average_score.toFixed(1)}/100</p>
              <p className="text-[11px] text-emerald-600 font-semibold">Calificación observada</p>
            </Card>

            <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs bg-slate-50/50 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">TOTAL INTENTOS</p>
              <p className="text-2xl font-extrabold text-slate-900">{data.total_attempts}</p>
              <p className="text-[11px] text-slate-500">{data.completed_attempts} finalizados</p>
            </Card>

            <Card className="rounded-2xl border-slate-200/80 p-4 shadow-xs bg-slate-50/50 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">KNOWLEDGE COMPONENTS</p>
              <p className="text-2xl font-extrabold text-purple-800">{data.kc_breakdown.length}</p>
              <p className="text-[11px] text-slate-500">Conceptos modelados</p>
            </Card>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex border-b border-slate-200 gap-6 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("kc")}
              className={`pb-2.5 transition-colors border-b-2 ${
                activeTab === "kc"
                  ? "border-teal-700 text-teal-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Dominio por Knowledge Component
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`pb-2.5 transition-colors border-b-2 ${
                activeTab === "questions"
                  ? "border-teal-700 text-teal-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Rendimiento por Reactivo
            </button>
            <button
              onClick={() => setActiveTab("sections")}
              className={`pb-2.5 transition-colors border-b-2 ${
                activeTab === "sections"
                  ? "border-teal-700 text-teal-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Desglose por Sección
            </button>
            <button
              onClick={() => setActiveTab("students")}
              className={`pb-2.5 transition-colors border-b-2 ${
                activeTab === "students"
                  ? "border-teal-700 text-teal-800"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Intentos de Estudiantes ({data.student_attempts.length})
            </button>
          </div>

          {/* Tab 1: Knowledge Components Breakdown */}
          {activeTab === "kc" && (
            <div className="space-y-3">
              {data.kc_breakdown.map((kc) => (
                <div key={kc.knowledge_component_id} className="p-4 rounded-2xl border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-900">{kc.knowledge_component_name}</span>
                    <span className="font-extrabold text-teal-800">{kc.mastery_rate}% acierto</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-teal-700 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${kc.mastery_rate}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {kc.correct_answers} respuestas correctas de {kc.total_answers} intentos registrados
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Tab 2: Question Accuracy Breakdown */}
          {activeTab === "questions" && (
            <div className="space-y-2.5">
              {data.questions_breakdown.map((q) => (
                <div key={q.question_id} className="p-4 rounded-2xl border border-slate-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-500">Pregunta {q.order_index}</span>
                    <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-700">
                      {q.knowledge_component_name}
                    </Badge>
                  </div>
                  <p className="font-semibold text-slate-900">{q.question_text}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>
                      {q.correct_answers} correctas de {q.total_answers} respuestas
                    </span>
                    <span className="font-bold text-teal-800">{q.accuracy_rate}% de precisión</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Sections Breakdown */}
          {activeTab === "sections" && (
            <div className="space-y-3">
              {data.sections_breakdown.map((sec) => (
                <div key={sec.section_id} className="p-4 rounded-2xl border border-slate-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{sec.section_name}</span>
                    <span className="font-bold text-teal-800">Promedio: {sec.average_score.toFixed(1)}/100</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {sec.participating_students} estudiantes evaluados de {sec.enrolled_count} matriculados ({sec.completed_attempts} intentos completados)
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Tab 4: Student Attempts Table */}
          {activeTab === "students" && (
            <div className="border border-slate-200 rounded-2xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-400 uppercase text-[10px] font-bold">
                    <th className="py-3 px-4">CÓDIGO</th>
                    <th className="py-3 px-4">ESTUDIANTE</th>
                    <th className="py-3 px-4">SECCIÓN</th>
                    <th className="py-3 px-4">PUNTAJE</th>
                    <th className="py-3 px-4">ESTADO</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.student_attempts.map((att) => (
                    <tr key={att.attempt_id}>
                      <td className="py-3 px-4 font-mono font-medium text-slate-500">{att.student_code || "—"}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">{att.student_name}</td>
                      <td className="py-3 px-4 text-slate-600">{att.section_name}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        {att.score !== null ? `${att.score.toFixed(1)}/100` : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {att.status === "completed" ? "Completado" : "En curso"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end">
          <Button onClick={onClose} className="rounded-xl text-xs bg-slate-800 text-white font-semibold">
            Cerrar analítica
          </Button>
        </div>
      </div>
    </div>
  );
}
