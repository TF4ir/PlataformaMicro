# Documentación de Telemetría de Exposición de Microcontenido (M5.2-B)

**Proyecto:** PlataformaMicro — Sistema Web de Microaprendizaje Adaptativo (5to Secundaria)  
**Módulo:** Content Exposure & Study Telemetry  
**Fecha:** Noviembre 2026  
**Migración:** [`supabase/migrations/20261103040000_content_exposure_events_m52.sql`](file:///root/PlataformaMicro/supabase/migrations/20261103040000_content_exposure_events_m52.sql)  

---

## 1. Contrato del Evento: `ContentExposureEvent`

El contrato tipado reside en [`ml/src/contracts/exposure_contract.py`](file:///root/PlataformaMicro/ml/src/contracts/exposure_contract.py#L30-L73) y modela la adquisición y repaso de conocimiento mediante microcontenido:

```python
class ContentExposureEvent(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    student_id_pseudo: uuid.UUID
    microcontent_id: uuid.UUID
    knowledge_component_id: uuid.UUID
    exposure_type: ExposureType  # initial_study, review_study, remedial_reading, diagnostic_exposure
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float
    active_reading_seconds: float | None
    completion_status: ExposureCompletionStatus  # completed, partial, abandoned
    session_id: uuid.UUID
    idempotency_key: uuid.UUID
    metadata: dict[str, Any]
```

---

## 2. Modelo Entidad-Relación

```
tenants (id)
  └── content_exposure_events (tenant_id)
        ├── profiles (student_id)
        ├── microcontents (microcontent_id)
        └── knowledge_components (knowledge_component_id)
```

---

## 3. Especificación de Persistencia SQL

La tabla `content_exposure_events` almacena cada sesión de lectura o visualización de microcontenido con blindaje append-only:

```sql
CREATE TABLE IF NOT EXISTS content_exposure_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    student_id_pseudo UUID NOT NULL,
    microcontent_id UUID NOT NULL REFERENCES microcontents(id) ON DELETE RESTRICT,
    knowledge_component_id UUID NOT NULL REFERENCES knowledge_components(id) ON DELETE RESTRICT,
    exposure_type exposure_type_enum NOT NULL DEFAULT 'initial_study',
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(8, 2) NOT NULL DEFAULT 0.0 CHECK (duration_seconds >= 0.0),
    active_reading_seconds NUMERIC(8, 2) CHECK (active_reading_seconds IS NULL OR active_reading_seconds >= 0.0),
    completion_status exposure_completion_status_enum NOT NULL DEFAULT 'completed',
    session_id UUID NOT NULL,
    idempotency_key UUID UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_exposure_completed_at CHECK (completed_at IS NULL OR completed_at >= started_at)
);
```

---

## 4. Políticas de Seguridad (RLS) y Privilegio Mínimo

1. **Denegación de Modificación:** Se revocaron explícitamente `UPDATE`, `DELETE` y `TRUNCATE`. Los triggers `trg_prevent_content_exposure_mutation` y `trg_prevent_content_exposure_truncate` lanzan la excepción `ERRCODE 55000` ante cualquier intento de alteración o eliminación.
2. **Aislamiento Estudiantil:**
   - La política `content_exposure_events_insert` restringe la inserción exclusivamente al usuario autenticado (`student_id = auth.uid()`).
   - La política `content_exposure_events_select` permite lectura al alumno de sus propios registros, al docente de su sección asignada (vía `is_teacher_of_student`), o al administrador.

---

## 5. Estrategia de Idempotencia y Sesión

- `idempotency_key` con índice único garantiza que reintentos de red desde el cliente no dupliquen lecturas.
- `session_id` agrupa lecturas fragmentadas o eventos de *heartbeat* vinculados a la misma sesión del navegador.
- `duration_seconds` registra el tiempo transcurrido, mientras que `active_reading_seconds` captura el tiempo efectivo con foco en la pestaña.

---

## 6. Pruebas de Integración y Verificación

Las pruebas automatizadas en [`services/ml-api/tests/test_content_exposure_m52.py`](file:///root/PlataformaMicro/services/ml-api/tests/test_content_exposure_m52.py) certifican:
1. Inserción correcta de eventos con validación de tipos y rangos.
2. Bloqueo de `UPDATE` y `DELETE` por trigger con código `55000`.
3. Rechazo de claves de idempotencia duplicadas (`UniqueViolationError`).
4. Rechazo de fechas incoherentes (`completed_at < started_at`) mediante `chk_exposure_completed_at`.
5. Unión cronológica con `answer_events` para reconstruir la secuencia completa de aprendizaje.

---

## 7. Procedimiento de Despliegue a Producción

1. **Respaldo previo:** Ejecutar `pg_dump -Fc` de la base de datos de destino.
2. **Aplicación DDL:**
   ```bash
   psql "$PROD_DATABASE_URL" -f supabase/migrations/20261103040000_content_exposure_events_m52.sql
   ```
3. **Verificación post-migración:**
   ```sql
   SELECT count(*) FROM content_exposure_events;
   ```
