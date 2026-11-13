# AWS-LAMBDA-02.2 — Final Deployment Readiness Audit

**Proyecto:** PlataformaMicro  
**Rama:** `release/mvp-aws-lambda`  
**Fecha de Auditoría:** 12 de Noviembre de 2026  
**Región AWS Destino:** `us-east-2` (Ohio)  
**ID de Cuenta AWS:** `716174523077`  
**Perfil Evaluado:** `platmicro`  
**Base de Datos & Auth:** Supabase PostgreSQL 15+ (Supavisor Transaction Pooler, `us-east-2`) & GoTrue ES256  
**Frontend Autorizado:** `https://plataformamicro.fabriziovalerio-c.workers.dev`  
**Estado de Modificación en la Nube:** Cero (0) recursos creados, modificados o eliminados en AWS.

---

## 1. Hallazgos Corregidos

1. **Eliminación de Parámetros Innecesarios en SAM (`deploy/aws/template.yaml`):**
   - Se suprimieron los parámetros `SupabaseJwtSecret` y `SupabaseServiceRoleKey` y sus correspondientes variables de entorno.
   - En producción sobre AWS Lambda, la autenticación se ejecuta exclusivamente mediante firmas asimétricas ES256 contra el endpoint JWKS de GoTrue (`${SUPABASE_URL}/auth/v1/.well-known/jwks.json`), y la persistencia se realiza mediante conexión directa PostgreSQL asíncrona (`asyncpg`) autenticada por `DATABASE_SECRET_ARN`.
2. **Mitigación de Exposición de Secretos en Argumentos de Procesos (`deploy/aws/README.md`):**
   - Se corrigió la instrucción de creación de secreto para prohibir el paso del DSN como argumento directo de línea de comandos en `--secret-string "..."` (el cual es visible para cualquier proceso local a través de `/proc/$PID/cmdline` o `ps aux`).
   - Se estableció como método recomendado la **Consola Web de AWS Secrets Manager** o la inyección segura por `stdin` (`file:///dev/stdin`).
3. **Guarda en UI para Cargas de Materiales Docentes (`apps/web`):**
   - En `GenerateQuestionsModal.tsx`, se incorporó un banner preventivo informando al docente que la extracción curricular con LLMs se encuentra en transición hacia un worker asíncrono desacoplado (Fase 2).
   - Se inhabilitó el botón de envío en la interfaz mientras `CONTENT_GENERATION_WORKER_ENABLED=false` en el backend Lambda, evitando que el usuario inicie cargas que culminarían en HTTP 503 (`WORKER_NOT_AVAILABLE_ON_SERVERLESS`) y dejen archivos huérfanos en Supabase Storage.
4. **Verificación Estricta de Permisos de Invocación de Function URL:**
   - La inspección del CloudFormation traducido (`sam translate` / debug) confirmó que AWS SAM genera automáticamente ambos permisos requeridos por el estándar actual de AWS: `lambda:InvokeFunctionUrl` (con `FunctionUrlAuthType: NONE`) y `lambda:InvokeFunction` (con `InvokedViaFunctionUrl: true`).
5. **Convención Canónica de Nombres sin Duplicación:**
   - En `template.yaml`, `RoleName: !Sub "${AWS::StackName}-role"` genera exactamente `nexo-mvp-ml-api-role` cuando el stack es `nexo-mvp-ml-api`.
   - Se exige el flag `--capabilities CAPABILITY_NAMED_IAM` en todas las ejecuciones de SAM CLI.
6. **Construcción Docker Single-Architecture:**
   - En `build_and_push.sh`, se forzó `--provenance=false --sbom=false` y `--load`, evitando la creación de manifiestos OCI multi-arquitectura o atestaciones incompatibles con Lambda.

---

## 2. Hallazgos Pendientes

1. **Uso de Identidad Root en el Perfil CLI Local (`platmicro`):**
   - El sondeo de `aws sts get-caller-identity` confirmó que el perfil activo corresponde a la cuenta root (`arn:aws:iam::716174523077:root`).
   - **Acción Requerida:** De acuerdo con las normas de seguridad de AWS y las restricciones del proyecto, **se detiene cualquier despliegue automatizado directo con estas credenciales**. El propietario de la cuenta debe aprovisionar manualmente un usuario o rol IAM de despliegue con privilegios mínimos mediante la consola web antes de ejecutar el primer despliegue.
2. **Aprovisionamiento Manual Inicial del CloudFormation Execution Role:**
   - La política de despliegue (`NexoMvpDeploymentPolicy`) no incluye (por principio de privilegio mínimo) permisos para crear o modificar roles IAM a discreción. Por consiguiente, `nexo-mvp-cloudformation-role` debe ser creado una sola vez en la consola IAM de AWS antes de ejecutar `sam deploy --role-arn`.

---

## 3. Identidad AWS Verificada

Se ejecutó la consulta no destructiva de verificación:

```bash
aws sts get-caller-identity --profile platmicro
```

**Salida Obtenida:**
```json
{
    "UserId": "716174523077",
    "Account": "716174523077",
    "Arn": "arn:aws:iam::716174523077:root"
}
```

> [!CAUTION] **Bloqueo de Seguridad Operativa:**
> La llamada confirma que la sesión actual opera bajo las credenciales de la cuenta `root`. Las políticas de despliegue y roles presentados en este documento están diseñados para operar bajo el principio de privilegio mínimo. **No se debe desplegar infraestructura productiva utilizando la cuenta root**.

### Procedimiento para Configurar la Identidad IAM de Despliegue No-Root:
1. Inicie sesión en la [Consola de Administración de AWS](https://console.aws.amazon.com/) con el usuario root.
2. Navegue a **IAM → Users → Create user**.
3. Nombre de usuario sugerido: `nexo-deployer`.
4. En **Set permissions**, cree y asocie la política personalizada `NexoMvpDeploymentPolicy` (detallada en la Sección 5).
5. En la pestaña **Security credentials**, genere un par de **Access Keys** para uso en CLI.
6. En su entorno local/WSL, configure el nuevo perfil:
   ```bash
   aws configure --profile platmicro-deployer
   ```
7. Verifique que la identidad resuelta sea la correcta:
   ```bash
   aws sts get-caller-identity --profile platmicro-deployer
   # Salida esperada: "Arn": "arn:aws:iam::716174523077:user/nexo-deployer"
   ```

---

## 4. Trust Policy de CloudFormation

Para delegar el aprovisionamiento de la infraestructura del stack sin otorgar privilegios administrativos a la identidad CLI, se utiliza un rol de ejecución dedicado de CloudFormation.

- **Nombre del Rol:** `nexo-mvp-cloudformation-role`
- **ARN Canónico:** `arn:aws:iam::716174523077:role/nexo-mvp-cloudformation-role`
- **Principal de Confianza:** `cloudformation.amazonaws.com`

**Documento JSON de Trust Policy:**
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

> [!NOTE] **Verificación de Delegación (`iam:PassRole`):**
> La política de la identidad de despliegue permite `iam:PassRole` exclusivamente sobre este rol y bajo la condición explícita `StringEquals: {"iam:PassedToService": "cloudformation.amazonaws.com"}`.

---

## 5. Matriz IAM Final

Se define una separación estricta de responsabilidades en 5 identidades y políticas de mínimo privilegio:

```mermaid
flowchart TD
    User["Operador / CI/CD (nexo-deployer)"]
    CFNRole["CloudFormation Execution Role (nexo-mvp-cloudformation-role)"]
    LambdaRole["Lambda Execution Role (nexo-mvp-ml-api-role)"]
    Secrets["AWS Secrets Manager (nexo-mvp-database-dsn)"]
    ECR["Amazon ECR (nexo-mvp-ml-api)"]
    Lambda["AWS Lambda (nexo-mvp-ml-api)"]

    User -->|"sam deploy --role-arn"| CFNRole
    CFNRole -->|"Aprovisiona & Gestiona"| Lambda
    CFNRole -->|"Crea & Pasa Rol"| LambdaRole
    CFNRole -->|"Aprovisiona Repositorio"| ECR
    LambdaRole -->|"Lectura Exclusiva DSN"| Secrets
    Lambda -->|"Asume al Ejecutar"| LambdaRole
```

### 1. Política de la Identidad de Despliegue (`NexoMvpDeploymentPolicy`)
Asociada al usuario IAM `nexo-deployer`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationOrchestration",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplate"
      ],
      "Resource": [
        "arn:aws:cloudformation:us-east-2:716174523077:stack/nexo-mvp-*/*",
        "arn:aws:cloudformation:us-east-2:716174523077:stack/aws-sam-cli-managed-default/*"
      ]
    },
    {
      "Sid": "CloudFormationGlobalValidation",
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ListStacks"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AuthorizeServerlessTransform",
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
      "Sid": "SamCliArtifactsBucketAccess",
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

### 2. Política del Rol de Ejecución de CloudFormation (`NexoMvpCloudFormationExecutionPolicy`)
Asociada al rol `nexo-mvp-cloudformation-role`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageLambdaAndFunctionUrls",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:CreateFunctionUrlConfig",
        "lambda:UpdateFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags"
      ],
      "Resource": "arn:aws:lambda:us-east-2:716174523077:function:nexo-mvp-*"
    },
    {
      "Sid": "ManageScopedExecutionRoles",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies"
      ],
      "Resource": "arn:aws:iam::716174523077:role/nexo-mvp-*-role"
    },
    {
      "Sid": "PassExecutionRoleToLambda",
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
      "Sid": "ManageScopedLogGroups",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy",
        "logs:DeleteRetentionPolicy",
        "logs:TagResource",
        "logs:UntagResource",
        "logs:ListTagsForResource"
      ],
      "Resource": "arn:aws:logs:us-east-2:716174523077:log-group:/aws/lambda/nexo-mvp-*"
    },
    {
      "Sid": "DescribeLogGroupsGlobal",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ManageScopedEcrRepositories",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:DescribeRepositories",
        "ecr:PutLifecyclePolicy",
        "ecr:DeleteLifecyclePolicy",
        "ecr:PutImageScanningConfiguration",
        "ecr:TagResource",
        "ecr:UntagResource",
        "ecr:ListTagsForResource"
      ],
      "Resource": "arn:aws:ecr:us-east-2:716174523077:repository/nexo-mvp-*"
    }
  ]
}
```

### 3. Política del Rol de Ejecución de Lambda (`nexo-mvp-ml-api-role`)
- **Política Administrada:** `arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole` (permite `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`).
- **Política en Línea (`SecretsManagerAccess`):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadDatabaseSecretOnly",
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

## 6. Verificación de Permisos y Recursos de Function URL

Se analizó la traducción sintética generada por AWS SAM (`sam validate --debug`):

```yaml
  MlApiFunctionUrl:
    Properties:
      AuthType: NONE
      Cors:
        AllowCredentials: false
        AllowHeaders:
        - authorization
        - content-type
        - x-idempotency-key
        - x-request-id
        AllowMethods:
        - GET
        - POST
        - PUT
        - PATCH
        - DELETE
        - HEAD
        AllowOrigins:
        - https://plataformamicro.fabriziovalerio-c.workers.dev
        MaxAge: 86400
      TargetFunctionArn:
        Ref: MlApiFunction
    Type: AWS::Lambda::Url

  MlApiFunctionUrlPublicPermissions:
    Properties:
      Action: lambda:InvokeFunctionUrl
      FunctionName:
        Ref: MlApiFunction
      FunctionUrlAuthType: NONE
      Principal: '*'
    Type: AWS::Lambda::Permission

  MlApiFunctionURLInvokeAllowPublicAccess:
    Properties:
      Action: lambda:InvokeFunction
      FunctionName:
        Ref: MlApiFunction
      InvokedViaFunctionUrl: true
      Principal: '*'
    Type: AWS::Lambda::Permission
```

### Aspectos de Seguridad Comprobados:
1. **Doble Permiso Requerido:** SAM emite tanto `lambda:InvokeFunctionUrl` como `lambda:InvokeFunction` con la condición `InvokedViaFunctionUrl: true`.
2. **Autenticación en la Capa de Aplicación:** Aunque la Function URL tenga `AuthType: NONE` para permitir la conectividad directa del navegador web, FastAPI valida la firma del token JWT asimétrico (ES256) en todas las rutas funcionales mediante `app.core.auth.py`.
3. **CORS NO es Autenticación:** CORS opera exclusivamente como una directiva del navegador para restringir orígenes cruzados. La protección de datos y el aislamiento de tenants dependen exclusivamente de la criptografía JWT y de las consultas a `public.profiles`.
4. **Capacidad de Carga y Concurrencia (Simulación 66 Estudiantes):**
   - **Parámetro SAM:** `ReservedConcurrency: 5`.
   - **Tiempo de Respuesta en Caliente:** 40 a 60 ms por inferencia/evaluación.
   - **Tasa de Llegada Máxima Estimada:** 66 estudiantes respondiendo un cuestionario simultáneo generan ~4.4 peticiones/segundo en promedio (un intento cada 15 s).
   - **Aplicación de Ley de Little:** $L = \lambda \times W = 4.4 \times 0.050\text{ s} \approx 0.22$ ejecuciones concurrentes.
   - **Conclusión:** El límite de 5 instancias concurrentes absorbe con holgura ráfagas de hasta $66\text{ req/s}$ ($L \approx 3.3$) sin degradación ni encolamiento, salvaguardando el límite de conexiones del pooler de Supabase.

---

## 7. Procedimiento Seguro para Crear el Secreto

### Opción 1: Consola de AWS (Método Oficial Preferente)
1. Navegue a **AWS Secrets Manager** en `us-east-2`.
2. Clic en **Store a new secret** $\rightarrow$ **Other type of secret**.
3. En **Key/value pairs**, añada `DATABASE_URL` con el DSN copiado de Supabase (*Connect → Transaction pooler*).
4. Nombre del secreto: `nexo-mvp-database-dsn`.
5. Guarde el secreto y copie el **Secret ARN** oficial generado.

### Opción 2: AWS CLI vía STDIN (Cero Exposición en `/proc/$PID/cmdline`)
```bash
aws secretsmanager create-secret \
  --name nexo-mvp-database-dsn \
  --description "DSN de Supabase Transaction Pooler para PlataformaMicro ML-API" \
  --secret-string file:///dev/stdin \
  --region us-east-2 \
  --profile platmicro-deployer << 'EOF'
{"DATABASE_URL":"postgresql://postgres.oqjahhbqcethwgpufgnm:PASSWORD_AQUI@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"}
EOF

# Obtener ARN exacto
DATABASE_SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id nexo-mvp-database-dsn \
  --region us-east-2 \
  --profile platmicro-deployer \
  --query "ARN" \
  --output text)
```

---

## 8. Secuencia de Aprovisionamiento (Plan de Ejecución)

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrador (Consola IAM)
    actor Deployer as Operador CLI (nexo-deployer)
    participant ECR as Amazon ECR
    participant CFN as AWS CloudFormation
    participant Secrets as AWS Secrets Manager
    participant Lambda as AWS Lambda

    Admin->>Admin: 1. Crear nexo-mvp-cloudformation-role y nexo-deployer
    Admin->>Secrets: 2. Crear nexo-mvp-database-dsn en us-east-2
    Deployer->>CFN: 3. sam deploy ecr.yaml (--role-arn)
    CFN->>ECR: Aprovisiona nexo-mvp-ml-api
    Deployer->>ECR: 4. docker build & push linux/amd64
    Deployer->>CFN: 5. sam deploy template.yaml (--capabilities CAPABILITY_NAMED_IAM --role-arn)
    CFN->>Lambda: Despliega nexo-mvp-ml-api y Function URL
    Deployer->>Lambda: 6. Pruebas de humo (health, 401 sin token, CORS)
```

---

## 9. Evidencia de Pruebas de Validación Local

Se certifican los siguientes resultados en el entorno local (WSL2 / Linux Ubuntu 24.04):

| Prueba | Comando Ejecutado | Resultado | Estado |
|---|---|---|:---:|
| **SAM Templates Lint** | `sam validate --lint -t deploy/aws/template.yaml && sam validate --lint -t deploy/aws/ecr.yaml` | Ambos templates válidos y conformes a especificación. | **PASSED** |
| **Suite Completa Pytest** | `pytest services/ml-api/tests` | **306 passed, 2 skipped** en 40.54 s. | **PASSED** |
| **Hardening de Lambda** | `pytest services/ml-api/tests/test_aws_lambda_hardening.py` | **33 passed** (secrets, CORS, payload limits, fallback). | **PASSED** |
| **Verificación M2 Contratos** | `python3 scripts/verify-m2.py` | **106 checks passed**, 0 failed. | **PASSED** |
| **Frontend Auth Matrix** | `node apps/web/src/tests/auth-authorization.test.mjs` | **21 passed** en 12.0 ms. | **PASSED** |
| **Frontend Data Integrity** | `node apps/web/src/tests/data-integrity.test.mjs` | **15 passed** en 22.5 ms. | **PASSED** |
| **Frontend TypeCheck** | `npx tsc --noEmit` en `apps/web/` | 0 errores de compilación TypeScript. | **PASSED** |
| **Análisis Estático Ruff** | `ruff check services/ml-api/app services/ml-api/tests` | All checks passed (0 warnings/errors). | **PASSED** |
| **Tipado Estricto MyPy** | `mypy --config-file pyproject.toml services/ml-api/app ml/src` | Success: no issues found in 92 source files. | **PASSED** |
| **Docker Build Single-Arch** | `docker buildx build --platform linux/amd64 --provenance=false --sbom=false` | Imagen compilada exitosamente (712 MB). | **PASSED** |
| **Filesystem Read-Only** | `docker run --read-only --tmpfs /tmp` | Health probe HTTP 200 OK verificado en contenedor. | **PASSED** |

---

## 10. Decisión Final

### Estado de Preparación: **NOT READY FOR DIRECT ROOT DEPLOYMENT**  
### Estado del Código y Artefactos: **READY FOR MANUAL DEPLOYMENT ONCE IAM USER IS CONFIGURED**

**Justificación:**
1. El repositorio, los contratos OpenAPI, el código fuente Python, la interfaz Next.js y los templates CloudFormation/SAM se encuentran **100% validados, endurecidos y listos para producción**.
2. Sin embargo, las credenciales actualmente activas en el entorno local pertenecen a la cuenta **root** (`arn:aws:iam::716174523077:root`). Por política estricta de seguridad y gobernanza, el despliegue con credenciales root está **terminantemente prohibido**.
3. **Condición de Desbloqueo:** Una vez que el propietario de la cuenta cree el usuario `nexo-deployer` y el rol `nexo-mvp-cloudformation-role` en la consola IAM de AWS, el proyecto pasará inmediatamente a estado **READY FOR MANUAL DEPLOYMENT**.
