# Arquitectura de Seguridad, Gobernanza y Protección de Datos

## 1. Visión General de Seguridad

La **Plataforma de Microaprendizaje Adaptativo** implementa una arquitectura de seguridad por capas basada en el principio de **Defensa en Profundidad (*Defense-in-Depth*)** y **Privilegio Mínimo**.

Dado que los usuarios primarios son **menores de edad** (estudiantes de 5to año de secundaria, 16–17 años), el diseño incorpora salvaguardas técnicas y organizacionales alineadas con la **Ley N° 29733 (Ley de Protección de Datos Personales del Perú)** y estándares internacionales como **FERPA** y **GDPR**.

---

## 2. Matriz de Control de Acceso (RBAC y ABAC)

El sistema combina el control de acceso basado en roles (**RBAC**) con políticas basadas en atributos (**ABAC**) evaluadas en tiempo real mediante PostgreSQL Row Level Security (RLS) y dependencias de seguridad en FastAPI.

### 2.1 Definición de Roles del Sistema
- **`super_admin`:** Administrador técnico global de la infraestructura multitenant.
- **`admin`:** Administrador institucional de un colegio o red educativa específica (`tenant`).
- **`teacher`:** Docente titular asignado a secciones académicas específicas.
- **`student`:** Estudiante matriculado en una o más secciones.
- **`researcher`:** Investigador científico y evaluador de tesis (acceso exclusivamente a datos disociados y seudonimizados).
- **`service_role`:** Identidad de servicio interno autorizada para persistencia de inferencias y tareas batch.

### 2.2 Matriz de Operaciones por Entidad y Rol

| Entidad | Operación | `super_admin` | `admin` (Tenant) | `teacher` (Docente) | `student` (Alumno) | `researcher` | `service_role` (Backend) |
|---|---|---|---|---|---|---|---|
| `tenants` | SELECT | Todos | Propio | Propio | Propio | Solo activos | Todos |
| `tenants` | INSERT/UPDATE/DELETE | Full CRUD | Denegado | Denegado | Denegado | Denegado | Denegado |
| `profiles` | SELECT | Todos | Miembros Tenant | Alumnos Asignados | Propio únicamente | Seudonimizado | Todos |
| `profiles` | UPDATE | Full | Miembros Tenant | Denegado | Propio (avatar/nombre) | Denegado | Full |
| `courses` / `units` / `kc` | SELECT | Todos | Tenant | Tenant | Tenant | Tenant | Todos |
| `courses` / `units` / `kc` | INSERT/UPDATE/DELETE | Full | Tenant | Denegado | Denegado | Denegado | Full |
| `questions` / `options` | SELECT | Todos | Tenant | Tenant | Solo en intento activo | Tenant | Todos |
| `questions` / `options` | INSERT/UPDATE/DELETE | Full | Tenant | Autor de pregunta | Denegado | Denegado | Full |
| `activities` | SELECT | Todos | Tenant | Tenant | Asignadas | Tenant | Todos |
| `quiz_attempts` | SELECT | Todos | Tenant | Secciones a cargo | Propios únicamente | Seudonimizado | Todos |
| `quiz_attempts` | INSERT | Denegado | Denegado | Denegado | Propios únicamente | Denegado | Full |
| **`answer_events`** | **INSERT** | **Denegado** | **Denegado** | **Denegado** | **Propio únicamente** | **Denegado** | **Full (Inferencia)** |
| **`answer_events`** | **SELECT** | **Todos** | **Tenant** | **Alumnos Asignados**| **Propios únicamente**| **Solo `student_id_pseudo`** | **Todos** |
| **`answer_events`** | **UPDATE / DELETE** | **DENIED** | **DENIED** | **DENIED** | **DENIED** | **DENIED** | **DENIED** |
| `predictions` | SELECT | Todos | Tenant | Secciones a cargo | Propios únicamente | Seudonimizado | Todos |
| `predictions` | INSERT | Denegado | Denegado | Denegado | Denegado | Denegado | Full |
| `recommendations` | SELECT | Todos | Tenant | Secciones a cargo | Propios únicamente | Seudonimizado | Todos |
| `recommendations` | UPDATE (status) | Full | Tenant | Secciones a cargo | Propios (completar) | Denegado | Full |
| `review_assignments` | SELECT | Todos | Tenant | Secciones a cargo | Propios únicamente | Seudonimizado | Todos |

### 2.3 Condiciones de Evaluación ABAC (Row Level Security):
1. **Condición de Pertenencia Estudiantil:**
   ```sql
   student_id = (SELECT auth.uid()) AND tenant_id = (SELECT current_user_tenant_id())
   ```
2. **Condición de Titularidad Docente:**
   ```sql
   is_teacher_of_student(student_id) = true
   ```
   Verifica que exista al menos una sección activa donde el docente sea titular y el estudiante esté formalmente matriculado.
3. **Inmutabilidad Absoluta del Registro de Respuestas:**
   ```sql
   REVOKE UPDATE, DELETE ON answer_events FROM anon, authenticated;
   ```
   Ningún rol en la aplicación web, ni siquiera administradores de escuela, puede alterar marcas de tiempo, reactivos respondidos ni resultados observados.

---

## 3. Validación Criptográfica de JWT en FastAPI mediante JWKS

El microservicio de inferencia `services/ml-api/` no comparte bases de datos de usuarios ni depende de secretos simétricos compartidos para verificar sesiones. Emplea el estándar **JSON Web Key Set (JWKS)** expuesto por Supabase Auth (GoTrue).

```text
[Cliente Web (Next.js)]           [FastAPI (services/ml-api)]          [Supabase Auth]
         │                                     │                              │
         │ (1) Request con Bearer JWT          │                              │
         ├────────────────────────────────────>│                              │
         │                                     │ (2) Cache miss? Consulta JWKS│
         │                                     ├─────────────────────────────>│
         │                                     │<─────────────────────────────┤
         │                                     │     Retorna claves públicas  │
         │                                     │                              │
         │                                     │ (3) Valida firma (kid, RS256)│
         │                                     │ (4) Valida claims (aud, exp) │
         │                                     │ (5) Inyecta CurrentUser      │
         │                                     │                              │
         │ (6) Inferencia o Respuesta JSON     │                              │
         │<────────────────────────────────────┤                              │
```

### 3.1 Procedimiento de Verificación en Middleware:
1. **Extracción del Token:** Lee la cabecera HTTP `Authorization: Bearer <token>`. Si falta, retorna HTTP 401 con código RFC 7807 `MISSING_AUTHORIZATION_HEADER`.
2. **Descubrimiento y Caché de Llaves Públicas:**
   - Consulta el endpoint público `https://<supabase-host>/auth/v1/.well-known/jwks.json`.
   - Las llaves públicas RSA/ECDSA se almacenan en memoria con un TTL (*Time-to-Live*) de **24 horas**.
   - Ante la presencia de un `kid` desconocido en la cabecera del JWT, se realiza una invalidación anticipada de caché para admitir rotación automática de llaves.
3. **Verificación Criptográfica y Validación de Claims:**
   - Valida la firma digital empleando el algoritmo declarado (`RS256` o `ES256`).
   - Verifica que el claim de audiencia sea exactamente `aud == "authenticated"`.
   - Verifica que `exp > timestamp_actual_utc()` (rechazo estricto de tokens expirados).
   - Verifica el emisor institucional: `iss == "https://<supabase-host>/auth/v1"`.
4. **Construcción del Contexto de Seguridad:**
   - Extrae el claim `sub` (UUID del usuario en Supabase).
   - Extrae el rol (`user_role`) y el `tenant_id` contenidos en la metadata de la sesión.
   - Inyecta la entidad `AuthenticatedUser` en el contenedor de dependencias de FastAPI (`Depends(get_current_user)`).

---

## 4. Segregación de Secretos y Llaves Criptográficas

Para evitar filtraciones accidentales de credenciales con privilegios elevados, se impone una rigurosa **segregación de llaves por entorno y capa**:

### 4.1 Entorno Frontend (`apps/web/.env.local`):
- `NEXT_PUBLIC_SUPABASE_URL`: Dirección pública del API Gateway de Supabase.
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Llave pública anónima de cliente, con permisos restringidos exclusivamente a través de las políticas RLS.
- **PROHIBICIÓN ESTRICTA:** Queda terminantemente prohibido incluir la variable `SUPABASE_SERVICE_ROLE_KEY` en `apps/web/`, en paquetes de distribución cliente o en repositorios de control de versiones.

### 4.2 Entorno Backend Predictivo (`services/ml-api/.env`):
- `SUPABASE_URL`: URL interna o externa de la base de datos PostgreSQL.
- `SUPABASE_SERVICE_ROLE_KEY`: Llave privada de servicio, utilizada **única y exclusivamente** por procesos backend autorizados para persistir inferencias en segundo plano o ejecutar agregaciones de telemetría analítica.
- `APP_SECRET_KEY`: Llave simétrica de 256 bits para firma de tokens inter-servicio y comprobaciones de integridad.
- `ML_ARTIFACTS_DIR`: Ruta protegida en el sistema de archivos del contenedor para el alojamiento de artefactos congelados (`.joblib`).

---

## 5. Gobernanza Ética y Protección de Datos de Menores (Ley N° 29733 - Perú)

En concordancia con el marco regulatorio peruano sobre protección de datos personales de adolescentes y menores de edad en entornos educativos:

### 5.1 Disociación Permanente de Identidad (*Pseudonymization*):
1. **Generación de Token Disociado:** Al momento de la matrícula de un estudiante en una sección, la tabla `enrollments` genera de forma automática un UUID criptográfico independiente: `student_id_pseudo`.
2. **Aislamiento en Datasets de Machine Learning:**
   - Todos los datasets de entrenamiento (`ml/datasets/`), registros de características temporales y scripts de validación utilizan **exclusivamente** `student_id_pseudo`.
   - Queda prohibido exportar o almacenar nombres completos, apellidos, teléfonos, correos electrónicos o documentos de identidad en archivos CSV, datasets parquet, notebooks de investigación o registros de log.
3. **Auditoría de Exportaciones Analíticas:**
   - Las consultas SQL y vistas destinadas a la investigación de tesis solo proyectan campos anonimizados (`student_id_pseudo`, `kc_id`, `is_correct`, `response_time_seconds`).

### 5.2 Consentimiento Informado Institucional:
- Previo al inicio de las actividades escolares formativas, la institución educativa titular y los padres o apoderados legales formalizan la suscripción del **Formulario de Consentimiento Informado Institucional**, autorizando el procesamiento de la telemetría de interacción con fines exclusivamente pedagógicos y de mejora de la retención del aprendizaje.

---

## 6. Integridad Científica y Cuarentena de Reactivos de Evaluación a 7 Días

Para garantizar la validez científica del diseño experimental cuasiexperimental de la investigación de tesis:

### 6.1 Problema de Contaminación del Instrumento (*Testing Effect Leakage*):
La evaluación diferida aplicada a los **7 días** de la sesión inicial constituye el instrumento formal de medición de la retención a largo plazo. Si los reactivos de dicha evaluación fueran presentados como material de micro-repaso adaptativo durante la semana de intervención, la variable dependiente de la investigación quedaría contaminada por efecto de exposición previa.

### 6.2 Regla de Aislamiento y Cuarentena Inmutable:
- **Cuarentena Estricta del Banco de Preguntas:** Todas las preguntas asociadas a actividades con `activity_type = 'delayed_assessment'` quedan **estrictamente en cuarentena**:
  ```sql
  -- Restricción obligatoria en consultas de la política adaptativa:
  WHERE a.activity_type != 'delayed_assessment'
  ```
- **Validación en el Motor de Recomendación:** El servicio `AdaptationPolicy` verifica programáticamente que ningún reactivo ni microcontenido vinculado a la evaluación diferida sea seleccionado para tareas de repaso `practice`.

### 6.3 Registro de Decisiones Pedagógicas (*Algorithmic Audit Trail*):
Cada recomendación adaptativa generada persiste en la tabla `recommendations`:
- `selection_method`: Identifica si la decisión provino de inferencia predictiva (`predictive_model`), regla de contingencia (`rule_based_fallback`) o asignación docente (`teacher_assigned`).
- `decision_reason`: Explicación textual transparente que justifica por qué se programó el microcontenido.
- `prediction_id`: Enlace auditable a la estimación probabilística de riesgo de olvido que motivó la intervención.
