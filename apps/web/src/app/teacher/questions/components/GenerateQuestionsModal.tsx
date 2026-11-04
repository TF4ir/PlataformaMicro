"use client";

import React, { useState, useRef } from "react";
import {
  X,
  UploadCloud,
  FileText,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Layers,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CourseItem,
  contentGenerationApi,
} from "@/lib/api/content-generation";

interface GenerateQuestionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  courses: CourseItem[];
  selectedCourseId: string;
  onJobCreated: (jobId: string) => void;
}

export function GenerateQuestionsModal({
  isOpen,
  onClose,
  courses,
  selectedCourseId,
  onJobCreated,
}: GenerateQuestionsModalProps) {
  const [courseId, setCourseId] = useState<string>(selectedCourseId || (courses[0]?.id || ""));
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [targetCount, setTargetCount] = useState<number>(5);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "pptx"].includes(ext || "")) {
        setErrorMessage("Formato no compatible. Por favor sube un documento PDF o presentación PPTX.");
        setSelectedFile(null);
        return;
      }
      if (file.size > 30 * 1024 * 1024) {
        setErrorMessage("El archivo excede el tamaño máximo permitido de 30 MB.");
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setErrorMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!["pdf", "pptx"].includes(ext || "")) {
        setErrorMessage("Solo se admiten documentos PDF o presentaciones PPTX.");
        return;
      }
      if (file.size > 30 * 1024 * 1024) {
        setErrorMessage("El archivo excede el tamaño máximo de 30 MB.");
        return;
      }
      setSelectedFile(file);
      setErrorMessage(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Por favor selecciona un material curricular PDF o PPTX.");
      return;
    }
    if (!courseId) {
      setErrorMessage("Por favor selecciona un curso para vincular el trabajo.");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);

    try {
      // 1. Upload material to secure storage
      const uploadRes = await contentGenerationApi.uploadMaterial(selectedFile, courseId);

      // 2. Create generation job
      const job = await contentGenerationApi.createGenerationJob({
        storage_path: uploadRes.storage_path,
        storage_bucket: uploadRes.storage_bucket,
        original_filename: uploadRes.original_filename,
        mime_type: uploadRes.mime_type,
        file_size_bytes: uploadRes.file_size_bytes,
        file_checksum: uploadRes.file_checksum,
        course_id: courseId,
        target_question_count: targetCount,
      });

      setSuccessMessage("¡Trabajo de generación encolado con éxito!");
      setTimeout(() => {
        onJobCreated(job.job_id);
        onClose();
      }, 1000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al crear el trabajo de generación.";
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-lg">
                Generar preguntas con IA
              </h3>
              <p className="text-xs text-slate-500">
                Sube tu material de clase para extraer borradores calibrados.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {errorMessage && (
          <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs font-medium">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Course Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Curso Académico
            </label>
            <select
              value={courseId}
              onChange={(e) => setCourseId(e.target.value)}
              className="w-full h-11 px-3 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl text-slate-800 focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 focus:outline-none"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.code})
                </option>
              ))}
            </select>
          </div>

          {/* File Upload Area */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Material Curricular (PDF o PPTX, máx. 30 MB)
            </label>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                selectedFile
                  ? "border-teal-500 bg-teal-50/30"
                  : "border-slate-200 hover:border-teal-400 hover:bg-slate-50/50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
                onChange={handleFileChange}
                className="hidden"
              />

              {selectedFile ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <p className="text-xs sm:text-sm font-bold text-slate-900 truncate max-w-xs">
                      {selectedFile.name}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Clic para cambiar
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs sm:text-sm font-semibold text-slate-800">
                      Arrastra y suelta tu archivo aquí, o{" "}
                      <span className="text-teal-700 underline font-bold">explora tus carpetas</span>
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Guías de aprendizaje, diapositivas de clase o lecturas temáticas
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Question Count Slider/Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Cantidad de preguntas a generar
              </label>
              <span className="font-bold text-teal-700 text-sm">{targetCount} reactivos</span>
            </div>
            <input
              type="range"
              min={3}
              max={10}
              value={targetCount}
              onChange={(e) => setTargetCount(parseInt(e.target.value))}
              className="w-full accent-teal-600 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>3 preguntas</span>
              <span>5 (recomendado)</span>
              <span>10 preguntas</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isUploading}
              className="rounded-xl text-xs"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={isUploading || !selectedFile}
              className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl text-xs gap-1.5 shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isUploading ? "Cargando y procesando..." : "Comenzar generación"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
