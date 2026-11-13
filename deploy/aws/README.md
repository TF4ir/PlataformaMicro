# AWS Lambda Deployment & Hardening — PlataformaMicro ML-API

Este documento describe la arquitectura, controles de seguridad, configuración y procedimiento de despliegue endurecido (hardening) del microservicio FastAPI `services/ml-api` en **AWS Lambda** con **AWS Lambda Web Adapter 1.1.0** y **Amazon ECR**.

```
deploy/aws/
├── ecr.yaml              # Repositorio ECR, scan-on-push, cifrado AES256, ciclo de vida
├── template.yaml         # Stack SAM: Lambda, Function URL, Secrets Manager, CORS, IAM
├── build_and_push.sh     # Script compilación linux/amd64 (single-arch) y push a ECR (us-east-2)
└── README.md             # Especificación técnica, gobernanza, matriz IAM y guía operativa
```

---

## 1. Convención de Nombres y CAPABILITY_NAMED_IAM

Para evitar colisiones, nombres duplicados o concatenaciones redundantes (`nexo-mvp-ml-api-ml-api` o `nexo-mvp-ml-api-ml-api-role`), se establece una convención estricta:

| Recurso | Identificador / Formato Convencional | Referencia en Template |
|---|---|---|
| **CloudFormation Stack** | `nexo-mvp-ml-api` | `--stack-name nexo-mvp-ml-api` |
| **Función Lambda** | `nexo-mvp-ml-api` | `FunctionName: !Ref AWS::StackName` |
| **Log Group CloudWatch** | `/aws/lambda/nexo-mvp-ml-api` | `LogGroupName: !Sub "/aws/lambda/${AWS::StackName}"` |
| **Lambda Execution Role** | `nexo-mvp-ml-api-role` | `RoleName: !Sub "${AWS::StackName}-role"` |
| **CloudFormation Execution Role** | `nexo-mvp-cloudformation-role` | `--role-arn arn:aws:iam::716174523077:role/nexo-mvp-cloudformation-role` |
| **Database Secret** | `nexo-mvp-database-dsn` | Nombre del recurso en Secrets Manager |
| **Repositorio ECR** | `nexo-mvp-ml-api` | Creado por `deploy/aws/ecr.yaml` |

### Justificación de CAPABILITY_NAMED_IAM
En AWS CloudFormation, cuando una plantilla declara un recurso de tipo `AWS::IAM::Role` con una propiedad `RoleName` explícita (en lugar de delegar el nombrado aleatorio al motor de CloudFormation), AWS exige de manera obligatoria la capacidad **`CAPABILITY_NAMED_IAM`**.

Si se proporciona únicamente `CAPABILITY_IAM`, CloudFormation rechaza el despliegue con:
```
Requires capabilities : [CAPABILITY_NAMED_IAM]
```
Por tanto, todas las instrucciones de despliegue (`sam deploy`) para `deploy/aws/template.yaml` especifican explícitamente `--capabilities CAPABILITY_NAMED_IAM`.

---

## 2. Gestión Segura de Secretos y Supabase Pooler

### Integración con AWS Secrets Manager
1. El parámetro `DatabaseSecretArn` en `template.yaml` especifica el ARN del secreto en Secrets Manager.
2. Durante el arranque en frío (lifespan de FastAPI), `app.core.secrets.get_database_dsn()` recupera el valor del secreto utilizando `boto3.client('secretsmanager')`.
3. El secreto admite formato JSON (`{"DATABASE_URL": "..."}` o campos individuales `username`, `password`, `host`, `port`, `dbname`) o una cadena directa `postgresql://...`.
4. El DSN resuelto se mantiene en memoria (`_CACHED_DATABASE_DSN`).
5. **Máscara de Seguridad:** Toda traza de log utiliza `mask_database_dsn()`, sustituyendo contraseñas por `***` (cero fugas de credenciales en CloudWatch Logs).
6. **Invalidación y Recarga de Caché:** El módulo expone `invalidate_cached_dsn()`. Si ocurre un error de autenticación PostgreSQL (`asyncpg.InvalidPasswordError` o `asyncpg.InvalidAuthorizationSpecificationError`), la capa de conexión en `database.py` descarta automáticamente el DSN en memoria para que el siguiente intento de conexión solicite el secreto fresco desde Secrets Manager (habilitando rotación de credenciales sin reiniciar el contenedor).

### Procedimiento Seguro de Creación del Secreto

> [!CAUTION] **Seguridad de Procesos en Linux:**
> Nunca pase el DSN directamente como argumento de línea de comandos en `--secret-string "{\"DATABASE_URL\":\"...\"}"`. Aunque se utilice `read -s` para evitar el eco en terminal, los argumentos de ejecución de cualquier comando son visibles para otros procesos del sistema operativo a través de `/proc/$PID/cmdline` o mediante utilidades como `ps aux`.

#### Método A (Recomendado): Consola Web de AWS
1. Inicie sesión en la consola de AWS con una identidad autorizada y navegue a **AWS Secrets Manager** en la región `us-east-2`.
2. Haga clic en **Store a new secret**.
3. Seleccione **Other type of secret**.
4. En **Key/value pairs**, añada la clave `DATABASE_URL` y pegue la cadena del Supabase Transaction Pooler (obtenida de *Connect → Transaction pooler*).
5. Asigne el nombre de secreto: `nexo-mvp-database-dsn`.
6. Finalice la creación y copie el **Secret ARN** completo (e.g. `arn:aws:secretsmanager:us-east-2:716174523077:secret:nexo-mvp-database-dsn-aBcDeF`).

#### Método B (CLI Seguro vía STDIN / Sin Exposición de Procesos)
Si se requiere utilizar AWS CLI, pase el secreto directamente a través de `stdin` (`file:///dev/stdin`) para que el DSN jamás viaje en los argumentos del proceso:

```bash
# 1. Crear el secreto leyendo el payload JSON desde stdin
aws secretsmanager create-secret \
  --name nexo-mvp-database-dsn \
  --description "DSN de Supabase Transaction Pooler para PlataformaMicro ML-API" \
  --secret-string file:///dev/stdin \
  --region us-east-2 \
  --profile platmicro << 'EOF'
{"DATABASE_URL":"postgresql://postgres.oqjahhbqcethwgpufgnm:TU_PASSWORD_AQUI@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"}
EOF

# 2. Obtener el ARN COMPLETO generado por AWS (con sufijo aleatorio oficial)
REAL_SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id nexo-mvp-database-dsn \
  --region us-east-2 \
  --profile platmicro \
  --query "ARN" \
  --output text)

echo "ARN oficial generado por AWS: ${REAL_SECRET_ARN}"
# Ejemplo de ARN real:
# arn:aws:secretsmanager:us-east-2:716174523077:secret:nexo-mvp-database-dsn-aBcDeF
```

> **ADVERTENCIA CRÍTICA:** Jamás construya manualmente el ARN del secreto asumiendo que termina en `-dsn`. AWS Secrets Manager siempre añade un sufijo aleatorio de 6 caracteres al ARN canónico. Utilice exactamente el valor retornado por `describe-secret` para el parámetro `DatabaseSecretArn`.

### Lista de Comprobación: Conexión Supabase Transaction Pooler
No asuma que el host del pooler puede inferirse por la región AWS. La cadena de conexión debe obtenerse directamente del panel de Supabase:
**Project Settings → Database → Connection Pooling / Connect → Transaction pooler**.

Verificar rigurosamente cada componente:
- [x] **Usuario:** `postgres.[PROJECT-REF]` (ejemplo: `postgres.oqjahhbqcethwgpufgnm`).
- [x] **Host exacto:** Host indicado en la consola de Supabase (ejemplo: `aws-0-us-east-2.pooler.supabase.com` u otro asignado por Supavisor).
- [x] **Puerto:** `6543` (Modo Transacción / Supavisor). No usar puerto `5432` en Lambda para evitar saturar conexiones de sesión.
- [x] **Cifrado TLS:** `sslmode=require` (obligatorio para asyncpg remoto hacia Supabase).
- [x] **Percent-encoding de caracteres especiales:** Si la contraseña contiene caracteres como `#`, `!`, `@`, `$`, `%`, `&`, `?`, deben estar codificados en percent-encoding (ej. `#` -> `%23`, `@` -> `%40`).
- [x] **statement_cache_size=0:** Obligatorio en Transaction Mode (`DB_STATEMENT_CACHE_SIZE=0`) para prevenir `DuplicatePreparedStatementError` cuando Supavisor multiplexa consultas entre múltiples backends Postgres.

---

## 3. Seguridad de Function URL, Autenticación y CORS

### Configuración CORS de Function URL (AllowCredentials=false)
- La Lambda Function URL es la **única responsable de CORS en producción**.
- En Lambda, `ENABLE_CORS_MIDDLEWARE="false"` desactiva el `CORSMiddleware` interno de FastAPI para prevenir cabeceras `Access-Control-Allow-Origin` duplicadas.
- **Configuración en template.yaml:**
  ```yaml
  FunctionUrlConfig:
    AuthType: NONE
    Cors:
      AllowOrigins:
        - https://plataformamicro.fabriziovalerio-c.workers.dev
      AllowCredentials: false
      AllowMethods:
        - GET
        - POST
        - PUT
        - PATCH
        - DELETE
        - HEAD
      AllowHeaders:
        - authorization
        - content-type
        - x-idempotency-key
        - x-request-id
      MaxAge: 86400
  ```
- **AllowCredentials=false:** Nuestra arquitectura autentica exclusivamente mediante tokens `Authorization: Bearer <JWT>` transmitidos en cabeceras HTTP sin cookies de sesión. Establecer `AllowCredentials: false` es la práctica más segura y conforme a las especificaciones CORS para APIs token-based.

### Validación de Autenticación y Rutas Reales
- **Ruta pública:** `GET /api/v1/health` responde `200 OK` sin requerir credenciales (usada por health checks y readiness probes del AWS Lambda Web Adapter).
- **Ruta de retención:** `GET /api/v1/students/me/retention`
  - Sin token: responde `401 Unauthorized`.
  - Con token de estudiante válido: responde `200 OK` con el perfil de retención probabilístico.
- **Aislamiento de roles docente/alumno:**
  - Si un estudiante intenta acceder a rutas docentes (`GET /api/v1/content-generation/courses`, `POST /api/v1/content-generation/upload-material`, `GET /api/v1/content-generation/questions`), recibe inmediatamente `403 Forbidden` (`INSUFFICIENT_PERMISSIONS`).
- **Peticiones Preflight (OPTIONS):** La Function URL intercepta y resuelve peticiones `OPTIONS` antes de invocar el contenedor. En desarrollo local, FastAPI resuelve `OPTIONS` con cabeceras CORS autorizadas.

---

## 4. Gestión de Documentos y Supabase Storage Direct Upload

### Restricción de 6 MB en AWS Lambda
En modo síncrono/buffered, AWS Lambda y Function URL imponen un límite ineludible de **6 MB** en el payload de la petición HTTP. Cargar archivos de clase (PDFs o PPTXs de 10 a 30 MB) a través de Lambda provoca errores `413 Request Entity Too Large` o timeouts de transferencia.

### Arquitectura de Carga Directa
1. **Frontend (`apps/web`):**
   - Para archivos de material docente (> 6 MB o flujo canónico), el cliente sube el archivo **directamente a Supabase Storage** en el bucket privado `teacher-materials` mediante la API de Supabase autenticada con RLS.
   - La ruta en almacenamiento sigue el patrón: `{tenant_id}/{course_id}/{clean_filename}`.
   - El cliente calcula localmente el hash SHA-256 del archivo.
2. **ML-API (`POST /api/v1/content-generation/upload-material`):**
   - Acepta referencias directas de almacenamiento (`storage_path`, `storage_bucket`, `original_filename`, `mime_type`, `file_size_bytes`, `file_checksum`) sin requerir los bytes binarios del archivo.
   - Valida rigurosamente la autorización del inquilino mediante `validate_storage_authorization()` (la ruta debe comenzar con el `tenant_id` del docente autenticado; cualquier intento de path traversal o acceso cruzado es rechazado con 400/403).
   - Valida el tipo MIME permitido (`application/pdf`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`) y el tamaño máximo (hasta 30 MB).
   - Devuelve el contrato `UploadMaterialResponse`.
3. **Creación de Trabajos (`POST /api/v1/content-generation/jobs`):**
   - Si `CONTENT_GENERATION_WORKER_ENABLED=false` (valor por defecto en Lambda), responde inmediatamente con `503 Service Unavailable` (`CONTENT_GENERATION_UNAVAILABLE`), evitando que los trabajos queden encolados indefinidamente.

---

## 5. Matriz de Permisos IAM Definitiva (Principio de Mínimo Privilegio)

Se delimitan cinco dominios de permisos estrictamente independientes, utilizando la estrategia recomendada de **CloudFormation Execution Role dedicado (`sam deploy --role-arn`)**:

| Dominio / Identidad | Entidad Principal (Principal) | Propósito / Alcance | Privilegios Otorgados |
|---|---|---|---|
| **1. Deployment Identity** | Usuario IAM / OIDC CI/CD (`platmicro`) | Ejecutar `sam deploy` y orquestar el ciclo de despliegue | CloudFormation ChangeSets, S3 artefactos SAM, PassRole a CloudFormation, ECR Auth |
| **2. CFN Execution Role** | `cloudformation.amazonaws.com` | Crear/actualizar recursos del stack durante el despliegue | Lambda, Function URL, Log Group, IAM Role de Lambda, PassRole a Lambda |
| **3. Lambda Execution Role** | `lambda.amazonaws.com` | Operación en tiempo de ejecución del contenedor | CloudWatch Logs (`PutLogEvents`), Secrets Manager (`GetSecretValue` solo DSN) |
| **4. ECR Push/Pull** | Deployment Identity (Push) / Lambda Service (Pull) | Publicación y descarga de imágenes Docker | Push limitado al repo `nexo-mvp-ml-api`; Pull gestionado por AWS Lambda |
| **5. Secrets Manager Ops** | Operador de Seguridad (CLI manual) | Crear y consultar el secreto de base de datos | `CreateSecret`, `DescribeSecret`, `GetSecretValue`, `TagResource` en `nexo-mvp-database-dsn-*` |

> **NOTA DE GOBERNANZA:** Queda terminantemente prohibido el uso de `AdministratorAccess`. No se ha creado aún ninguna identidad ni política en AWS; estas definiciones constituyen la especificación canónica lista para autorización.

---

### A. Política de la Identidad de Despliegue (`NexoMvpDeploymentPolicy`)

Esta política se asigna al usuario u operador IAM (`platmicro`) o rol de CI/CD. **No tiene permisos para crear roles IAM directamente ni para modificar la función Lambda fuera de CloudFormation**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAuthToken",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRImagePushOperations",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories"
      ],
      "Resource": "arn:aws:ecr:us-east-2:716174523077:repository/nexo-mvp-ml-api"
    },
    {
      "Sid": "CloudFormationGlobalReadAndValidation",
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ListStacks"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudFormationStackManagement",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:GetTemplate",
        "cloudformation:ListStackResources",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:ListChangeSets"
      ],
      "Resource": [
        "arn:aws:cloudformation:us-east-2:716174523077:stack/nexo-mvp-*/*",
        "arn:aws:cloudformation:us-east-2:716174523077:stack/aws-sam-cli-managed-default/*"
      ]
    },
    {
      "Sid": "ServerlessTransformAuthorization",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:us-east-2:aws:transform/Serverless-2016-10-31"
    },
    {
      "Sid": "PassRoleToCloudFormationOnly",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::716174523077:role/nexo-mvp-cloudformation-role",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "cloudformation.amazonaws.com"
        }
      }
    },
    {
      "Sid": "S3SamArtifactBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::aws-sam-cli-managed-*",
        "arn:aws:s3:::aws-sam-cli-managed-*/*"
      ]
    }
  ]
}
```

---

### B. Rol de Ejecución de CloudFormation (`nexo-mvp-cloudformation-role`)

Asumido por `cloudformation.amazonaws.com` mediante `--role-arn`. Contiene los permisos para aprovisionar y mutar exclusivamente los recursos de los stacks `nexo-mvp-*`:

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudformation.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permission Policy (`NexoMvpCloudFormationExecutionPolicy`):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaFunctionAndUrlManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:PublishVersion",
        "lambda:CreateFunctionUrlConfig",
        "lambda:UpdateFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:GetPolicy",
        "lambda:PutFunctionConcurrency",
        "lambda:DeleteFunctionConcurrency",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags"
      ],
      "Resource": "arn:aws:lambda:us-east-2:716174523077:function:nexo-mvp-*"
    },
    {
      "Sid": "IAMRoleManagementForLambdaOnly",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:UpdateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:GetRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies"
      ],
      "Resource": "arn:aws:iam::716174523077:role/nexo-mvp-*-role"
    },
    {
      "Sid": "PassRoleToLambdaService",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::716174523077:role/nexo-mvp-*-role",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    },
    {
      "Sid": "CloudWatchLogGroupGlobalDescribe",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogGroupManagement",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy",
        "logs:DeleteRetentionPolicy",
        "logs:TagLogGroup",
        "logs:UntagLogGroup",
        "logs:TagResource",
        "logs:UntagResource",
        "logs:ListTagsForResource"
      ],
      "Resource": "arn:aws:logs:us-east-2:716174523077:log-group:/aws/lambda/nexo-mvp-*"
    },
    {
      "Sid": "ServerlessTransformInCFN",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:us-east-2:aws:transform/Serverless-2016-10-31"
    },
    {
      "Sid": "ECRRepositoryManagementForStack",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:DescribeRepositories",
        "ecr:PutLifecyclePolicy",
        "ecr:GetLifecyclePolicy",
        "ecr:PutImageScanningConfiguration",
        "ecr:GetRepositoryPolicy",
        "ecr:TagResource",
        "ecr:UntagResource",
        "ecr:ListTagsForResource"
      ],
      "Resource": "arn:aws:ecr:us-east-2:716174523077:repository/nexo-mvp-*"
    }
  ]
}
```

---

### C. Lambda Execution Role (`nexo-mvp-ml-api-role`)

Definido en `template.yaml`, asumido por `lambda.amazonaws.com`. Mínimo privilegio estricto:

**Managed Policy:** `arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole` (emisión de logs a CloudWatch).

**Inline Policy (`SecretsManagerDatabaseSecretAccess`):**
En `template.yaml`, el recurso se enlaza directamente al ARN canónico oficial mediante `Resource: !Ref DatabaseSecretArn`. A nivel de especificación IAM estática, cubre el sufijo aleatorio de 6 caracteres generado por AWS Secrets Manager:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsManagerDatabaseSecretAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-2:716174523077:secret:nexo-mvp-database-dsn-*"
    }
  ]
}
```

---

### D. Política de Operaciones ECR (`NexoMvpEcrPushPolicy`)

Asignada a la identidad de CI/CD u operador responsable de compilar y publicar imágenes de contenedor a Amazon ECR (`build_and_push.sh`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRGetAuthorizationToken",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRRepositoryPushPullOperations",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages",
        "ecr:ListImages"
      ],
      "Resource": "arn:aws:ecr:us-east-2:716174523077:repository/nexo-mvp-ml-api"
    }
  ]
}
```

---

### E. Política de Operador para Secrets Manager (`NexoMvpSecretsManagerOperatorPolicy`)

Asignada exclusivamente al operador de seguridad para la creación, actualización y consulta interactiva del secreto de conexión a Supabase (`nexo-mvp-database-dsn`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsManagerCreateAndDescribeOperations",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:TagResource"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-2:716174523077:secret:nexo-mvp-database-dsn-*"
    },
    {
      "Sid": "SecretsManagerListOperations",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 6. Procedimiento de Construcción Docker Single-Architecture

AWS Lambda requiere que las imágenes de contenedor sean manifiestos individuales de arquitectura única (`application/vnd.docker.distribution.manifest.v2+json` o `application/vnd.oci.image.manifest.v1+json`).

Las versiones recientes de Docker Buildx habilitan por defecto la generación de índices multi-arquitectura OCI con atestaciones SLSA (`--provenance=true`), las cuales son **rechazadas por AWS Lambda** con el error:
```
The image manifest is not supported: Lambda only supports single-architecture image manifests.
```

El script `deploy/aws/build_and_push.sh` garantiza la creación de un manifiesto de arquitectura única `linux/amd64` mediante:
```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --file services/ml-api/Dockerfile.lambda \
  --tag "${FULL_IMAGE_URI}" \
  --load \
  .
```

---

## 7. Guía de Despliegue Operativo Paso a Paso

### Prerrequisitos
- AWS CLI v2 autenticado con perfil `platmicro`:
  ```bash
  aws sts get-caller-identity --profile platmicro
  # Esperado: Account: 716174523077, Region: us-east-2
  ```
- AWS SAM CLI v1.100+.
- Docker activo con BuildKit / Buildx.

### Paso 1: Desplegar Repositorio ECR
```bash
sam deploy \
  --template-file deploy/aws/ecr.yaml \
  --stack-name nexo-mvp-ecr \
  --region us-east-2 \
  --profile platmicro \
  --capabilities CAPABILITY_IAM
```

### Paso 2: Compilar y Publicar Imagen Docker en ECR
```bash
AWS_REGION=us-east-2 \
AWS_PROFILE=platmicro \
deploy/aws/build_and_push.sh
```

### Paso 3: Crear Secreto de Base de Datos y Obtener ARN Oficial

> [!TIP] **Recomendación:** Se recomienda crear el secreto a través de la consola web de AWS Secrets Manager (Sección 2) para máxima seguridad y cero visibilidad en procesos de terminal.
> Si utiliza AWS CLI, emplee `file:///dev/stdin` para evitar exponer la contraseña en los argumentos del proceso (`/proc/$PID/cmdline`):

```bash
# Crear el secreto leyendo el payload JSON desde stdin
aws secretsmanager create-secret \
  --name nexo-mvp-database-dsn \
  --description "DSN de Supabase Transaction Pooler para PlataformaMicro ML-API" \
  --secret-string file:///dev/stdin \
  --region us-east-2 \
  --profile platmicro << 'EOF'
{"DATABASE_URL":"postgresql://postgres.oqjahhbqcethwgpufgnm:TU_PASSWORD_AQUI@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"}
EOF

# Obtener el ARN oficial generado por AWS (con sufijo aleatorio oficial)
DATABASE_SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id nexo-mvp-database-dsn \
  --region us-east-2 \
  --profile platmicro \
  --query "ARN" \
  --output text)

echo "DatabaseSecretArn resuelto: ${DATABASE_SECRET_ARN}"
```

### Paso 4: Desplegar Stack de Inferencia Lambda con SAM
```bash
# Obteniendo ImageUri generado en el Paso 2
IMAGE_URI="716174523077.dkr.ecr.us-east-2.amazonaws.com/nexo-mvp-ml-api:mvp-$(git rev-parse --short HEAD)"

sam deploy \
  --template-file deploy/aws/template.yaml \
  --stack-name nexo-mvp-ml-api \
  --region us-east-2 \
  --profile platmicro \
  --capabilities CAPABILITY_NAMED_IAM \
  --resolve-s3 \
  --parameter-overrides \
    ImageUri="${IMAGE_URI}" \
    DatabaseSecretArn="${DATABASE_SECRET_ARN}" \
    SupabaseUrl="https://oqjahhbqcethwgpufgnm.supabase.co" \
    CorsOrigins="https://plataformamicro.fabriziovalerio-c.workers.dev" \
    ReservedConcurrency=5 \
    MemorySize=1024 \
    Timeout=30
```

> **Opción con CloudFormation Execution Role:**
> Si se ha configurado el rol de ejecución de CloudFormation (`nexo-mvp-cloudformation-role`), añada `--role-arn arn:aws:iam::716174523077:role/nexo-mvp-cloudformation-role` al comando anterior.

### Paso 5: Verificación Post-Despliegue
```bash
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name nexo-mvp-ml-api \
  --region us-east-2 \
  --profile platmicro \
  --query "Stacks[0].Outputs[?OutputKey=='FunctionUrl'].OutputValue" \
  --output text)

echo "Function URL: ${FUNCTION_URL}"

# 1. Health check público (200 OK)
curl -i "${FUNCTION_URL}api/v1/health"

# 2. Retención sin token (401 Unauthorized esperado)
curl -i "${FUNCTION_URL}api/v1/students/me/retention"

# 3. Verificación CORS Preflight
curl -i -X OPTIONS "${FUNCTION_URL}api/v1/students/me/retention" \
  -H "Origin: https://plataformamicro.fabriziovalerio-c.workers.dev" \
  -H "Access-Control-Request-Method: GET"
```

---

## 8. Matriz de Variables de Entorno del Contenedor Lambda

| Variable | Valor Configurado | Justificación Técnica |
|---|---|---|
| `ENVIRONMENT` | `production` | Activa guardas estrictas de producción (rechazo de modelos sintéticos). |
| `DEBUG` | `false` | Desactiva trazas de error verbosas en respuestas HTTP públicas. |
| `REPOSITORY_BACKEND` | `postgres` | Persistencia en base de datos real Supabase vía asyncpg. |
| `DATABASE_SECRET_ARN` | `!Ref DatabaseSecretArn` | ARN en Secrets Manager para recuperación segura de DSN sin contraseñas en texto plano. |
| `DB_POOL_MODE` | `transaction` | Optimizado para el Transaction Pooler de Supavisor (puerto 6543). |
| `DB_POOL_MIN_SIZE` | `1` | Conexión mínima por instancia Lambda. |
| `DB_POOL_MAX_SIZE` | `1` | Conexión máxima por instancia para no agotar el pool de Supabase. |
| `DB_STATEMENT_CACHE_SIZE` | `0` | Obligatorio en Transaction Mode para prevenir colisiones de sentencias preparadas. |
| `DB_SSL_MODE` | `require` | Cifrado TLS obligatorio para conexiones remotas hacia Supabase. |
| `DB_COMMAND_TIMEOUT` | `30` | Timeout de ejecución de consultas en segundos. |
| `DB_CONNECT_TIMEOUT` | `5` | Timeout de establecimiento de conexión en segundos. |
| `DB_MAX_INACTIVE_CONNECTION_LIFETIME` | `30` | Descarta conexiones inactivas tras ciclos freeze/thaw de Lambda. |
| `DB_MAX_QUERIES` | `1000` | Recicla conexiones para prevenir fugas de memoria o socket stale. |
| `DB_STALE_RETRY_ATTEMPTS` | `1` | Reintento automático ante socket cerrado tras descongelamiento de Lambda. |
| `SUPABASE_URL` | `!Ref SupabaseUrl` | URL base de Supabase para JWKS y validación de tokens. |
| `SUPABASE_JWKS_URL` | `${SupabaseUrl}/auth/v1/.well-known/jwks.json` | Endpoint de claves públicas asimétricas ES256 (GoTrue). |
| `CORS_ORIGINS` | `!Ref CorsOrigins` | Origen frontend homologado (`https://plataformamicro.fabriziovalerio-c.workers.dev`). |
| `ENABLE_CORS_MIDDLEWARE` | `false` | Deshabilita CORSMiddleware interno en Lambda (CORS gestionado exclusivamente en Function URL con `AllowCredentials: false`). |
| `CONTENT_GENERATION_WORKER_ENABLED` | `false` | Deshabilita worker en background continuo incompatible con el ciclo de vida de Lambda. |
| `MODEL_ARTIFACTS_DIR` | `/app/ml/artifacts` | Ruta absoluta a los artefactos del modelo en la imagen Docker. |
| `TMPDIR` | `/tmp` | Directorio temporal de escritura compatible con filesystem de solo lectura. |
| `PORT` | `8000` | Puerto de escucha de Uvicorn. |
| `AWS_LWA_PORT` | `8000` | Puerto objetivo del AWS Lambda Web Adapter. |
| `AWS_LWA_READINESS_CHECK_PATH` | `/api/v1/health` | Ruta de sondeo de preparación (readiness probe) de Lambda Web Adapter. |
| `AWS_LWA_INVOKE_MODE` | `buffered` | Modo de invocación estándar para peticiones síncronas hasta 6 MB. |

---

## 9. Plan Definitivo de Aprovisionamiento y Gobernanza

1. **Aprobación de Políticas IAM:** El equipo de seguridad debe revisar y autorizar la creación de `NexoMvpDeploymentPolicy` y `nexo-mvp-cloudformation-role`. Ningún recurso ha sido creado ni mutado en AWS durante esta auditoría.
2. **Aprovisionamiento del Secreto en AWS Secrets Manager:**
   - Crear el secreto `nexo-mvp-database-dsn` en `us-east-2` utilizando el procedimiento libre de historial shell documentado en la Sección 2.
   - Extraer el ARN exacto con `aws secretsmanager describe-secret`.
3. **Despliegue de Infraestructura SAM:**
   - Desplegar `ecr.yaml` (`nexo-mvp-ecr`).
   - Ejecutar `build_and_push.sh` generando la imagen Docker `linux/amd64` sin attestations.
   - Desplegar `template.yaml` con `--capabilities CAPABILITY_NAMED_IAM`.
4. **Coordinación de DNS y URL Pública:**
   - Actualizar `NEXT_PUBLIC_API_URL` en Cloudflare Workers (`plataformamicro.fabriziovalerio-c.workers.dev`) con la Function URL generada tras verificar las pruebas de humo.
5. **Transición a CloudFront OAC + WAF (Post-MVP):**
   - Planificar la transición a `AuthType: AWS_IAM` protegiendo la Function URL detrás de Amazon CloudFront con Origin Access Control (OAC) y AWS WAF en Fase 2.
