"use client";

import React, { useState } from "react";
import {
  Users,
  Search,
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StudentRow {
  id: string;
  code: string;
  name: string;
  section: string;
  overallRetention: number;
  lastActive: string;
  completedActivities: number;
  suggestedAction: string;
}

const mockStudents: StudentRow[] = [
  {
    id: "std-1",
    code: "EST-501",
    name: "Lucía Mendoza (Seudónimo)",
    section: "5.° A",
    overallRetention: 84,
    lastActive: "Hoy, hace 2 horas",
    completedActivities: 18,
    suggestedAction: "Repaso de Fotosíntesis agendado",
  },
  {
    id: "std-2",
    code: "EST-502",
    name: "Mateo Quispe (Seudónimo)",
    section: "5.° A",
    overallRetention: 72,
    lastActive: "Ayer",
    completedActivities: 14,
    suggestedAction: "Refuerzo sugerido en Respiración",
  },
  {
    id: "std-3",
    code: "EST-503",
    name: "Valeria Castillo (Seudónimo)",
    section: "5.° A",
    overallRetention: 91,
    lastActive: "Hoy",
    completedActivities: 22,
    suggestedAction: "Progreso al día",
  },
  {
    id: "std-4",
    code: "EST-504",
    name: "Joaquín Flores (Seudónimo)",
    section: "5.° B",
    overallRetention: 65,
    lastActive: "Hace 3 días",
    completedActivities: 9,
    suggestedAction: "Momento ideal para repasar",
  },
  {
    id: "std-5",
    code: "EST-505",
    name: "Camila Rojas (Seudónimo)",
    section: "5.° B",
    overallRetention: 88,
    lastActive: "Ayer",
    completedActivities: 17,
    suggestedAction: "Progreso al día",
  },
];

export default function TeacherStudentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSection, setSelectedSection] = useState("all");
  const [generatedPinStudent, setGeneratedPinStudent] = useState<string | null>(null);
  const [tempPin, setTempPin] = useState<string | null>(null);

  const filteredStudents = mockStudents.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSection =
      selectedSection === "all" || s.section === selectedSection;
    return matchesSearch && matchesSection;
  });

  const handleGeneratePin = (studentCode: string) => {
    const randomPin = Math.floor(100000 + Math.random() * 900000).toString();
    setGeneratedPinStudent(studentCode);
    setTempPin(randomPin);
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">
            AULA & SECCIONES
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Estudiantes y Secciones
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Supervisión individual del ritmo de aprendizaje y probabilidad de retención esperada en 5.° de secundaria.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="text-teal-800 bg-teal-50 border-teal-200 py-1.5 px-3 text-xs gap-1.5 font-semibold"
          >
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            Ley N° 29733 · Datos seudonimizados
          </Badge>
        </div>
      </div>

      {/* OTP Generated PIN Alert */}
      {tempPin && generatedPinStudent && (
        <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-teal-600 text-white flex items-center justify-center flex-shrink-0">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-teal-900">
                PIN temporal de recuperación para {generatedPinStudent}:
              </p>
              <p className="font-mono text-xl font-extrabold text-teal-800 tracking-wider">
                {tempPin}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-teal-700">Válido por 15 minutos en el aula</span>
            <Button
              size="sm"
              variant="outline"
              className="text-xs rounded-xl"
              onClick={() => {
                setTempPin(null);
                setGeneratedPinStudent(null);
              }}
            >
              Cerrar
            </Button>
          </div>
        </div>
      )}

      {/* Filter and Section Selector */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por código o estudiante..."
            className="w-full h-11 pl-10 pr-4 text-xs sm:text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-600/30 text-slate-800 shadow-2xs"
          />
        </div>

        <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80 self-start sm:self-auto">
          {["all", "5.° A", "5.° B", "5.° C"].map((sec) => (
            <button
              key={sec}
              onClick={() => setSelectedSection(sec)}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                selectedSection === sec
                  ? "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {sec === "all" ? "Todas" : sec}
            </button>
          ))}
        </div>
      </div>

      {/* Students Table / Cards */}
      <div className="space-y-3">
        {filteredStudents.map((s) => (
          <Card
            key={s.id}
            className="rounded-2xl border-slate-200/80 p-5 shadow-xs bg-white hover:border-teal-300 transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  {s.code.replace("EST-", "")}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">{s.name}</h3>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {s.code}
                    </Badge>
                    <span className="text-xs text-slate-400 font-medium">{s.section}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {s.suggestedAction} · Última actividad: {s.lastActive}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100">
                <div className="text-right">
                  <p className="text-xs font-bold text-slate-900">
                    {s.overallRetention}% retención est.
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {s.completedActivities} microactividades
                  </p>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleGeneratePin(s.code)}
                  className="rounded-xl text-xs h-9 gap-1.5 border-slate-200 hover:border-teal-400 text-slate-700"
                  title="Generar PIN para recuperación de contraseña en el aula"
                >
                  <KeyRound className="w-3.5 h-3.5 text-teal-600" />
                  Generar PIN
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
