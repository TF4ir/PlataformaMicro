"use client";

import React, { useState } from "react";
import {
  FileQuestion,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  MoreVertical,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface QuestionItem {
  id: string;
  code: string;
  prompt: string;
  kcName: string;
  kcTag: string;
  difficulty: "Básica" | "Intermedia" | "Avanzada";
  bloomLevel: string;
  accuracyRate: number;
  totalAttempts: number;
}

const mockQuestions: QuestionItem[] = [
  {
    id: "q-001",
    code: "PREG-BIO-01",
    prompt: "¿Cuál es la función principal de la clorofila en la fase luminosa de la fotosíntesis?",
    kcName: "Fase Luminosa y Pigmentos",
    kcTag: "Fotosíntesis",
    difficulty: "Intermedia",
    bloomLevel: "Comprensión",
    accuracyRate: 78,
    totalAttempts: 142,
  },
  {
    id: "q-002",
    code: "PREG-BIO-02",
    prompt: "¿En qué estructura del cloroplasto ocurre la síntesis de glucosa durante el Ciclo de Calvin?",
    kcName: "Ciclo de Calvin y Fijación de CO2",
    kcTag: "Fotosíntesis",
    difficulty: "Avanzada",
    bloomLevel: "Análisis",
    accuracyRate: 61,
    totalAttempts: 129,
  },
  {
    id: "q-003",
    code: "PREG-BIO-03",
    prompt: "¿Qué molécula actúa como aceptor final de electrones en la fosforilación oxidativa mitocondrial?",
    kcName: "Cadena de Transporte Electrónico",
    kcTag: "Respiración Celular",
    difficulty: "Avanzada",
    bloomLevel: "Comprensión",
    accuracyRate: 54,
    totalAttempts: 110,
  },
  {
    id: "q-004",
    code: "PREG-BIO-04",
    prompt: "¿Cuál es el balance neto de moléculas de ATP producidas directamente por molécula de glucosa en la glucólisis?",
    kcName: "Glucólisis Anaeróbica",
    kcTag: "Metabolismo",
    difficulty: "Básica",
    bloomLevel: "Recuerdo",
    accuracyRate: 88,
    totalAttempts: 165,
  },
  {
    id: "q-005",
    code: "PREG-BIO-05",
    prompt: "Durante la respiración celular anaeróbica en levaduras, ¿cuáles son los productos terminales?",
    kcName: "Fermentación Alcohólica",
    kcTag: "Respiración Celular",
    difficulty: "Básica",
    bloomLevel: "Comprensión",
    accuracyRate: 82,
    totalAttempts: 138,
  },
];

export default function TeacherQuestionsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [kcFilter, setKcFilter] = useState("all");

  const filteredQuestions = mockQuestions.filter((q) => {
    const matchesSearch =
      q.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.kcName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesKc = kcFilter === "all" || q.kcTag === kcFilter;
    return matchesSearch && matchesKc;
  });

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-[#0A635F]">
            BANCO ADAPTATIVO
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Banco de preguntas
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Reactivos formativos calibrados para modelado de retención por Componentes de Conocimiento (KC).
          </p>
        </div>

        <div>
          <Button
            size="lg"
            className="bg-[#0A635F] hover:bg-[#0B2D34] text-white font-semibold rounded-xl gap-2 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            Nueva pregunta
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por enunciado, código o componente de conocimiento..."
            className="w-full h-11 pl-10 pr-4 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 focus:border-teal-600 transition-all text-slate-800 placeholder:text-slate-400 shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={kcFilter}
            onChange={(e) => setKcFilter(e.target.value)}
            className="h-11 px-3 text-xs font-semibold bg-white border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-600/30 w-full sm:w-auto shadow-2xs"
          >
            <option value="all">Todos los conceptos</option>
            <option value="Fotosíntesis">Fotosíntesis</option>
            <option value="Respiración Celular">Respiración Celular</option>
            <option value="Metabolismo">Metabolismo</option>
          </select>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-3">
        {filteredQuestions.map((q) => (
          <Card
            key={q.id}
            className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white hover:border-teal-300 hover:shadow-sm transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-2 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                    {q.code}
                  </span>
                  <Badge
                    variant="outline"
                    className="text-[10px] font-semibold text-teal-800 bg-teal-50 border-teal-200"
                  >
                    KC: {q.kcTag}
                  </Badge>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      q.difficulty === "Básica"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : q.difficulty === "Intermedia"
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-rose-50 text-rose-700 border border-rose-200"
                    }`}
                  >
                    {q.difficulty}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Nivel: {q.bloomLevel}
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  {q.prompt}
                </h3>

                <p className="text-xs text-slate-500">
                  Componente de Conocimiento específico: <span className="font-medium text-slate-700">{q.kcName}</span>
                </p>
              </div>

              {/* Stats & Actions */}
              <div className="flex items-center gap-6 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-900">
                    {q.accuracyRate}% aciertos
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {q.totalAttempts} intentos observados
                  </p>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-xl text-xs h-9 border-slate-200 hover:bg-slate-50"
                >
                  Editar
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
