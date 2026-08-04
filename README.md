# Sentinel AI Guard

Backend FastAPI para registrar documentos JSON y analizarlos localmente antes de utilizarlos con una IA. El bounded context **Documents** conserva la carga y referencia del archivo; **Analytics** obtiene esa referencia mediante el contrato de consulta existente, detecta datos sensibles, consulta Ollama con contexto sanitizado, calcula el riesgo y conserva un historial seguro.

## Alcance actual

- Solo documentos con MIME `application/json` y raiz objeto o arreglo.
- Deteccion determinista estructural con JSONPath.
- Interpretacion contextual mediante Ollama local.
- Riesgos `low`, `medium`, `high` y `critical`.
- Historial de ejecuciones y estados `running`, `completed` y `failed`.
- Hallazgos enmascarados y una copia JSON sanitizada independiente.
- API REST documentada en Swagger.
- No incluye autenticacion, frontend, PDF, DOCX, OCR, Audit ni decisiones `ALLOW/WARN/SANITIZE/BLOCK`.

## Flujo de Analytics

```text
document_id
  -> contrato de consulta de Documents
  -> descarga del JSON registrado
  -> parseo y recorrido estructural
  -> deteccion determinista + JSONPath
  -> enmascarado y JSON sanitizado
  -> resumen estructural (inicio, centro y final)
  -> Ollama con contexto seguro
  -> validacion estricta de la respuesta
  -> calculo final de riesgo
  -> persistencia historica + evento de dominio
```

El JSON original no se envia completo a Ollama. El modelo recibe nombre, MIME, tamano, estructura, claves principales, conteos, categorias, JSONPaths, evidencias enmascaradas y muestras tomadas de una version ya sanitizada.

## Requisitos

- Windows PowerShell, Linux o macOS.
- `uv`.
- Python 3.11, administrado por `uv`.
- PostgreSQL para ejecutar la API principal.
- Ollama y el modelo configurado.
- Credenciales de Cloudinary solo para subir documentos mediante Documents.

## Instalacion

```powershell
uv python install 3.11
uv python pin 3.11
uv sync --extra dev
```

Si PowerShell no reconoce `uv` despues de instalarlo con `pip`, cierra y abre la terminal o agrega la carpeta `Scripts` de Python al `PATH`. En este repositorio tambien se puede invocar temporalmente con la ruta completa de `uv.exe`.

Crea un `.env` usando [.env.example](.env.example) como referencia. No subas `.env` al repositorio.

## Variables de entorno

| Variable | Uso | Valor de desarrollo sugerido |
| --- | --- | --- |
| `DATABASE_URL` | Conexion SQLAlchemy asincrona | `postgresql+asyncpg://postgres:change-me@localhost:5432/sentinel_ai_guard` |
| `CLOUDINARY_CLOUD_NAME` | Cuenta para Documents | Valor de tu cuenta |
| `CLOUDINARY_API_KEY` | API key para Documents | Valor de tu cuenta |
| `CLOUDINARY_API_SECRET` | Secreto para Documents | Valor de tu cuenta |
| `OLLAMA_BASE_URL` | API HTTP local de Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo contextual | `llama3.2:3b` |
| `OLLAMA_REQUEST_TIMEOUT_SECONDS` | Timeout total | `180` |
| `OLLAMA_CONTEXT_TOKENS` | Ventana de contexto | `8192` |
| `OLLAMA_MAX_OUTPUT_TOKENS` | Limite de respuesta | `300` |

## Ollama

Instala Ollama desde su instalador oficial y descarga el modelo:

```powershell
ollama pull llama3.2:3b
ollama serve
```

En algunas instalaciones de Windows, Ollama ya se ejecuta en segundo plano y `ollama serve` indicara que el puerto esta ocupado; eso significa que el servicio ya esta disponible. Ejecutar solamente `ollama` abre el selector interactivo de modelos, no es un error.

Puedes verificar el modelo con:

```powershell
ollama list
ollama run llama3.2:3b
```

## Ejecutar el backend

Con PostgreSQL, Ollama y la configuracion disponibles:

```powershell
uv run uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

El arranque ejecuta una migracion idempotente limitada a la tabla de Analytics. Si existe la tabla parcial anterior, conserva sus filas, habilita historial y elimina evidencia heredada sin enmascarar.

## Endpoints

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| `POST` | `/api/v1/analysis/{document_id}` | Ejecuta y persiste un analisis (`201`) |
| `GET` | `/api/v1/analysis/{document_id}` | Obtiene la ejecucion mas reciente del documento |
| `GET` | `/api/v1/analysis/runs/{analysis_id}` | Obtiene una ejecucion historica |
| `GET` | `/api/v1/analysis/runs/{analysis_id}/findings` | Devuelve hallazgos enmascarados |
| `GET` | `/api/v1/analysis/runs/{analysis_id}/sanitized` | Devuelve la representacion JSON sanitizada |
| `GET` | `/api/v1/analysis?page=1&page_size=20` | Lista el historial paginado |

Ejecutar un analisis registrado:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/analysis/1
```

Consultar el resultado:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/analysis/1
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/analysis/runs/1/findings
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/analysis/runs/1/sanitized
```

Respuesta abreviada:

```json
{
  "id": 3,
  "document_id": 8,
  "status": "completed",
  "risk_level": "high",
  "secrets_risk": "high",
  "personal_data_risk": "medium",
  "confidence": "high",
  "tampering_suspected": false,
  "data_categories": ["api_key", "email"],
  "estimated_subjects": "1-5",
  "findings": [
    {
      "finding_id": "f1",
      "finding_type": "api_key",
      "json_path": "$.integration.api_key",
      "evidence": "sk-p*******************************f5Ja",
      "detection_method": "recognized_credential_pattern",
      "confidence": "high",
      "occurrences": 1,
      "is_placeholder": false
    }
  ]
}
```

La API no devuelve `source_document_url`, contrasenas, tarjetas, CVV, tokens ni claves completas.

## Datasets sinteticos

`samples/` contiene diez escenarios y [expected-results.json](samples/expected-results.json) define riesgos, tipos, categorias y conteos minimos esperados.

```powershell
uv run python scripts/generate_analytics_samples.py
```

Los escenarios son: inventario limpio, exportacion de clientes, volcado de credenciales, logs de autenticacion, logs de API Gateway, logs de pagos, datos personales incidentales, placeholders, prompt injection y hallazgo ubicado al final de un JSON grande.

Todos los nombres, identificadores, tarjetas y credenciales con forma realista son datos sinteticos de prueba y no son operativos.

## Seed local

El seed permite demostrar Analytics sin Cloudinary, PostgreSQL ni Ollama real. Crea `storage/analytics-demo.db`, registra los diez documentos directamente y ejecuta para cada uno:

```text
extraccion -> deteccion -> Ollama falso -> riesgo -> persistencia
```

```powershell
uv run --extra dev python scripts/seed_analytics_samples.py
```

El script es idempotente para los nombres de archivo ya registrados. Tambien acepta otra conexion asincrona:

```powershell
uv run --extra dev python scripts/seed_analytics_samples.py --database-url "postgresql+asyncpg://postgres:change-me@localhost:5432/sentinel_ai_guard"
```

## Pruebas

Las pruebas automatizadas nunca llaman a Ollama real.

```powershell
uv run --extra dev pytest -q
```

La suite cubre recorrido recursivo, JSONPath, email, nombre, telefono, identificadores, contrasenas, API keys, AWS keys, tokens, Luhn, CVV, claves privadas, placeholders, prompt injection, enmascarado, sanitizacion, resumen distribuido, riesgo, contrato estricto y timeout de Ollama, persistencia historica, paginacion, API y controles de fuga.

## Arquitectura

```text
app/analysis/
  domain/                         entidades, value objects, eventos y contratos
  application/internal/          orquestacion, deteccion, resumen, riesgo y sanitizacion
  infrastructure/                HTTP/Ollama, descarga y SQLAlchemy asincrono
  interfaces/rest/               recursos Pydantic y rutas FastAPI
```

La integracion con Documents usa `DocumentQueryService` y transforma solo los datos requeridos a `SourceDocumentReference`. Analytics no importa modelos SQLAlchemy internos de Documents para su logica de aplicacion y no modifica el documento original.

## Limitaciones y pendientes

- Audit debe consumir posteriormente `DocumentAnalysisStartedEvent`, `DocumentAnalysisCompletedEvent` y `DocumentAnalysisFailedEvent`.
- Los eventos se publican actualmente en memoria, siguiendo la convencion existente; no hay Kafka ni RabbitMQ.
- La decision final de permitir, advertir, sanitizar o bloquear pertenece a otro bounded context.
- La precision contextual depende del modelo local configurado, pero ningun fallo del modelo se convierte en riesgo bajo.
- La deteccion determinista reduce falsos positivos con contexto, Luhn y placeholders, pero debe evolucionar con nuevas familias de secretos y normativas.
