import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.api.tools import router as tools_router
from app.api.tasks import router as tasks_router
from app.api.desktop import router as desktop_router
from app.api.activity import router as activity_router
from app.api.settings import router as settings_router
from app.api.auth import router as auth_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jarvis.backend")

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing J.A.R.V.I.S. Core Subsystems...")
    await init_db()
    logger.info(f"Subsystems initialized. J.A.R.V.I.S. online. Host: {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    yield
    logger.info("J.A.R.V.I.S. Core Subsystems shutting down.")


app = FastAPI(
    title="J.A.R.V.I.S. AI Backend",
    description="Intelligent Conversational Core, Tool Orchestrator & Memory Manager",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred in J.A.R.V.I.S. subsystems.", "error": str(exc)}
    )

# Include Routers under /api
api_prefix = "/api"
app.include_router(health_router, prefix=api_prefix)
app.include_router(chat_router, prefix=api_prefix)
app.include_router(memory_router, prefix=api_prefix)
app.include_router(tools_router, prefix=api_prefix)
app.include_router(tasks_router, prefix=api_prefix)
app.include_router(desktop_router, prefix=api_prefix)
app.include_router(activity_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)

# Mount frontend assets if built
if FRONTEND_ASSETS.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="assets")


@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    # Serve the interactive J.A.R.V.I.S. Command Center UI if available
    if FRONTEND_INDEX.is_file() and "text/html" in accept:
        return FileResponse(str(FRONTEND_INDEX))

    return {
        "name": settings.ASSISTANT_NAME,
        "status": "online",
        "documentation": "/docs",
        "health": "/api/health"
    }


# Catch-all route to support browser SPA navigation if not matching /api
@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    if not full_path.startswith("api") and not full_path.startswith("docs") and not full_path.startswith("openapi"):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        if FRONTEND_INDEX.is_file():
            return FileResponse(str(FRONTEND_INDEX))
    return JSONResponse(status_code=404, content={"detail": f"Not found: /{full_path}"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
