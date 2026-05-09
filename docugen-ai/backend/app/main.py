import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import ai, auth, reports, templates
from app.core.config import settings
from app.db.session import Base, engine
from app.middleware.error_handler import register_error_handlers
from app.middleware.jwt_middleware import JWTMiddleware
from app.models import ImageAsset, TemplateProfile, User

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        description="Starter API for the DocuGen AI document automation platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(JWTMiddleware)

    register_error_handlers(app)
    app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Auth"])
    app.include_router(reports.router, prefix=f"{settings.API_PREFIX}/reports", tags=["Reports"])
    app.include_router(templates.router, prefix=f"{settings.API_PREFIX}/templates", tags=["Templates"])
    app.include_router(ai.router, prefix=f"{settings.API_PREFIX}/ai", tags=["AI"])

    @app.on_event("startup")
    def initialize_database() -> None:
        try:
            Base.metadata.create_all(bind=engine)
        except SQLAlchemyError as exc:
            logger.warning("Database initialization skipped: %s", exc)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.PROJECT_NAME}

    return app


app = create_app()
