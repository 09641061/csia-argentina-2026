# Sentinel AI Guard — Backend MVP

API FastAPI para acceso seguro a una IA local. El MVP acepta consultas de texto: analiza el prompt, aplica la política `ALLOWED/BLOCKED`, genera una respuesta solo cuando está permitido y conserva una auditoría enmascarada.

## Bounded Contexts

- **IAM:** registro, login, Argon2 y JWT Bearer.
- **Analysis:** detección determinista y evaluación contextual de prompts.
- **Decision & Audit:** política de autorización y auditoría explicable.
- **Chat:** conversaciones y mensajes protegidos mediante la ACL de Decision.

La carga y el análisis de documentos no forman parte del alcance del MVP.

## Requisitos

- Python 3.11 o superior.
- PostgreSQL.
- Ollama con el modelo configurado para análisis, descubrimiento y generación.
- `uv` para instalar y ejecutar el proyecto.

## Configuración y ejecución

```powershell
Copy-Item .env.example .env
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

OpenAPI queda disponible en `http://127.0.0.1:8000/docs`.

## Endpoints principales

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/prompts/analyses`
- `GET /api/v1/analyses`
- `GET /api/v1/analyses/{analysis_id}`
- `POST /api/v1/secure-queries`
- `GET /api/v1/interactions`
- `POST /api/v1/chat/conversations`
- `POST /api/v1/chat/conversations/{conversation_id}/messages`
- `GET /api/v1/health`

Los endpoints protegidos requieren `Authorization: Bearer <token>`.

## Pruebas

```powershell
uv run pytest
```
