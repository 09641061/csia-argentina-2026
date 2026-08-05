from fastapi import FastAPI

from app.core.database import initialize_database
from app.analysis.interfaces.rest.controllers.document_analysis_router import router as analysis_router
from app.documents.interfaces.rest.controllers.document_router import router as documents_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sentinel AI Guard",
        version="0.1.0",
        description="Document intake and document analysis bounded contexts for Sentinel AI Guard.",
    )

    app.include_router(documents_router)
    app.include_router(analysis_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await initialize_database()

    return app


app = create_app()
