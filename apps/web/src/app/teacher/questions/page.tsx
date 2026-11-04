"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  FileQuestion,
  BookOpen,
  Check,
  AlertCircle,
  RotateCw,
  Plus,
  Trash2,
  ExternalLink,
  Info,
  Folder,
  FolderKanban,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  contentGenerationApi,
  ContentGenerationJob,
  QuestionDraftItem,
  CanonicalQuestionItem,
  CourseItem,
  KnowledgeComponentItem,
  UpdateDraftPayload,
} from "@/lib/api/content-generation";
import { MetricsCards } from "./components/MetricsCards";
import { QuestionEditorModal } from "./components/QuestionEditorModal";
import { GenerateQuestionsModal } from "./components/GenerateQuestionsModal";
import { RejectReasonDialog } from "./components/RejectReasonDialog";

export default function TeacherQuestionsPage() {
  // Navigation tabs: 'drafts' (cuarentena), 'bank' (canónico), 'jobs' (historial)
  const [activeTab, setActiveTab] = useState<"drafts" | "bank" | "jobs">("drafts");

  // Courses and KCs
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [knowledgeComponents, setKnowledgeComponents] = useState<KnowledgeComponentItem[]>([]);
  const [selectedKcFilter, setSelectedKcFilter] = useState<string>("all");

  // Search & Status filters
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [draftStatusFilter, setDraftStatusFilter] = useState<string>("all");

  // Data states
  const [jobs, setJobs] = useState<ContentGenerationJob[]>([]);
  const [drafts, setDrafts] = useState<QuestionDraftItem[]>([]);
  const [canonicalQuestions, setCanonicalQuestions] = useState<CanonicalQuestionItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Modals state
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState<boolean>(false);
  const [editingDraft, setEditingDraft] = useState<QuestionDraftItem | null>(null);
  const [rejectingDraftId, setRejectingDraftId] = useState<string | null>(null);

  // Batch selection in drafts
  const [selectedDraftIds, setSelectedDraftIds] = useState<Set<string>>(new Set());

  // Show transient notification
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

  // 2. Load Knowledge Components when course changes
  useEffect(() => {
    if (!selectedCourseId) return;
    async function loadKcs() {
      try {
        const kcs = await contentGenerationApi.getCourseKnowledgeComponents(selectedCourseId);
        setKnowledgeComponents(kcs);
      } catch (err) {
        console.error("Error loading course KCs:", err);
      }
    }
    loadKcs();
  }, [selectedCourseId]);

  // 3. Load Main Data: Jobs, Drafts, and Canonical Questions
  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    else setIsRefreshing(true);

    try {
      // A. Load Jobs
      const jobList = await contentGenerationApi.getJobs(
        selectedCourseId || undefined
      );
      setJobs(jobList);

      // B. Load Drafts for all loaded jobs
      let allDrafts: QuestionDraftItem[] = [];
      for (const j of jobList) {
        try {
          const jobDrafts = await contentGenerationApi.getDraftsByJob(j.job_id);
          allDrafts = allDrafts.concat(jobDrafts);
        } catch (e) {
          console.debug(`Could not load drafts for job ${j.job_id}:`, e);
        }
      }
      setDrafts(allDrafts);

      // C. Load Canonical Published Questions
      const canon = await contentGenerationApi.getCanonicalQuestions(
        selectedCourseId || undefined
      );
      setCanonicalQuestions(canon);
    } catch (err) {
      console.error("Error loading question bank data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [selectedCourseId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 4. Polling for in-flight jobs
  useEffect(() => {
    const hasActiveJobs = jobs.some(
      (j) => j.status === "queued" || j.status === "processing"
    );
    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      loadData(true);
    }, 4000);

    return () => clearInterval(interval);
  }, [jobs, loadData]);

  // Handlers for Draft Operations
  const handleSaveDraft = async (draftId: string, payload: UpdateDraftPayload) => {
    const updated = await contentGenerationApi.updateDraft(draftId, payload);
    setDrafts((prev) => prev.map((d) => (d.id === draftId ? updated : d)));
    setEditingDraft(updated);
    showToast("success", "Borrador actualizado con éxito.");
  };

  const handleApproveDraft = async (draftId: string, kcId?: string) => {
    try {
      const resp = await contentGenerationApi.approveDraft(draftId, {
        knowledge_component_id: kcId,
      });
      showToast("success", "Pregunta aprobada e incorporada al banco institucional.");
      // Refresh to update stats and canonical questions
      await loadData(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al aprobar la pregunta.";
      showToast("error", msg);
      throw err;
    }
  };

  const handleBatchApprove = async () => {
    if (selectedDraftIds.size === 0) return;
    const ids = Array.from(selectedDraftIds);

    // Group drafts by job_id
    const draftsByJob: Record<string, string[]> = {};
    for (const did of ids) {
      const d = drafts.find((item) => item.id === did);
      if (d) {
        if (!draftsByJob[d.generation_job_id]) draftsByJob[d.generation_job_id] = [];
        draftsByJob[d.generation_job_id].push(did);
      }
    }

    try {
      let approvedTotal = 0;
      for (const [jobId, jobDraftIds] of Object.entries(draftsByJob)) {
        const res = await contentGenerationApi.batchApproveDrafts(jobId, jobDraftIds);
        approvedTotal += res.approved_count;
      }
      setSelectedDraftIds(new Set());
      showToast("success", `Se aprobaron y publicaron ${approvedTotal} preguntas.`);
      await loadData(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error en aprobación por lote.";
      showToast("error", msg);
    }
  };

  const handleRejectConfirm = async (reason: string) => {
    if (!rejectingDraftId) return;
    try {
      const updated = await contentGenerationApi.rejectDraft(rejectingDraftId, reason);
      setDrafts((prev) => prev.map((d) => (d.id === rejectingDraftId ? updated : d)));
      showToast("success", "Borrador de pregunta descartado.");
      await loadData(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al descartar la pregunta.";
      showToast("error", msg);
    } finally {
      setRejectingDraftId(null);
    }
  };

  // Drafts filtering
  const filteredDrafts = drafts.filter((d) => {
    const matchesSearch =
      d.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.suggested_kc_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.explanation && d.explanation.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus =
      draftStatusFilter === "all" ||
      d.status === draftStatusFilter ||
      (draftStatusFilter === "pending" && (d.status === "draft" || d.status === "edited"));

    const matchesKc =
      selectedKcFilter === "all" ||
      d.knowledge_component_id === selectedKcFilter ||
      d.suggested_kc_name.toLowerCase() ===
        knowledgeComponents.find((k) => k.id === selectedKcFilter)?.name.toLowerCase();

    return matchesSearch && matchesStatus && matchesKc;
  });

  // Canonical bank filtering
  const filteredCanonical = canonicalQuestions.filter((q) => {
    const matchesSearch =
      q.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.knowledge_component_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesKc = selectedKcFilter === "all" || q.knowledge_component_id === selectedKcFilter;
    return matchesSearch && matchesKc;
  });

  // Calculate stats for MetricsCards
  const canonicalCount = canonicalQuestions.length;
  const pendingDraftsCount = drafts.filter((d) => d.status === "draft" || d.status === "edited").length;
  const activeJobsCount = jobs.filter((j) => j.status === "queued" || j.status === "processing").length;
  const rejectedCount = drafts.filter((d) => d.status === "rejected").length;

  return (
    <div className="space-y-6 pb-16">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl text-xs font-semibold animate-in slide-in-from-bottom-2 ${
            notification.type === "success"
              ? "bg-emerald-800 text-white"
              : "bg-rose-800 text-white"
          }`}
        >
          {notification.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-300" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#0A635F] bg-teal-50 px-2.5 py-0.5 rounded-md border border-teal-200">
              MÓDULO DOCENTE M3
            </span>
            <span className="text-xs text-slate-400">• Control Humano en el Bucle</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 mt-1">
            Editor y Banco de Preguntas
          </h1>
          <p className="text-slate-500 text-xs sm:text-sm mt-1 max-w-2xl">
            Genera reactivos a partir de tus materiales curriculares, verifica su fundamento documental y apruébalos para el banco institucional.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadData(true)}
            disabled={isRefreshing}
            className="rounded-xl h-10 px-3 text-xs border-slate-200 text-slate-700 hover:bg-slate-50"
            title="Recargar datos"
          >
            <RotateCw className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Actualizar
          </Button>

          <Button
            size="sm"
            onClick={() => setIsGenerateModalOpen(true)}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl h-10 px-4 text-xs gap-2 shadow-xs transition-all"
          >
            <Sparkles className="w-4 h-4" />
            + Generar preguntas con IA
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <MetricsCards
        canonicalCount={canonicalCount}
        pendingDraftsCount={pendingDraftsCount}
        activeJobsCount={activeJobsCount}
        rejectedCount={rejectedCount}
      />

      {/* Subject Folders Grid (Captura 16: Banco de preguntas - Carpetas por asignatura) */}
      {courses.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold uppercase tracking-wider text-[11px] text-slate-700">
              Carpetas por Asignatura (Banco de Preguntas)
            </span>
            <span>{courses.length} cursos asignados</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {courses.map((course) => {
              const isSelected = course.id === selectedCourseId;
              const courseJobs = jobs.filter((j) => j.course_id === course.id);
              const courseDrafts = drafts.filter((d) => {
                const j = jobs.find((job) => job.job_id === d.generation_job_id);
                return j?.course_id === course.id;
              });

              return (
                <button
                  key={course.id}
                  type="button"
                  onClick={() => setSelectedCourseId(course.id)}
                  className={`p-3.5 rounded-2xl border text-left transition-all ${
                    isSelected
                      ? "bg-teal-50/60 border-teal-500 ring-2 ring-teal-500/20 shadow-xs"
                      : "bg-white border-slate-200/90 hover:border-slate-300 shadow-2xs hover:shadow-xs"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold ${
                        isSelected
                          ? "bg-teal-600 text-white"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      <Folder className="w-4 h-4" />
                    </div>
                    {isSelected && (
                      <span className="text-[10px] font-bold text-teal-700 bg-teal-100 px-2 py-0.5 rounded-full">
                        Activo
                      </span>
                    )}
                  </div>
                  <div className="mt-2.5 space-y-0.5">
                    <h4 className="text-xs sm:text-sm font-bold text-slate-900 truncate">
                      {course.name}
                    </h4>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {course.code}
                    </p>
                    <p className="text-[10px] text-slate-400 pt-1">
                      {courseJobs.length} materiales • {courseDrafts.length} borradores
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Course & KC Filter Row */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-2xs">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por enunciado, concepto o justificación pedagógica..."
            className="w-full h-10 pl-10 pr-4 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-600/30 focus:border-teal-600 transition-all text-slate-800"
          />
        </div>

        {/* Course selector */}
        <select
          value={selectedCourseId}
          onChange={(e) => setSelectedCourseId(e.target.value)}
          className="h-10 px-3 text-xs font-semibold bg-white border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-600/30 w-full sm:w-auto min-w-[160px]"
        >
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.code})
            </option>
          ))}
        </select>

        {/* KC selector */}
        <select
          value={selectedKcFilter}
          onChange={(e) => setSelectedKcFilter(e.target.value)}
          className="h-10 px-3 text-xs font-semibold bg-white border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-600/30 w-full sm:w-auto min-w-[180px]"
        >
          <option value="all">Todos los conceptos (KC)</option>
          {knowledgeComponents.map((kc) => (
            <option key={kc.id} value={kc.id}>
              {kc.name}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation Tabs Header */}
      <div className="flex items-center justify-between border-b border-slate-200">
        <div className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => setActiveTab("drafts")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "drafts"
                ? "border-teal-600 text-teal-800"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Borradores por revisar</span>
            {pendingDraftsCount > 0 && (
              <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full font-bold">
                {pendingDraftsCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("bank")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "bank"
                ? "border-teal-600 text-teal-800"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Banco publicado</span>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-full font-bold">
              {canonicalCount}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("jobs")}
            className={`px-4 py-2.5 text-xs sm:text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "jobs"
                ? "border-teal-600 text-teal-800"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Historial de trabajos</span>
            {activeJobsCount > 0 && (
              <span className="text-[10px] bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded-full font-bold animate-pulse">
                {activeJobsCount} activos
              </span>
            )}
          </button>
        </div>

        {/* Tab-specific actions (e.g. batch approve) */}
        {activeTab === "drafts" && selectedDraftIds.size > 0 && (
          <Button
            size="sm"
            onClick={handleBatchApprove}
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white text-xs font-semibold rounded-xl gap-1.5 shadow-xs mb-1"
          >
            <Check className="w-3.5 h-3.5" />
            Aprobar seleccionadas ({selectedDraftIds.size})
          </Button>
        )}
      </div>

      {/* =========================================================================
          TAB 1: BORRADORES POR REVISAR (Quarantine)
         ========================================================================= */}
      {activeTab === "drafts" && (
        <div className="space-y-4">
          {/* Status filter pills */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold text-[11px] uppercase mr-1">
              Estado:
            </span>
            {[
              { id: "all", label: "Todos los borradores" },
              { id: "pending", label: "Pendientes (Borrador + Editado)" },
              { id: "draft", label: "Solo Borrador IA" },
              { id: "edited", label: "Solo Editados" },
              { id: "rejected", label: "Descartados" },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setDraftStatusFilter(st.id)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                  draftStatusFilter === st.id
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Drafts Cards List */}
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-xs font-medium space-y-2">
              <RotateCw className="w-6 h-6 animate-spin mx-auto text-teal-600" />
              <p>Cargando borradores generados...</p>
            </div>
          ) : filteredDrafts.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto">
                <FileQuestion className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">
                No hay borradores pendientes para el filtro actual
              </h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Sube una guía de clase o presentación PPTX con el botón &quot;+ Generar preguntas con IA&quot; para iniciar un nuevo lote.
              </p>
              <Button
                size="sm"
                onClick={() => setIsGenerateModalOpen(true)}
                className="bg-[#0A635F] hover:bg-[#0B2D34] text-white text-xs font-semibold rounded-xl gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Generar nuevo lote
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredDrafts.map((d) => {
                const isSelected = selectedDraftIds.has(d.id);
                const isTerminal = d.status === "approved" || d.status === "rejected";

                return (
                  <Card
                    key={d.id}
                    className={`rounded-2xl border p-5 bg-white shadow-2xs hover:shadow-xs transition-all ${
                      isSelected
                        ? "border-teal-500 ring-1 ring-teal-500/30 bg-teal-50/10"
                        : "border-slate-200/80 hover:border-teal-300"
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Checkbox for batch approval (only if non-terminal) */}
                      {!isTerminal && (
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            const newSet = new Set(selectedDraftIds);
                            if (e.target.checked) newSet.add(d.id);
                            else newSet.delete(d.id);
                            setSelectedDraftIds(newSet);
                          }}
                          className="mt-1 w-4 h-4 rounded text-teal-600 focus:ring-teal-500 cursor-pointer"
                        />
                      )}

                      <div className="flex-1 space-y-2">
                        {/* Tags row */}
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge
                            variant="outline"
                            className={`text-[10px] font-bold uppercase ${
                              d.status === "approved"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : d.status === "edited"
                                ? "bg-blue-50 text-blue-700 border-blue-200"
                                : d.status === "rejected"
                                ? "bg-rose-50 text-rose-700 border-rose-200"
                                : "bg-amber-50 text-amber-700 border-amber-200"
                            }`}
                          >
                            {d.status === "draft"
                              ? "Borrador IA"
                              : d.status === "edited"
                              ? "Editado por Docente"
                              : d.status === "approved"
                              ? "Aprobado"
                              : "Descartado"}
                          </Badge>

                          <Badge
                            variant="outline"
                            className="text-[10px] font-semibold text-teal-800 bg-teal-50 border-teal-200"
                          >
                            KC: {d.suggested_kc_name}
                          </Badge>

                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                            Dificultad: {(d.difficulty || d.suggested_difficulty || 0.5).toFixed(2)}
                          </span>

                          <span className="text-[11px] text-slate-400">
                            Bloom: {d.bloom_taxonomy || d.suggested_bloom_level}
                          </span>
                        </div>

                        {/* Question Stem */}
                        <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                          {d.question_text}
                        </h3>

                        {/* Options preview */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                          {d.options &&
                            d.options.map((opt, oIdx) => (
                              <div
                                key={oIdx}
                                className={`text-xs px-2.5 py-1.5 rounded-lg flex items-center gap-2 border ${
                                  opt.is_correct
                                    ? "bg-teal-50 text-teal-900 border-teal-200 font-medium"
                                    : "bg-slate-50 text-slate-600 border-slate-100"
                                }`}
                              >
                                <span className="font-mono text-[10px] font-bold text-slate-400">
                                  {String.fromCharCode(65 + oIdx)}.
                                </span>
                                <span className="truncate flex-1">{opt.text}</span>
                                {opt.is_correct && (
                                  <Check className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                                )}
                              </div>
                            ))}
                        </div>

                        {/* Document Source Verification Quote */}
                        {d.source_references && d.source_references.length > 0 && (
                          <div className="text-[11px] text-amber-900 bg-amber-50/70 border border-amber-200/60 rounded-lg p-2.5 flex items-start gap-2">
                            <BookOpen className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                            <div className="space-y-0.5">
                              <span className="font-bold">
                                {d.source_references[0].type === "page"
                                  ? `Página ${d.source_references[0].index}: `
                                  : `Diapositiva ${d.source_references[0].index}: `}
                              </span>
                              <span className="italic">
                                &ldquo;{d.source_references[0].snippet}&rdquo;
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Rejection Reason (if rejected) */}
                        {d.rejection_reason && (
                          <p className="text-[11px] text-rose-700 bg-rose-50 p-2 rounded-lg border border-rose-200">
                            <strong>Motivo de descarte:</strong> {d.rejection_reason}
                          </p>
                        )}
                      </div>

                      {/* Action buttons */}
                      <div className="flex flex-col sm:flex-row items-center gap-2 shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingDraft(d)}
                          className="rounded-xl text-xs h-9 border-slate-200 hover:bg-slate-50 font-semibold"
                        >
                          Revisar / Editar
                        </Button>

                        {!isTerminal && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleApproveDraft(d.id, d.knowledge_component_id || undefined)}
                              className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs h-9 font-semibold gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Aprobar
                            </Button>

                            <button
                              onClick={() => setRejectingDraftId(d.id)}
                              className="p-2 text-slate-400 hover:text-rose-600 transition-colors rounded-lg"
                              title="Descartar borrador"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: BANCO PUBLICADO (Canonical questions)
         ========================================================================= */}
      {activeTab === "bank" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Reactivos institucionales promovidos al banco canónico tras validación docente.
            </p>
            <span className="text-xs font-bold text-slate-700">
              {filteredCanonical.length} preguntas en el banco
            </span>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-xs">
              <RotateCw className="w-6 h-6 animate-spin mx-auto text-teal-600 mb-2" />
              Cargando banco canónico...
            </div>
          ) : filteredCanonical.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-2">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-800">
                Aún no hay preguntas aprobadas en este curso
              </h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Revisa los borradores generados en la pestaña &quot;Borradores por revisar&quot; y apruébalos para incorporarlos aquí.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredCanonical.map((q) => (
                <Card
                  key={q.id}
                  className="rounded-2xl border border-slate-200/80 p-5 bg-white shadow-2xs hover:shadow-xs transition-all space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className="text-[10px] font-semibold text-teal-800 bg-teal-50 border-teal-200"
                      >
                        KC: {q.knowledge_component_name}
                      </Badge>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                        Dificultad: {q.difficulty.toFixed(2)}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(q.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {q.source_draft_id && (
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                        Origen: borrador verificado
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 leading-snug">
                    {q.question_text}
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {q.options &&
                      q.options.map((opt, i) => (
                        <div
                          key={opt.id}
                          className={`text-xs px-3 py-2 rounded-lg flex items-center justify-between border ${
                            opt.is_correct
                              ? "bg-teal-50 text-teal-900 border-teal-200 font-semibold"
                              : "bg-slate-50 text-slate-600 border-slate-100"
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <span className="font-mono text-[10px] text-slate-400">
                              {String.fromCharCode(65 + i)}.
                            </span>
                            <span className="truncate">{opt.option_text}</span>
                          </div>
                          {opt.is_correct && (
                            <Check className="w-3.5 h-3.5 text-teal-600 shrink-0 ml-1" />
                          )}
                        </div>
                      ))}
                  </div>

                  {q.explanation && (
                    <p className="text-[11px] text-slate-500 bg-slate-50/80 p-2.5 rounded-lg border border-slate-100">
                      <strong>Fundamento formativo:</strong> {q.explanation}
                    </p>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: HISTORIAL DE TRABAJOS (Jobs Telemetry)
         ========================================================================= */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Registro histórico y trazabilidad de los procesos de extracción y generación estructurada.
            </p>
            <span className="text-xs font-bold text-slate-700">
              {jobs.length} trabajos registrados
            </span>
          </div>

          {jobs.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-2">
              <Layers className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-800">
                Aún no has generado trabajos de preguntas
              </h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Haz clic en &quot;+ Generar preguntas con IA&quot; para subir tu primer material de clase.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((j) => (
                <Card
                  key={j.job_id}
                  className="rounded-2xl border border-slate-200/80 p-5 bg-white shadow-2xs hover:shadow-xs transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-bold uppercase ${
                            j.status === "review_required"
                              ? "bg-amber-50 text-amber-700 border-amber-200"
                              : j.status === "processing"
                              ? "bg-blue-50 text-blue-700 border-blue-200 animate-pulse"
                              : j.status === "queued"
                              ? "bg-slate-100 text-slate-700 border-slate-200"
                              : j.status === "failed"
                              ? "bg-rose-50 text-rose-700 border-rose-200"
                              : "bg-emerald-50 text-emerald-700 border-emerald-200"
                          }`}
                        >
                          {j.status === "review_required"
                            ? "Revisión Requerida"
                            : j.status === "processing"
                            ? "Procesando Pipeline..."
                            : j.status === "queued"
                            ? "En Cola"
                            : j.status === "failed"
                            ? "Fallido"
                            : j.status}
                        </Badge>

                        <span className="font-mono text-[11px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                          {j.original_filename}
                        </span>

                        <span className="text-[11px] text-slate-400">
                          {(j.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <span>Proveedor: <strong className="text-slate-700">{j.provider} ({j.model_id})</strong></span>
                        <span>•</span>
                        <span>{new Date(j.created_at).toLocaleString()}</span>
                      </div>

                      {j.error_message && (
                        <p className="text-xs text-rose-700 bg-rose-50 p-2 rounded-lg border border-rose-200">
                          {j.error_message}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-xs font-bold text-slate-900">
                          {j.drafts_count} borradores
                        </p>
                        <p className="text-[11px] text-slate-400">
                          producidos
                        </p>
                      </div>

                      {j.status === "review_required" && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setActiveTab("drafts");
                            setDraftStatusFilter("all");
                          }}
                          className="bg-[#0A635F] hover:bg-[#0B2D34] text-white rounded-xl text-xs h-9 font-semibold gap-1.5"
                        >
                          Ver borradores
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Support & Academic Guidance Card (Captura 16: Need Help? We're here for you) */}
      <div className="bg-gradient-to-r from-[#0B2D34] to-[#0A635F] text-white rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm border border-teal-800/40">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-300">
              ¿Dudas con la calibración pedagógica?
            </span>
          </div>
          <p className="text-xs text-teal-100/90 max-w-2xl leading-relaxed">
            Las preguntas aprobadas aquí se resguardan en el banco institucional hasta la activación de los cuestionarios formativos en el Hito M4. Cada reactivo cuenta con trazabilidad completa de su evidencia documental.
          </p>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => setIsGenerateModalOpen(true)}
            className="rounded-xl text-xs font-semibold bg-white text-slate-900 hover:bg-slate-100 border-0 shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-teal-700" />
            + Generar preguntas con IA
          </Button>
        </div>
      </div>

      {/* Question Editor Modal */}
      <QuestionEditorModal
        isOpen={!!editingDraft}
        onClose={() => setEditingDraft(null)}
        draft={editingDraft}
        currentIndex={
          editingDraft
            ? filteredDrafts.findIndex((d) => d.id === editingDraft.id)
            : undefined
        }
        totalDrafts={filteredDrafts.length}
        onNavigate={(direction) => {
          if (!editingDraft) return;
          const idx = filteredDrafts.findIndex((d) => d.id === editingDraft.id);
          if (idx === -1) return;
          const nextIdx =
            direction === "next"
              ? Math.min(filteredDrafts.length - 1, idx + 1)
              : Math.max(0, idx - 1);
          setEditingDraft(filteredDrafts[nextIdx]);
        }}
        knowledgeComponents={knowledgeComponents}
        onSave={handleSaveDraft}
        onApprove={handleApproveDraft}
        onReject={(draftId) => {
          setEditingDraft(null);
          setRejectingDraftId(draftId);
        }}
      />

      {/* Generate Questions Modal */}
      <GenerateQuestionsModal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        courses={courses}
        selectedCourseId={selectedCourseId}
        onJobCreated={async (newJobId) => {
          showToast("success", `Trabajo ${newJobId.slice(0, 8)}... iniciado. Procesando en segundo plano.`);
          await loadData(true);
        }}
      />

      {/* Reject Reason Dialog */}
      <RejectReasonDialog
        isOpen={!!rejectingDraftId}
        onClose={() => setRejectingDraftId(null)}
        onConfirm={handleRejectConfirm}
        questionStem={
          drafts.find((d) => d.id === rejectingDraftId)?.question_text || ""
        }
      />
    </div>
  );
}
