"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Bookmark,
  Sparkles,
  Trash2,
  Plus,
  BookOpen,
  HelpCircle,
  Save,
  Check,
  Eye,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  GripVertical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  QuestionDraftItem,
  QuestionOptionDraft,
  KnowledgeComponentItem,
  UpdateDraftPayload,
} from "@/lib/api/content-generation";

interface QuestionEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  draft: QuestionDraftItem | null;
  currentIndex?: number;
  totalDrafts?: number;
  onNavigate?: (direction: "prev" | "next") => void;
  knowledgeComponents: KnowledgeComponentItem[];
  onSave: (draftId: string, payload: UpdateDraftPayload) => Promise<void>;
  onApprove: (draftId: string, kcId?: string) => Promise<void>;
  onReject: (draftId: string) => void;
}

const BLOOM_LEVELS = [
  { value: "remember", label: "Recuerdo (Remember)" },
  { value: "understand", label: "Comprensión (Understand)" },
  { value: "apply", label: "Aplicación (Apply)" },
  { value: "analyze", label: "Análisis (Analyze)" },
  { value: "evaluate", label: "Evaluación (Evaluate)" },
  { value: "create", label: "Creación (Create)" },
];

const DIFFICULTY_PRESETS = [
  { value: 0.35, label: "Básica (0.35)", desc: "Familiaridad conceptual y recuerdo directo" },
  { value: 0.55, label: "Intermedia (0.55)", desc: "Comprensión y aplicación guiada" },
  { value: 0.8, label: "Avanzada (0.80)", desc: "Análisis profundo y resolución de problemas" },
];

export function QuestionEditorModal({
  isOpen,
  onClose,
  draft,
  currentIndex,
  totalDrafts,
  onNavigate,
  knowledgeComponents,
  onSave,
  onApprove,
  onReject,
}: QuestionEditorModalProps) {
  // Form fields
  const [questionText, setQuestionText] = useState("");
  const [options, setOptions] = useState<QuestionOptionDraft[]>([]);
  const [explanation, setExplanation] = useState("");
  const [selectedKcId, setSelectedKcId] = useState<string>("");
  const [difficulty, setDifficulty] = useState<number>(0.5);
  const [bloomTaxonomy, setBloomTaxonomy] = useState<string>("understand");

  // State management
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Right pane tab: "preview" (Captura 17) or "source" (Captura 18 & 19)
  const [activeRightTab, setActiveRightTab] = useState<"preview" | "source">("preview");

  // Simulated preview interactive choice selection
  const [previewSelectedOptionIndex, setPreviewSelectedOptionIndex] = useState<number | null>(null);

  // Document explorer viewer controls (Captura 18)
  const [docZoom, setDocZoom] = useState<number>(100);
  const [docPage, setDocPage] = useState<number>(1);

  useEffect(() => {
    if (draft) {
      setQuestionText(draft.question_text || "");
      setOptions(
        draft.options && draft.options.length > 0
          ? draft.options.map((o) => ({ ...o }))
          : [
              { text: "", is_correct: true },
              { text: "", is_correct: false },
            ]
      );
      setExplanation(draft.explanation || "");
      setDifficulty(draft.difficulty || draft.suggested_difficulty || 0.5);
      setBloomTaxonomy(draft.bloom_taxonomy || draft.suggested_bloom_level || "understand");

      // Auto-match KC by id or name
      if (draft.knowledge_component_id) {
        setSelectedKcId(draft.knowledge_component_id);
      } else if (draft.suggested_kc_name) {
        const matched = knowledgeComponents.find(
          (kc) =>
            kc.name.toLowerCase().trim() === draft.suggested_kc_name.toLowerCase().trim()
        );
        if (matched) setSelectedKcId(matched.id);
        else if (knowledgeComponents.length > 0) setSelectedKcId(knowledgeComponents[0].id);
      } else if (knowledgeComponents.length > 0) {
        setSelectedKcId(knowledgeComponents[0].id);
      }

      if (draft.source_references && draft.source_references.length > 0) {
        setDocPage(draft.source_references[0].index || 1);
      } else {
        setDocPage(1);
      }

      setValidationError(null);
      setSaveSuccess(false);
      setPreviewSelectedOptionIndex(null);
    }
  }, [draft, knowledgeComponents]);

  if (!isOpen || !draft) return null;

  const handleOptionTextChange = (index: number, text: string) => {
    const updated = [...options];
    updated[index].text = text;
    setOptions(updated);
  };

  const handleMisconceptionChange = (index: number, mis: string) => {
    const updated = [...options];
    updated[index].misconception_explanation = mis;
    setOptions(updated);
  };

  const handleSetCorrectOption = (selectedIndex: number) => {
    const updated = options.map((opt, i) => ({
      ...opt,
      is_correct: i === selectedIndex,
      misconception_explanation: i === selectedIndex ? null : opt.misconception_explanation,
    }));
    setOptions(updated);
  };

  const handleAddOption = () => {
    if (options.length >= 6) return;
    setOptions([...options, { text: "", is_correct: false, misconception_explanation: "" }]);
  };

  const handleRemoveOption = (index: number) => {
    if (options.length <= 2) return;
    const isRemovingCorrect = options[index].is_correct;
    const updated = options.filter((_, i) => i !== index);
    if (isRemovingCorrect && updated.length > 0) {
      updated[0].is_correct = true;
    }
    setOptions(updated);
  };

  const validateForm = (): boolean => {
    if (!questionText.trim()) {
      setValidationError("El enunciado de la pregunta no puede estar vacío.");
      return false;
    }
    if (options.length < 2 || options.length > 6) {
      setValidationError("La pregunta debe contener entre 2 y 6 alternativas.");
      return false;
    }
    for (let i = 0; i < options.length; i++) {
      if (!options[i].text.trim()) {
        setValidationError(`La alternativa ${i + 1} no puede estar vacía.`);
        return false;
      }
    }
    const correctCount = options.filter((o) => o.is_correct).length;
    if (correctCount !== 1) {
      setValidationError("Debes marcar exactamente una alternativa como correcta.");
      return false;
    }
    if (!explanation.trim()) {
      setValidationError("Debes proporcionar una explicación o fundamento pedagógico.");
      return false;
    }
    if (!selectedKcId) {
      setValidationError("Debes asociar un Componente de Conocimiento (KC) institucional.");
      return false;
    }
    setValidationError(null);
    return true;
  };

  const handleSaveDraft = async () => {
    if (!validateForm()) return;
    setIsSaving(true);
    try {
      await onSave(draft.id, {
        question_text: questionText.trim(),
        options: options.map((o) => ({
          text: o.text.trim(),
          is_correct: o.is_correct,
          misconception_explanation: o.is_correct ? null : o.misconception_explanation || null,
        })),
        explanation: explanation.trim(),
        difficulty,
        bloom_taxonomy: bloomTaxonomy,
        knowledge_component_id: selectedKcId,
        expected_updated_at: draft.updated_at,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al guardar el borrador.";
      setValidationError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleApproveDraft = async () => {
    if (!validateForm()) return;
    setIsApproving(true);
    try {
      // 1. Guardar cambios si hubo edición
      await onSave(draft.id, {
        question_text: questionText.trim(),
        options: options.map((o) => ({
          text: o.text.trim(),
          is_correct: o.is_correct,
          misconception_explanation: o.is_correct ? null : o.misconception_explanation || null,
        })),
        explanation: explanation.trim(),
        difficulty,
        bloom_taxonomy: bloomTaxonomy,
        knowledge_component_id: selectedKcId,
        expected_updated_at: draft.updated_at,
      });

      // 2. Promover atómicamente a canónica
      await onApprove(draft.id, selectedKcId);

      // Si hay más borradores en lote, avanzar al siguiente
      if (onNavigate && currentIndex !== undefined && totalDrafts !== undefined && currentIndex + 1 < totalDrafts) {
        onNavigate("next");
      } else {
        onClose();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al aprobar la pregunta.";
      setValidationError(msg);
    } finally {
      setIsApproving(false);
    }
  };

  const isTerminal = draft.status === "approved" || draft.status === "rejected";
  const sourceRef = draft.source_references && draft.source_references.length > 0 ? draft.source_references[0] : null;
  const selectedKcName = knowledgeComponents.find((k) => k.id === selectedKcId)?.name || draft.suggested_kc_name;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-6xl w-full max-h-[94vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden my-auto">
        {/* Modal Header (Captura 17 & 19) */}
        <div className="px-6 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-teal-600/10 text-teal-700 flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold text-slate-900">
                  Revisión y Aprobación de Preguntas
                </h2>
                {currentIndex !== undefined && totalDrafts !== undefined && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                    {currentIndex + 1} de {totalDrafts}
                  </span>
                )}
                <Badge
                  variant="outline"
                  className={`text-[10px] font-bold uppercase ${
                    draft.status === "approved"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : draft.status === "edited"
                      ? "bg-blue-50 text-blue-700 border-blue-200"
                      : draft.status === "rejected"
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-amber-50 text-amber-700 border-amber-200"
                  }`}
                >
                  {draft.status === "draft"
                    ? "Borrador IA"
                    : draft.status === "edited"
                    ? "Editado por Docente"
                    : draft.status === "approved"
                    ? "Aprobado (Canónico)"
                    : "Descartado"}
                </Badge>
              </div>
              <p className="text-[11px] text-slate-500">
                Verifica la procedencia documental, edita el reactivo y aprueba su publicación institucional.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1.5 transition-colors"
            title="Cerrar ventana"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body: Split Screen (Capturas 17, 18, 19) */}
        <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
          {/* =========================================================================
              LEFT COLUMN (7 cols): Compose Question & Manage Options (Captura 17)
             ========================================================================= */}
          <div className="lg:col-span-7 p-5 sm:p-6 space-y-5 overflow-y-auto max-h-[calc(94vh-130px)]">
            {validationError && (
              <div className="flex items-start gap-2.5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs animate-in slide-in-from-top-1">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{validationError}</span>
              </div>
            )}

            {saveSuccess && (
              <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold animate-in fade-in">
                <Check className="w-4 h-4" />
                <span>Borrador guardado correctamente con estado &apos;editado&apos;.</span>
              </div>
            )}

            {/* Enunciado / Stem Editor */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center justify-between">
                <span>Enunciado de la Pregunta (Stem)</span>
                <span className="text-[11px] font-normal text-slate-400">
                  {questionText.length} caracteres
                </span>
              </label>
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                disabled={isTerminal}
                rows={3}
                placeholder="Escribe el enunciado claro y contextualizado del reactivo..."
                className="w-full text-xs sm:text-sm p-3.5 border border-slate-200 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none resize-none transition-all disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>

            {/* Alternativas de Respuesta (2 a 6 opciones) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <span>Alternativas de Respuesta</span>
                  <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                    {options.length} opciones
                  </span>
                </label>

                {!isTerminal && options.length < 6 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleAddOption}
                    className="text-xs h-7 gap-1 rounded-lg border-teal-200 text-teal-700 hover:bg-teal-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    + Añadir alternativa
                  </Button>
                )}
              </div>

              <p className="text-[11px] text-slate-500">
                Marca el selector circular para indicar la <strong>única respuesta correcta</strong>. En los distractores, anota el error conceptual diagnosticado.
              </p>

              <div className="space-y-2.5">
                {options.map((opt, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border transition-all ${
                      opt.is_correct
                        ? "bg-teal-50/50 border-teal-300 ring-1 ring-teal-300/40"
                        : "bg-white border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="text-slate-300 cursor-grab" title="Reordenar">
                        <GripVertical className="w-3.5 h-3.5" />
                      </span>

                      <input
                        type="radio"
                        name="correct_option"
                        checked={opt.is_correct}
                        onChange={() => handleSetCorrectOption(idx)}
                        disabled={isTerminal}
                        className="w-4 h-4 text-teal-600 focus:ring-teal-500 cursor-pointer"
                        title="Marcar como respuesta correcta"
                      />

                      <span className="font-mono text-xs font-bold text-slate-400 w-5">
                        {String.fromCharCode(65 + idx)}.
                      </span>

                      <input
                        type="text"
                        value={opt.text}
                        onChange={(e) => handleOptionTextChange(idx, e.target.value)}
                        disabled={isTerminal}
                        placeholder={`Texto de la alternativa ${String.fromCharCode(65 + idx)}...`}
                        className="flex-1 text-xs sm:text-sm bg-transparent border-0 focus:outline-none text-slate-900 font-medium"
                      />

                      {opt.is_correct && (
                        <Badge className="bg-teal-600 hover:bg-teal-600 text-[10px] text-white">
                          Correcta
                        </Badge>
                      )}

                      {!isTerminal && options.length > 2 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveOption(idx)}
                          className="text-slate-400 hover:text-rose-600 p-1 rounded-md transition-colors"
                          title="Eliminar alternativa"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    {/* Misconception for distractors */}
                    {!opt.is_correct && (
                      <div className="mt-2 pl-9 pt-2 border-t border-slate-100 flex items-center gap-2">
                        <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <input
                          type="text"
                          value={opt.misconception_explanation || ""}
                          onChange={(e) => handleMisconceptionChange(idx, e.target.value)}
                          disabled={isTerminal}
                          placeholder="Anotación docente: error conceptual que evidencia este distractor (opcional)..."
                          className="w-full text-[11px] text-slate-600 placeholder:text-slate-400 bg-transparent border-0 focus:outline-none"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Metadatos Pedagógicos (KC, Bloom, Dificultad) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-2 border-t border-slate-100">
              {/* Knowledge Component */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1">
                  <Bookmark className="w-3.5 h-3.5 text-teal-600" />
                  <span>Concepto (KC)</span>
                </label>
                <select
                  value={selectedKcId}
                  onChange={(e) => setSelectedKcId(e.target.value)}
                  disabled={isTerminal}
                  className="w-full h-9 px-2.5 text-xs font-medium bg-white border border-slate-200 rounded-xl text-slate-800 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none"
                >
                  <option value="">-- Seleccionar KC --</option>
                  {knowledgeComponents.map((kc) => (
                    <option key={kc.id} value={kc.id}>
                      {kc.name}
                    </option>
                  ))}
                </select>
                {draft.suggested_kc_name && (
                  <p className="text-[10px] text-slate-400 truncate">
                    IA: &quot;{draft.suggested_kc_name}&quot;
                  </p>
                )}
              </div>

              {/* Taxonomía de Bloom */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700">
                  Taxonomía Bloom
                </label>
                <select
                  value={bloomTaxonomy}
                  onChange={(e) => setBloomTaxonomy(e.target.value)}
                  disabled={isTerminal}
                  className="w-full h-9 px-2.5 text-xs font-medium bg-white border border-slate-200 rounded-xl text-slate-800 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none"
                >
                  {BLOOM_LEVELS.map((bl) => (
                    <option key={bl.value} value={bl.value}>
                      {bl.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Dificultad */}
              <div className="space-y-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-700">
                  Dificultad ({difficulty.toFixed(2)})
                </label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(parseFloat(e.target.value))}
                  disabled={isTerminal}
                  className="w-full h-9 px-2.5 text-xs font-medium bg-white border border-slate-200 rounded-xl text-slate-800 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none"
                >
                  {DIFFICULTY_PRESETS.map((dp) => (
                    <option key={dp.value} value={dp.value}>
                      {dp.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Explicación y Justificación Pedagógica */}
            <div className="space-y-1.5 pt-1">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Feedback y Justificación Formativa de la Respuesta
              </label>
              <textarea
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                disabled={isTerminal}
                rows={2}
                placeholder="Fundamento formativo que se presentará al estudiante..."
                className="w-full text-xs p-3 border border-slate-200 rounded-xl text-slate-800 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none resize-none disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>
          </div>

          {/* =========================================================================
              RIGHT COLUMN (5 cols): Live Student Preview & Source Explorer (Capturas 17, 18, 19)
             ========================================================================= */}
          <div className="lg:col-span-5 bg-slate-50/70 p-5 sm:p-6 flex flex-col space-y-4 max-h-[calc(94vh-130px)] overflow-y-auto">
            {/* Tab switch buttons */}
            <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl shrink-0">
              <button
                type="button"
                onClick={() => setActiveRightTab("preview")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  activeRightTab === "preview"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Eye className="w-3.5 h-3.5 text-teal-600" />
                <span>Vista Estudiante</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveRightTab("source")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  activeRightTab === "source"
                    ? "bg-white text-slate-900 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5 text-amber-700" />
                <span>Explorar Fuente PDF</span>
              </button>
            </div>

            {/* TAB CONTENT A: Real-time Student Preview (Captura 17) */}
            {activeRightTab === "preview" && (
              <div className="flex-1 space-y-3.5 animate-in fade-in">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-semibold uppercase tracking-wider text-[10px]">
                    Simulación Interactiva
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] bg-teal-50 text-teal-800 font-bold px-2 py-0.5 rounded-full border border-teal-200">
                      KC: {selectedKcName}
                    </span>
                    <span className="text-[10px] bg-slate-100 text-slate-700 font-bold px-1.5 py-0.5 rounded border border-slate-200">
                      {difficulty.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Simulated Student Question Card */}
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 leading-snug">
                    {questionText || "Escribe el enunciado para previsualizarlo..."}
                  </h4>

                  <div className="space-y-2">
                    {options.map((opt, i) => {
                      const isSelected = previewSelectedOptionIndex === i;
                      return (
                        <div
                          key={i}
                          onClick={() => setPreviewSelectedOptionIndex(i)}
                          className={`text-xs p-3 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
                            isSelected
                              ? opt.is_correct
                                ? "bg-emerald-50 border-emerald-300 ring-1 ring-emerald-300 text-emerald-950 font-semibold"
                                : "bg-rose-50 border-rose-300 ring-1 ring-rose-300 text-rose-950"
                              : "bg-slate-50/80 border-slate-200 hover:bg-slate-100 text-slate-700"
                          }`}
                        >
                          <span className="w-4 h-4 rounded-full border border-slate-400 flex items-center justify-center shrink-0 text-[10px] font-bold">
                            {isSelected ? (opt.is_correct ? "✓" : "✗") : String.fromCharCode(65 + i)}
                          </span>
                          <span className="flex-1">{opt.text || `Alternativa ${String.fromCharCode(65 + i)}`}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Immediate Formative Feedback preview */}
                  {previewSelectedOptionIndex !== null && (
                    <div
                      className={`p-3 rounded-xl text-xs space-y-1 animate-in fade-in border ${
                        options[previewSelectedOptionIndex]?.is_correct
                          ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                          : "bg-amber-50 text-amber-900 border-amber-200"
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5">
                        {options[previewSelectedOptionIndex]?.is_correct ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>¡Respuesta Correcta!</span>
                          </>
                        ) : (
                          <>
                            <HelpCircle className="w-4 h-4 text-amber-700" />
                            <span>Observación Pedagógica:</span>
                          </>
                        )}
                      </div>
                      <p className="text-[11px] leading-relaxed">
                        {!options[previewSelectedOptionIndex]?.is_correct &&
                        options[previewSelectedOptionIndex]?.misconception_explanation
                          ? options[previewSelectedOptionIndex].misconception_explanation
                          : explanation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB CONTENT B: Document Source Explorer (Captura 18 & 19) */}
            {activeRightTab === "source" && (
              <div className="flex-1 space-y-3.5 animate-in fade-in">
                {/* Explorer Toolbar */}
                <div className="flex items-center justify-between text-xs bg-white p-2.5 rounded-xl border border-slate-200">
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setDocPage((p) => Math.max(1, p - 1))}
                      className="h-7 w-7 p-0 rounded-lg"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </Button>
                    <span className="text-[11px] font-bold text-slate-700">
                      {sourceRef?.type === "page" ? "Página" : "Diapositiva"} {docPage}
                    </span>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setDocPage((p) => p + 1)}
                      className="h-7 w-7 p-0 rounded-lg"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>

                  <div className="flex items-center gap-1.5 text-slate-500">
                    <button
                      type="button"
                      onClick={() => setDocZoom((z) => Math.max(80, z - 10))}
                      className="p-1 hover:text-slate-800 rounded"
                      title="Reducir zoom"
                    >
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-[11px] font-bold font-mono">{docZoom}%</span>
                    <button
                      type="button"
                      onClick={() => setDocZoom((z) => Math.min(150, z + 10))}
                      className="p-1 hover:text-slate-800 rounded"
                      title="Aumentar zoom"
                    >
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Rendered Document View (Captura 18 & 19) */}
                <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs space-y-3">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 border-b pb-2">
                    <span className="font-bold text-slate-700 truncate max-w-[200px]">
                      {draft.suggested_kc_name || "Material Curricular"}
                    </span>
                    <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-800 border-amber-300">
                      Evidencia Documental
                    </Badge>
                  </div>

                  {/* Document Page Simulation with Highlighted Excerpt */}
                  <div
                    style={{ transform: `scale(${docZoom / 100})`, transformOrigin: "top left" }}
                    className="p-3 bg-amber-50/20 rounded-xl border border-amber-200/50 space-y-2 text-xs transition-transform"
                  >
                    <p className="text-[11px] text-slate-400 italic">
                      Fragmento curricular extraído por el pipeline de generación:
                    </p>

                    {sourceRef?.snippet ? (
                      <blockquote className="p-3 bg-amber-100/70 border-l-4 border-amber-500 text-amber-950 font-serif text-xs rounded-r-lg leading-relaxed shadow-2xs">
                        &ldquo;{sourceRef.snippet}&rdquo;
                      </blockquote>
                    ) : (
                      <p className="text-slate-500 italic text-xs">
                        No se registraron citas textuales para este reactivo.
                      </p>
                    )}

                    <div className="pt-2 text-[10px] text-slate-400 flex items-center justify-between">
                      <span>Fundamento: {selectedKcName}</span>
                      <span>Índice: #{docPage}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer / Sequential Actions (Captura 19) */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div>
            {!isTerminal && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onReject(draft.id)}
                className="rounded-xl border-rose-200 text-rose-700 hover:bg-rose-50 hover:text-rose-800 text-xs font-semibold"
              >
                <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                Descartar reactivo
              </Button>
            )}
          </div>

          {/* Sequential Navigation (< 1 / N >) */}
          {onNavigate && currentIndex !== undefined && totalDrafts !== undefined && (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={currentIndex === 0}
                onClick={() => onNavigate("prev")}
                className="h-8 px-2.5 rounded-xl text-xs gap-1"
                title="Borrador anterior"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Anterior
              </Button>

              <span className="text-xs font-bold text-slate-600 px-1">
                {currentIndex + 1} / {totalDrafts}
              </span>

              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={currentIndex + 1 >= totalDrafts}
                onClick={() => onNavigate("next")}
                className="h-8 px-2.5 rounded-xl text-xs gap-1"
                title="Siguiente borrador"
              >
                Siguiente
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              className="rounded-xl text-xs"
            >
              Cerrar
            </Button>

            {!isTerminal && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleSaveDraft}
                  disabled={isSaving || isApproving}
                  className="rounded-xl text-xs gap-1.5 border-slate-300 font-semibold text-slate-700 hover:bg-slate-100"
                >
                  <Save className="w-3.5 h-3.5" />
                  {isSaving ? "Guardando..." : "Guardar cambios"}
                </Button>

                <Button
                  type="button"
                  size="sm"
                  onClick={handleApproveDraft}
                  disabled={isSaving || isApproving}
                  className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs gap-1.5 shadow-xs"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {isApproving ? "Publicando..." : "Aprobar y publicar en banco"}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
