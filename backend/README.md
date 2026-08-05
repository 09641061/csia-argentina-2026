# Sentinel AI Guard — Backend

Portal seguro de acceso a una IA local. Una consulta y un archivo opcional se revisan
antes de que el modelo pueda responder. Solo el contenido permitido llega al generador.

```text
prompt + archivo opcional
  -> IAM autentica al usuario antes de permitir operaciones funcionales
  -> Chat recibe la pregunta y obtiene capacidades externas mediante ACL
  -> Documents valida el formato real y sube los bytes a Cloudinary (se guarda la URL)
  -> Analysis extrae una estructura acotada (Ollama Vision para las imágenes)
  -> Ollama clasifica obligatoriamente el contenido local completo sin devolver valores
  -> Analysis detecta y enmascara datos sensibles
  -> Ollama clasifica obligatoriamente el riesgo contextual
  -> Decision & Audit aplica ALLOWED/BLOCKED
  -> si es ALLOWED y hay pregunta: Ollama genera la respuesta
  -> la interacción queda auditada con evidencia enmascarada
```

## Alcance del MVP

- Formatos: JSON, PNG y JPEG, con máximo 5 MB.
- Decisiones `ALLOWED` y `BLOCKED`. No hay WARN, SANITIZE ni aprobaciones.
- No se entrega al usuario ninguna versión sanitizada del contenido bloqueado.
- Autenticación local inicial con credenciales configuradas en Python; sin conversaciones, RAG ni dashboard.
- Ollama tiene cuatro usos separados: descubrimiento de datos sensibles, visión documental,
  evaluación contextual y generación.
- La IA es una dependencia funcional: sin una evaluación válida no existe `ALLOWED`; sin visión no
  se pueden analizar imágenes; sin generación no existe respuesta.

## Contextos delimitados

| Contexto | Responsabilidad | No hace |
| --- | --- | --- |
| **Documents** | Recibe archivos admitidos, valida tipo/tamaño/contenedor, los guarda con nombre interno opaco y expone metadatos seguros | No decide el riesgo ni llama al generador |
| **Analysis** | Extracción local acotada, visión Ollama cuando corresponde, escaneo determinista, enmascarado, evaluación contextual obligatoria y cálculo de riesgo | No genera la respuesta ni decide si Ollama puede responder |
| **Decision & Audit** | Política ALLOWED/BLOCKED, autorización de generación, ejecución del generador, historial explicable | No analiza contenido por su cuenta |
| **IAM** | Autentica al usuario local y valida tokens Bearer firmados | No persiste usuarios ni credenciales |
| **Chat** | Recibe preguntas y recursos y consume la capacidad segura mediante ACL | No importa modelos internos de otros contextos |

La comunicación entre contextos pasa por fachadas ACL públicas
(`DocumentsContextFacade`, `AnalysisContextFacade`, `DecisionContextFacade`) y adaptadores del
consumidor. Ningún contexto importa los modelos SQLAlchemy ni las entidades internas de otro. No
hay Kafka ni RabbitMQ.

## Regla principal

El contenido solo queda `ALLOWED` cuando **todas** estas condiciones se cumplen:

- Cada revisión enviada terminó en estado `completed`.
- El riesgo final es `low`.
- No hay hallazgos sensibles confirmados (los placeholders no cuentan).
- No hay prompt injection ni manipulación sospechosa.
- La evaluación de seguridad de Ollama devolvió una respuesta válida.

En cualquier otro caso la decisión es `BLOCKED`. El sistema es *fail-closed*: un error, un timeout
o una respuesta inválida nunca se convierten en riesgo bajo, y la IA nunca puede reducir un riesgo
que las reglas deterministas ya confirmaron.

La garantía "una consulta bloqueada nunca llega al generador" está codificada en el tipo
`GenerationAuthorization`: solo puede construirse a partir de una decisión `ALLOWED`, y el cliente
generador la exige como argumento.

## Requisitos

- Python 3.11 o superior, administrado por `uv` (verificado con 3.13.7).
- PostgreSQL (verificado con 18.1).
- Ollama con `gemma3:4b`, el único modelo que usa el backend (es multimodal, así que también lee
  las imágenes).
- Cuenta de Cloudinary, salvo que uses `DOCUMENT_STORAGE_BACKEND=local`.

## Instalación

```powershell
uv sync --extra dev
```

Copia [.env.example](.env.example) a `.env` y ajusta `DATABASE_URL`.

### Base de datos

El backend crea el esquema al arrancar. La base debe existir:

```powershell
psql -U postgres -c "CREATE DATABASE sentinel_ai_guard;"
```

Si prefieres una instancia aislada con Docker, sin tocar otras bases:

```powershell
docker run -d --name sentinel-postgres `
  -e POSTGRES_PASSWORD=sentinel-dev `
  -e POSTGRES_DB=sentinel_ai_guard `
  -p 5433:5432 postgres:18
```

y usa `DATABASE_URL=postgresql+asyncpg://postgres:sentinel-dev@localhost:5433/sentinel_ai_guard`.

Si la base no está disponible, **el backend falla al arrancar**. Es intencional: una API que
responde sin poder escribir su auditoría es peor que una API caída.

### Ollama

```powershell
ollama pull gemma3:4b
ollama list
```

## Ejecutar

```powershell
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Salud: `http://127.0.0.1:8000/api/v1/health`

## Variables de entorno

| Variable | Uso | Valor sugerido |
| --- | --- | --- |
| `DATABASE_URL` | Conexión SQLAlchemy asíncrona | `postgresql+asyncpg://postgres:admin@localhost:5432/sentinel_ai_guard` |
| `FRONTEND_ORIGIN` | Orígenes permitidos por CORS, separados por comas | `http://localhost:5173,http://127.0.0.1:5173` |
| `DOCUMENT_STORAGE_BACKEND` | `cloudinary` o `local` | `cloudinary` |
| `DOCUMENT_STORAGE_DIR` | Carpeta privada del adaptador local | `storage/documents` |
| `MAX_DOCUMENT_SIZE_MB` | Tamaño máximo del archivo | `5` |
| `CLOUDINARY_*` | Credenciales, obligatorias con el backend `cloudinary` | — |
| `OLLAMA_BASE_URL` | API HTTP local de Ollama | `http://localhost:11434` |
| `OLLAMA_SECURITY_MODEL` | Modelo de evaluación de seguridad | `gemma3:4b` |
| `OLLAMA_SECURITY_TIMEOUT_SECONDS` | Timeout de la evaluación | `120` |
| `OLLAMA_SECURITY_CONTEXT_TOKENS` | Ventana de contexto de la evaluación | `8192` |
| `OLLAMA_SECURITY_MAX_OUTPUT_TOKENS` | Límite de salida de la evaluación | `300` |
| `OLLAMA_DISCOVERY_MODEL` | Clasificación local del contenido extraído completo | `gemma3:4b` |
| `OLLAMA_DISCOVERY_MAX_INPUT_CHARS` | Máximo que puede inspeccionarse completamente | `24000` |
| `OLLAMA_VISION_MODEL` | Modelo multimodal para imágenes PNG/JPEG | `gemma3:4b` |
| `OLLAMA_VISION_TIMEOUT_SECONDS` | Timeout de la extracción visual | `180` |
| `OLLAMA_VISION_CONTEXT_TOKENS` | Ventana de contexto visual | `8192` |
| `OLLAMA_VISION_MAX_OUTPUT_TOKENS` | Límite de la transcripción visual | `1200` |
| `OLLAMA_GENERATION_MODEL` | Modelo de generación de la respuesta | `gemma3:4b` |
| `OLLAMA_GENERATION_TIMEOUT_SECONDS` | Timeout de la generación | `180` |
| `OLLAMA_GENERATION_CONTEXT_TOKENS` | Ventana de contexto de la generación | `8192` |
| `OLLAMA_GENERATION_MAX_OUTPUT_TOKENS` | Límite de salida de la generación | `800` |
| `OLLAMA_GENERATION_MAX_DOCUMENT_CHARS` | Caracteres máximos del documento permitido | `24000` |
| `PROMPT_MIN_LENGTH` / `PROMPT_MAX_LENGTH` | Límites del prompt | `3` / `8000` |

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Estado de PostgreSQL y de los modelos locales |
| `POST` | `/api/v1/auth/login` | Autentica con usuario y contraseña y entrega un Bearer token |
| `POST` | `/api/v1/chat/messages` | Consulta autenticada con JSON o imagen opcional mediante ACL |
| `POST` | `/api/v1/documents` | Registra un archivo admitido (multipart `file`) |
| `GET` | `/api/v1/documents` | Lista paginada de documentos |
| `GET` | `/api/v1/documents/{document_id}` | Metadatos públicos de un documento |
| `GET` | `/api/v1/documents/{document_id}/table` | JSON normalizado como columnas, filas y metadatos |
| `POST` | `/api/v1/documents/{document_id}/analyses` | Revisa un documento registrado |
| `POST` | `/api/v1/prompts/analyses` | Revisa un prompt de texto libre |
| `GET` | `/api/v1/analyses` | Historial paginado de revisiones |
| `GET` | `/api/v1/analyses/{analysis_id}` | Una revisión |
| `GET` | `/api/v1/analyses/{analysis_id}/findings` | Hallazgos enmascarados |
| `POST` | `/api/v1/secure-queries` | **Caso de uso principal**: analizar y consultar |
| `GET` | `/api/v1/interactions` | Historial paginado de interacciones |
| `GET` | `/api/v1/interactions/{interaction_id}` | Detalle explicable de una interacción |

Salvo `/api/v1/health` y `/api/v1/auth/login`, las rutas requieren
`Authorization: Bearer <access_token>`. Todas las rutas son inequívocas: ningún segmento estático
compite con un parámetro de ruta.

Ejemplo:

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin"}'

curl -X POST http://127.0.0.1:8000/api/v1/chat/messages `
  -H "Authorization: Bearer $($login.access_token)" `
  -F "prompt=Explica las ventajas de una arquitectura orientada a eventos."

curl -X POST http://127.0.0.1:8000/api/v1/chat/messages `
  -H "Authorization: Bearer $($login.access_token)" `
  -F "prompt=Segun este inventario, que servicios pertenecen al equipo security?" `
  -F "file=@samples/sample-01-clean-inventory.json;type=application/json"
```

## Qué nunca devuelve la API

`storage_reference`, rutas locales, URLs de almacenamiento, prompts originales, contenido de
documentos, copias sanitizadas, credenciales, tarjetas completas, CVV, evidencia sin enmascarar,
secretos de configuración, stack traces ni mensajes internos.

De un prompt bloqueado se conserva únicamente el *fingerprint* SHA-256, una vista previa
enmascarada, la longitud, los hallazgos enmascarados, el riesgo, la decisión y la fecha.

## Almacenamiento

El adaptador por defecto es `LocalDocumentStorage`: escribe en una carpeta privada del proyecto
(`storage/`, ignorada por Git) con nombres generados (`<uuid4>.bin`). El nombre original nunca se
usa como ruta y toda lectura se confina a la raíz configurada, de modo que un *path traversal* es
imposible incluso con una referencia hostil.

Cloudinary se conserva pero **desactivado por defecto**: enviar un documento a un tercero antes de
revisarlo contradice el producto. Cuando se activa, su lectura pasa por `SafeUrlContentReader`, que
solo admite HTTPS hacia hosts permitidos, rechaza redirecciones y bloquea loopback, redes privadas
y endpoints de metadatos de nube.

## Datos sintéticos

`samples/` contiene los diez documentos originales, el manifiesto ejecutable
[expected-results.json](samples/expected-results.json) y once escenarios de consulta en
[prompt-scenarios.json](samples/prompt-scenarios.json): prompt limpio, correo, contraseña, API key,
tarjeta, prompt injection, consulta permitida con documento, bloqueo por documento, bloqueo por
prompt, fallo de análisis y fallo de generación.

Todos los valores son ficticios y no operativos.

```powershell
uv run python scripts/generate_sample_documents.py   # regenera los diez JSON
uv run --extra dev python scripts/seed_demo_history.py   # historial de demo sin Ollama
```

El seed ejecuta el flujo real con clientes de Ollama falsos, por lo que la demo del historial
funciona en un equipo sin el modelo instalado.

## Pruebas

Las pruebas automáticas nunca llaman a Ollama real, a Cloudinary ni a internet.

```powershell
uv run pytest -q
```

Cubren, entre otras cosas: extracción de JSON e imágenes, recorrido recursivo con
JSONPath, detección determinista, enmascarado, cálculo de riesgo, contratos estrictos y timeouts,
política
ALLOWED/BLOCKED, que un prompt bloqueado nunca llega al generador, que el generador exige una
autorización válida, que un fallo inesperado nunca deja una ejecución en `RUNNING`, path traversal,
SSRF, MIME y JSON inválidos, paginación, ausencia de conflictos de rutas y ausencia de secretos en
el esquema público.

## Arquitectura

```text
app/
  core/            settings, base de datos, composition root
  shared/          masking de texto, base SQLAlchemy, unit of work, transporte Ollama, prompts
  documents/       domain / application / infrastructure / interfaces
  analysis/        domain / application / infrastructure / interfaces
  decision/        domain / application / infrastructure / interfaces
```

Los cuatro usos de Ollama están separados en clientes, contratos y prompts de sistema distintos:
`OllamaSensitiveContentDiscoveryClientImpl` (clasifica contenido local sin devolver valores),
`OllamaVisionExtractionClientImpl` (transcripción visual JSON),
`OllamaSecurityAnalysisClientImpl` (clasificación JSON estricta, temperature 0) y
`OllamaAnswerGenerationClientImpl` (respuesta en prosa, exige `GenerationAuthorization`).

## Limitaciones

- La precisión contextual depende de `gemma3:4b`. El evaluador de seguridad admite un reintento
  correctivo ante una respuesta que no cumple el contrato; si sigue siendo inválida, la ejecución
  falla y la consulta queda bloqueada.
- `gemma3:4b` extrae correctamente los datos del documento permitido, pero **no cuenta ni suma de
  forma fiable**. Una pregunta de tipo "cuántos elementos hay" puede devolver una cifra incorrecta.
  Un modelo mayor corrige esto sin tocar el código.
- Los eventos de dominio se publican en memoria, siguiendo la convención existente.
- Solo se admiten JSON, PNG y JPEG. PDF, DOCX, XLSX y los formatos heredados quedan fuera del
  alcance, igual que el OCR masivo y el análisis forense de archivos.
- Con `DOCUMENT_STORAGE_BACKEND=cloudinary` el archivo se sube a Cloudinary antes de la revisión y
  en PostgreSQL solo queda la URL `https://res.cloudinary.com/...`, nunca los bytes. Usa `local` si
  el contenido no puede salir de la máquina.
- La transcripción visual es una interpretación del modelo local, no OCR certificado; después se
  somete igualmente al detector determinista y al clasificador de seguridad obligatorio.
