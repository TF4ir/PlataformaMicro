# Plataforma de Microaprendizaje Adaptativo

> Sistema web de microaprendizaje adaptativo para modelar la dinámica de retención y olvido mediante predicción probabilística por componentes de conocimiento (Knowledge Components - KC) en estudiantes de 5to año de secundaria (16-17 años).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://python.org)
[![Next.js: 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![Supabase: PostgreSQL 15+](https://img.shields.io/badge/Supabase-PostgreSQL%2015+-3ECF8E.svg)](https://supabase.com)

---

## 1. Descripción y Arquitectura

La plataforma implementa una topología desacoplada y orientada a contratos para proporcionar microaprendizaje espaciado y adaptativo:

- **Capa de Presentación (`apps/web/`)**: Aplicación Next.js (App Router) con Server Components, Tailwind CSS, shadcn/ui y consumo tipado de APIs. *(En Fase 0 se mantiene estrictamente como andamiaje sin componentes de interfaz visual)*.
- **Capa de Persistencia e Identidad (`supabase/`)**: PostgreSQL 15+, Supabase Auth, Row Level Security (RLS) mandatorio al 100%, y almacén inmutable de eventos (`answer_events`).
- **Servicio Predictivo & Adaptativo (`services/ml-api/`)**: Microservicio FastAPI en Python 3.11+ para cálculo de secuencias temporales, inferencia probabilística DAS3H/baselines y políticas adaptativas con fallback de contingencia.
- **Espacio Científico y Experimentación (`ml/`)**: Entorno de investigación para EDA, ingeniería de características, entrenamiento offline, validación Student Group-K-Fold y calibración probabilística (ECE).
- **Contratos Compartidos (`packages/contracts/`)**: Especificación OpenAPI 3.1 JSON y tipado TypeScript unificado.
- **Gobernanza de Agentes (`.agents/`)**: Reglas, habilidades y flujos de trabajo de ejecución autónoma bajo Antigravity.

---

## 2. Estructura del Repositorio

```text
/
├── .agents/          # Reglas (rules/), habilidades (skills/) y flujos (workflows/)
├── apps/
│   └── web/          # Frontend Next.js (scaffolding de Fase 0)
├── docs/             # Documentación técnica, contratos, SRS y ADRs
├── ml/               # Experimentación, datasets seudonimizados y entrenamiento
├── packages/
│   └── contracts/    # Esquemas OpenAPI 3.1 y tipos compartidos
├── services/
│   └── ml-api/       # Microservicio FastAPI de inferencia y recomendación
├── supabase/         # Migraciones SQL, seed y configuración de persistencia
├── .env.example      # Plantilla de variables de entorno del monorepo
├── .gitignore        # Reglas de exclusión de git
├── AGENTS.md         # Constitución técnica principal de gobernanza
├── CONTRIBUTING.md   # Guía de contribución para desarrolladores y agentes
└── docker-compose.yml# Orquestación de contenedores locales
```

---

## 3. Requisitos Previos

- **Node.js**: v20.x o superior
- **pnpm**: v9.x o superior
- **Python**: v3.11 o superior (con `pip` o `poetry`)
- **Docker** y **Docker Compose**: versión compatible con Compose V2
- **Supabase CLI**: v1.140+ (opcional para desarrollo local)

---

## 4. Guía de Inicio Rápido (Local Development)

### 4.1 Configurar Variables de Entorno
```bash
cp .env.example .env
```
Revise y complete los valores requeridos en `.env` (credenciales locales de PostgreSQL y Supabase).

### 4.2 Iniciar Servicios Base con Docker Compose
```bash
docker compose up -d postgres ml-api
```
- PostgreSQL disponible en: `localhost:54322`
- API FastAPI disponible en: `http://localhost:8000/docs`

### 4.3 Ejecutar Verificación de Fase 0
Para verificar la integridad del andamiaje monorepo y la consistencia de contratos:
```bash
python scripts/verify-phase0.py
```

---

## 5. Gobernanza y Filosofía de Agentes

Este repositorio está instrumentado para el desarrollo asistido por agentes autónomos (Antigravity):
- **Constitución Raíz**: `AGENTS.md` define los límites inmutables, la pila técnica y las restricciones éticas.
- **Reglas Permanentes**: `.agents/rules/` contiene las políticas activas (`architecture.md`, `frontend.md`, `backend.md`, `database.md`, `machine-learning.md`, `research-integrity.md`) con `trigger: always_on`.
- **Límites de Fase 0**: Queda expresamente prohibido implementar componentes visuales o wireframes en `apps/web/` antes de concluir la Fase 0 de arquitectura y contratos formales.

---

## 6. Ética de Investigación y Protección de Menores

El proyecto atiende a estudiantes de educación secundaria en Perú y cumple con la **Ley de Protección de Datos Personales (Ley N° 29733)**:
- Prohibición estricta de registrar o exportar nombres, apellidos, correos o datos identificables en datasets o telemetría analítica.
- Uso obligatorio de identificadores seudonimizados (`student_id_pseudo`).
- Las pruebas cuasiexperimentales diferidas a 7 días están en cuarentena estricta y nunca se contaminan con repasos adaptativos.
