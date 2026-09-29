from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from backend.app.api.v1.analyze import router as analyze_router
from backend.app.api.v1.artifacts import router as artifacts_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.results import router as results_router
from backend.app.core.config import settings
from backend.app.core.errors import ClaimGuardException
from backend.app.core.logging import logger, setup_logging
from backend.app.db.database import init_db

# Path to built frontend (populated by build.sh)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Lucen AI — Evidence Intelligence Engine v%s", settings.VERSION)
    init_db()
    yield
    logger.info("Shutting down Lucen AI engine.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Lucen AI — Evidence Intelligence for Insurance Claims",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for ClaimGuardException
@app.exception_handler(ClaimGuardException)
async def claimguard_exception_handler(request: Request, exc: ClaimGuardException):
    return exc.to_response()


# Global Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {},
            }
        },
    )


# Include API v1 routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(analyze_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(results_router, prefix=settings.API_V1_STR)
app.include_router(artifacts_router, prefix=settings.API_V1_STR)


# Serve frontend static files in production
if FRONTEND_DIST.exists():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{path:path}")
    async def serve_spa(request: Request, path: str):
        # Don't catch API or docs routes
        if path.startswith("api/") or path in ("docs", "redoc", "openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        # Try to serve the exact file first (favicon, icons, etc.)
        file_path = FRONTEND_DIST / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "api_v1": settings.API_V1_STR,
            "note": "Frontend not built. Run 'npm run build' in frontend/ directory.",
        }
