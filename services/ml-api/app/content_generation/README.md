# Módulo de Ingesta y Extracción Documental (Hito M2.1)

## 1. Identidad y Misión

El paquete `app.content_generation` implementa el motor de ingesta segura y extracción de texto estructurado para materiales curriculares de docentes (documentos PDF y presentaciones PPTX), almacenados en el bucket privado `teacher-materials` de Supabase Storage.

El objetivo pedagógico es recuperar estos materiales, extraer el texto preservando la procedencia exacta (número de página o diapositiva) y preparar los insumos para la generación asistida de preguntas de evaluación formativa (M2.2) y su posterior curaduría docente (Human-in-the-Loop, M2.3).

---

## 2. Aislamiento Arquitectónico Estricto

En estricto cumplimiento de **ADR-0004** y las reglas de arquitectura del proyecto:

1. **Aislamiento de Módulos Predictivos:**
   - Este módulo se encuentra 100% desacoplado de `app/prediction/` (modelos temporales DAS3H, PFA, BKT) y `app/adaptation/` (políticas de recomendación y fatiga cognitiva).
   - No compite con el hilo de inferencia en tiempo real para estudiantes.
2. **Sin Dependencias de Infraestructura Pesada:**
   - No se utiliza Redis, Celery ni RabbitMQ en esta fase.
   - El ciclo de procesamiento se coordina de manera determinista mediante estados en PostgreSQL (`content_generation_jobs`).
3. **Cero Dependencia de LLMs Externos en M2.1:**
   - No se conecta ninguna API externa (OpenAI, Gemini, Vertex, Anthropic).
   - No se envía ningún material a servicios de terceros.
   - No se utiliza OCR en esta fase.

---

## 3. Arquitectura del Módulo

```text
services/ml-api/app/content_generation/
├── __init__.py                     # Exportaciones públicas de la API de dominio
├── exceptions.py                   # Jerarquía de excepciones controladas y seguras
├── extractors/
│   ├── __init__.py
│   ├── base.py                     # BaseDocumentExtractor (ABC)
│   ├── pdf_extractor.py            # PdfDocumentExtractor (pypdf)
│   └── pptx_extractor.py           # PptxDocumentExtractor (python-pptx)
├── schemas/
│   ├── __init__.py
│   └── extracted_document.py       # Modelos Pydantic v2 (extra="forbid")
├── services/
│   ├── __init__.py
│   ├── extraction_service.py       # Orquestador DocumentExtractionService
│   └── document_validation.py      # Inspecciones criptográficas y defensas de seguridad
└── repositories/
    ├── __init__.py
    ├── job_repository.py           # Protocolo y repositorio en memoria con salvaguardas
    └── storage_client.py           # Protocolo y adaptadores de Supabase Storage
```

---

## 4. Extractores y Limitaciones Documentadas

### 4.1 Extractor PDF (`PdfDocumentExtractor`)
- **Librería base:** `pypdf >= 4.0.0`.
- **Procedencia:** Numera páginas de forma 1-indexada (`index=1, 2, ...`).
- **Seguridad y Cifrado:** Detecta documentos protegidos con contraseña mediante `reader.is_encrypted` y captura de `FileNotDecryptedError`, lanzando `EncryptedDocumentError` controlado sin causar HTTP 500.
- **Detección de Escaneo:** Si un documento no contiene texto extraíble digital (`total_text_length == 0`), lanza `NoExtractableTextError` reportando explícitamente en `details.requires_ocr = True` que se requiere OCR.
- **Defensa ante Volúmenes Excesivos:** Límite máximo configurable de 500 páginas (`MAX_PDF_PAGES`).

### 4.2 Extractor PPTX (`PptxDocumentExtractor`)
- **Librería base:** `python-pptx >= 0.6.23`.
- **Procedencia:** Preserva el orden secuencial de las diapositivas (`index=1, 2, ...`).
- **Extracción de Tablas:** Convierte estructuras tabulares a representación delimitada Markdown (`| Celda 1 | Celda 2 |`), normalizando saltos de línea y escapando caracteres de tubería (`\|`).
- **Aislamiento de Formas:** Si una forma o diagrama individual tiene un error de interpretación XML, se captura a nivel de forma (`warnings`) sin interrumpir la extracción del resto de diapositivas o formas.
- **Limitaciones Documentadas de PPTX:**
  - *Omitido por diseño en M2.1:* Notas del presentador (`notes_slide`), animaciones de transición, archivos multimedia embebidos (audio/video), y gráficos rasterizados sin texto OCR.
  - SmartArt complejos anidados se extraen como texto plano de sus marcos subordinados sin reproducir diagramas visuales.

---

## 5. Salvaguardas de Seguridad Documental

El archivo recibido se procesa bajo el principio de **contenido no confiable**:

1. **Límite de Tamaño:** Máximo 30 MB (`MAX_FILE_SIZE_BYTES = 31457280`).
2. **MIME y Extensión Declarada:** Solo se admiten `application/pdf` (`.pdf`) y `application/vnd.openxmlformats-officedocument.presentationml.presentation` (`.pptx`).
3. **Firma Binaria Real (Magic Bytes):**
   - PDF: Requiere encabezado `%PDF-`.
   - PPTX: Requiere encabezado ZIP (`PK\x03\x04`).
4. **Protección contra Zip Bombs en PPTX:**
   - Máximo tamaño descomprimido: 120 MB.
   - Máximo ratio de compresión: 30x.
   - Máximo número de entradas en archivo: 5000.
5. **Detección de Contenido Activo y Macros:**
   - Detección y rechazo de macros VBA (`vbaProject.bin`, `vbaData.xml`).
   - Rechazo de scripts o ejecutables embebidos (`.exe`, `.bat`, `.cmd`, `.sh`, `.vbs`, `.js`, `.ps1`, `.scr`, etc.).
6. **Aislamiento Multi-Tenant y Seguridad de Rutas:**
   - Bucket verificado: exclusivamente `teacher-materials`.
   - Detección de escapes de directorio (`..`, `\`).
   - Prohibición de caracteres nulos (`\0`) y barras consecutivas (`//`).
   - Rechazo terminante de URLs externas (`https://`, etc.).
   - Validación del prefijo de ruta contra `tenant_id`.
7. **Verificación de Permisos Docentes y Cursos:**
   - Se comprueba que el docente autenticado sea el creador del trabajo (`created_by == auth.uid()`).
   - Si el trabajo está vinculado a un curso (`course_id`), se valida la asignación académica del docente a dicho curso.
   - Estudiantes tienen denegado el acceso a la ingesta.

---

## 6. Propuesta Técnica de Persistencia para Resultados de Extracción

### 6.1 Análisis del Esquema Actual (`content_generation_jobs`)
La tabla `content_generation_jobs` creada en M1 contiene metadatos operativos (`id`, `tenant_id`, `course_id`, `storage_path`, `mime_type`, `file_checksum`, `status`, `provider`, `model_id`, etc.), pero **no contiene columnas para almacenar el texto extraído en crudo**.
Asimismo, las reglas arquitectónicas prohíben estrictamente almacenar documentos completos de 30 MB dentro de columnas destinadas a metadatos.

### 6.2 Propuesta Recomendada: Procesamiento Efímero en Memoria (Zero DDL)
- En el flujo end-to-end de M2.2, el trabajador toma el trabajo en estado `processing`, valida y extrae las unidades a memoria en el objeto `ExtractedDocument`.
- Dicho objeto se inyecta directamente al proveedor `QuestionGenerationProvider.generate_drafts(...)`.
- Los borradores resultantes se persisten en `question_drafts`, donde cada borrador almacena en su campo `source_references` el número de página/diapositiva y el extracto textual específico que sustenta la pregunta.
- **Ventaja:** Evita duplicar gigabytes de texto en la base de datos PostgreSQL, protege el límite de almacenamiento de 500 MB en la capa gratuita de Supabase y no requiere modificaciones DDL.

### 6.3 Alternativa para Auditoría Desacoplada: Objeto JSON en Supabase Storage
- Si la auditoría educativa o el desacoplamiento temporal entre extracción y generación con LLM requiere conservar el resultado de extracción completo:
- Guardar `ExtractedDocument.model_dump_json()` como un objeto estructurado en Supabase Storage bajo la ruta interna:
  `teacher-materials/<tenant_id>/extracted/<job_id>.json`.
- **Ventaja:** El almacenamiento de objetos maneja cargas pesadas de texto a costo mínimo, sin impactar las transacciones OLTP ni la memoria RAM de PostgreSQL.

### 6.4 Conclusión DDL
**No se requiere ninguna modificación al esquema relacional de PostgreSQL para el Hito M2.1.**
