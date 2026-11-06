# Evidencias visuales — Demo local

Capturas tomadas el **2026-11-05** contra el stack local:

- Frontend Next.js: `http://127.0.0.1:3000`
- API FastAPI: `http://127.0.0.1:8000`
- Supabase local: PostgreSQL `54322`, Auth `54321`

Datos: `supabase/seed.sql` + `supabase/seed_demo.sql` (dataset sintético y
reproducible de 10 estudiantes seudonimizados). No corresponden a estudiantes
reales ni a métricas de un modelo predictivo entrenado.

| Archivo | Vista | Qué evidencia |
|---|---|---|
| `01-student-dashboard.png` | Dashboard estudiante | Saludo personalizado, repaso prioritario, métricas observadas y actividades |
| `02-student-progress.png` | Progreso estudiante | Precisión observada, desglose por KC e historial de intentos |
| `03-student-courses.png` | Cursos estudiante | Curso, unidades, KCs y actividades asignadas |
| `04-recommendations.png` | Recomendaciones | Repasos pendientes generados por la política de reglas |
| `05-teacher-dashboard.png` | Dashboard docente | 10 estudiantes, distribución por consolidación y alumnos que requieren refuerzo |
| `06-teacher-students.png` | Directorio docente | Roster con precisión y actividad reciente |
| `07-teacher-reports.png` | Reportes docentes | Heatmap 10×5, precisión por KC y trayectoria semanal observada (sin proyecciones inventadas) |
| `08-teacher-courses.png` | Cursos docente | Estructura curricular y actividades publicadas |

## Reproducir

```bash
supabase start                 # o supabase db reset
services/ml-api/.venv/bin/python scripts/seed_demo.py

# API
cd services/ml-api
DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:54322/postgres' \
SUPABASE_URL='http://127.0.0.1:54321' \
SUPABASE_JWT_SECRET='super-secret-jwt-token-with-at-least-32-characters-long' \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd apps/web
npm run dev                    # NEXT_PUBLIC_API_URL=http://localhost:8000
```

Cuentas: `lucia.mendoza@nexo.edu.pe` (estudiante) y `ana.garcia@nexo.edu.pe`
(docente), contraseña `Nexo2026!`.
