import {
  StudentProfile,
  TeacherProfile,
  Course,
  RecommendedActivity,
  MicrocontentSection,
  QuizQuestion,
  StudentAnalytics,
  SystemStatusData,
} from "@/types/ui";

export const mockStudent: StudentProfile = {
  id: "std-001",
  name: "Lucía Mendoza",
  initials: "LM",
  grade: "5.° Secundaria",
  school: "Colegio Piloto San Agustín",
};

export const mockTeacher: TeacherProfile = {
  id: "tch-001",
  name: "Ana García",
  initials: "AG",
  roleTitle: "Docente de Ciencias",
};

export const mockCourses: Course[] = [
  {
    id: "course-ciencias",
    code: "CIEN-5SEC",
    title: "Ciencias",
    area: "Ciencias Naturales",
    description: "Biología, química y ambiente",
    grade: "5.° de secundaria",
    status: "active",
    unitsCount: 4,
    conceptsCount: 18,
    sectionsCount: 3,
    progressPercentage: 72,
    lastUpdated: "Hoy, 09:24",
  },
  {
    id: "course-ambiental",
    code: "AMB-5SEC",
    title: "Educación ambiental",
    area: "Ciencias Sociales y Ciudadanía",
    description: "Desarrollo sostenible y biodiversidad",
    grade: "5.° de secundaria",
    status: "draft",
    unitsCount: 0,
    conceptsCount: 0,
    sectionsCount: 0,
    progressPercentage: 0,
    lastUpdated: "16 may",
  },
];

export const mockRecommendedActivity: RecommendedActivity = {
  id: "rec-fotosintesis",
  courseId: "course-ciencias",
  courseTitle: "Ciencias",
  unitTitle: "Unidad 2",
  conceptTitle: "Fotosíntesis",
  title: "Un repaso breve para fortalecer la fotosíntesis",
  subtitle:
    "Esta actividad está diseñada para ayudarte a recuperar las ideas esenciales sin sobrecargarte.",
  whyRecommended:
    "En tu última actividad respondiste correctamente 3 de 5 preguntas. Un repaso ahora puede ayudarte a consolidar el concepto. Esta es una recomendación, no una certeza sobre tu aprendizaje.",
  estimatedMinutes: 8,
  steps: [
    {
      number: 1,
      title: "Microlección visual",
      description: "Conceptos fundamentales y proceso bioquímico",
      duration: "4 minutos",
      type: "lesson",
      route: "/learn/rec-fotosintesis",
    },
    {
      number: 2,
      title: "Recuperación breve",
      description: "Comprobación de retención activa",
      duration: "3 preguntas · 4 min",
      type: "quiz",
      route: "/quiz/rec-fotosintesis",
    },
  ],
};

export const mockMicrocontentSections: MicrocontentSection[] = [
  {
    id: 1,
    navTitle: "Idea principal",
    heading: "La fotosíntesis como base de la vida",
    tag: "FOTOSÍNTESIS",
    lead: "Las células vegetales convierten compuestos inorgánicos simples en moléculas energéticas ricas en enlaces de carbono.",
    durationMinutes: 2,
  },
  {
    id: 2,
    navTitle: "El proceso",
    heading: "La luz se transforma en alimento",
    tag: "FOTOSÍNTESIS",
    lead: "Las plantas capturan energía del sol y la usan para producir glucosa a partir de agua y dióxido de carbono.",
    durationMinutes: 4,
    formula: "6CO₂  +  6H₂O  —luz→  C₆H₁₂O₆  +  6O₂",
    analogy: {
      title: "Piensa en un panel solar natural",
      body: "Así como un panel captura luz para producir electricidad, la clorofila de las hojas captura luz para producir energía química almacenada en la glucosa.",
    },
    keyTakeaways: [
      {
        number: "01",
        text: "Ocurre principalmente en las hojas, dentro de los cloroplastos.",
      },
      {
        number: "02",
        text: "Necesita luz, agua y dióxido de carbono.",
      },
      {
        number: "03",
        text: "Produce glucosa y oxígeno.",
      },
    ],
  },
  {
    id: 3,
    navTitle: "Ejemplo",
    heading: "La hoja bajo el microscopio",
    tag: "ESTOMAS Y CLOROPLASTOS",
    lead: "A través de los estomas entra el dióxido de carbono y sale el oxígeno liberado a la atmósfera.",
    durationMinutes: 3,
  },
  {
    id: 4,
    navTitle: "Ideas clave",
    heading: "Síntesis para retención a largo plazo",
    tag: "CONSOLIDACIÓN",
    lead: "Comprender la diferencia entre fuente de materia y fuente de energía es la clave para dominar este concepto.",
    durationMinutes: 2,
  },
];

export const mockQuizQuestions: QuizQuestion[] = [
  {
    id: "q-1",
    questionNumber: 1,
    totalQuestions: 3,
    conceptTitle: "Fotosíntesis",
    prompt: "¿Cuál es la función principal de la luz solar durante la fotosíntesis?",
    scorePoints: 1,
    options: [
      {
        id: "opt-a",
        label: "A",
        text: "Calentar las hojas para que absorban más agua.",
      },
      {
        id: "opt-b",
        label: "B",
        text: "Proporcionar la energía necesaria para producir glucosa.",
      },
      {
        id: "opt-c",
        label: "C",
        text: "Convertir directamente el oxígeno en dióxido de carbono.",
      },
      {
        id: "opt-d",
        label: "D",
        text: "Transportar minerales desde las raíces hasta las hojas.",
      },
    ],
    correctOptionId: "opt-b",
    explanation:
      "La energía luminosa es capturada por la clorofila y transformada en energía química. Esa energía permite sintetizar glucosa, que la planta utiliza y almacena como alimento.",
    reminderNote: "Recuerda: la luz aporta energía; no se convierte en materia.",
  },
];

export const mockStudentAnalytics: StudentAnalytics = {
  completedActivities: 24,
  completedThisMonth: 6,
  observedAccuracy: 82,
  totalResponses: 68,
  consolidatedConcepts: 11,
  totalConcepts: 18,
  currentStreakDays: 6,
  bestStreakDays: 9,
  weeklyLearningMinutes: 42,
  weeklyDeltaPercentage: 12,
  reviewedConceptsCount: 12,
  weeklyTargetCount: 15,
  overallProgress: 78,
  evolutionData: [
    { date: "22 abr", accuracy: 22 },
    { date: "29 abr", accuracy: 38 },
    { date: "6 may", accuracy: 52 },
    { date: "13 may", accuracy: 50 },
    { date: "20 may", accuracy: 82 },
  ],
  conceptStatusBreakdown: [
    { status: "Consolidados", count: 11, color: "#0d9488" },
    { status: "En proceso", count: 5, color: "#6366f1" },
    { status: "Por iniciar", count: 2, color: "#cbd5e1" },
  ],
  history: [
    {
      id: "hist-1",
      concept: "Fotosíntesis",
      date: "Hoy, 10:15",
      observedResult: "3 de 3 (100%)",
      status: "Consolidado",
    },
    {
      id: "hist-2",
      concept: "Respiración celular",
      date: "Ayer, 16:40",
      observedResult: "4 de 5 (80%)",
      status: "En proceso",
    },
    {
      id: "hist-3",
      concept: "Mitosis y meiosis",
      date: "18 may",
      observedResult: "2 de 3 (66%)",
      status: "En proceso",
    },
    {
      id: "hist-4",
      concept: "Membrana celular y transporte",
      date: "15 may",
      observedResult: "5 de 5 (100%)",
      status: "Consolidado",
    },
  ],
};

export const mockSystemStatus: SystemStatusData = {
  apiStatus: "healthy",
  coldStartEstimatedSeconds: 0,
  activeModel: "DAS3H_Candidate",
  inferenceLatencyMs: 142,
  supabaseRlsStatus: "active_enforced",
  pseudonymizationStatus: "compliant_law_29733",
  lastHeartbeat: "Hace 12 segundos",
};
