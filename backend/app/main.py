import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analysis.interfaces.rest.controllers.security_analysis_router import (
    router as analysis_router,
)
from app.chat.interfaces.rest.controllers.chat_router import router as chat_router
from app.core.database import initialize_database
from app.core.settings import get_settings
from app.decision.interfaces.rest.controllers.secure_query_router import (
    router as secure_query_router,
)
from app.iam.interfaces.rest.controllers.authentication_router import (
    router as authentication_router,
)
from app.shared.interfaces.rest.health_router import router as health_router

logger = logging.getLogger(__name__)

DESCRIPTION = """
Sentinel AI Guard es un portal seguro de acceso a una IA local.

Cada mensaje de una conversación se revisa antes de que el modelo pueda responder.
Solo los mensajes permitidos llegan al generador de respuestas.

Contextos delimitados:

* **Analysis** detecta datos sensibles en cada mensaje y exige una evaluación contextual
  al modelo local de seguridad.
* **Decision & Audit** aplica la política ALLOWED/BLOCKED, ejecuta la generación solo si
  el contenido fue permitido y conserva el historial explicable.
* **IAM** registra usuarios locales, protege contraseñas con Argon2 y valida JWT Bearer.
* **Chat** administra conversaciones y mensajes, y consume las capacidades de seguridad
  mediante ACL.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Prepare the schema before serving.

    A database failure here stops the process on purpose: an API that answers
    while it cannot write the audit trail would be worse than one that is down.
    """

    del app
    await initialize_database()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Sentinel AI Guard",
        version="1.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Authorization"],
    )

    app.include_router(health_router)
    app.include_router(authentication_router)
    app.include_router(chat_router)
    app.include_router(analysis_router)
    app.include_router(secure_query_router)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        """Never let an internal message, path or stack trace reach a client."""

        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        del error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Ocurrió un error inesperado en el servidor."},
        )

    return app


app = create_app()
