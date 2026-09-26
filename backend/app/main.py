"""
ThreatPro - RAKSHAK Intelligence Grid
FastAPI Application Entry Point with CORS, WebSocket support, and startup seeding.
"""

import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from .config import settings, parse_cors_origins
from .database import init_db, reseed_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("trishul-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database and seed data on startup."""
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"  Starting RAKSHAK Intelligence Grid...")
    logger.info("=" * 60)

    # Initialize database tables
    logger.info("Initializing database...")
    init_db()

    # Seed demo data
    logger.info("Seeding demonstration data...")
    try:
        reseed_db()
        logger.info("Database seeded successfully!")
    except Exception as e:
        logger.warning(f"Seeding warning (non-critical): {e}")

    logger.info(f"Server running at http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API Docs at http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("Ready for interception commands.")
    yield
    logger.info("ThreatPro shutting down.")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ThreatPro - National Digital Public Safety Intelligence Grid
    
    ## Modules
    - **Interceptor**: Real-time digital arrest call detection & threat alerting
    - **Sentinel**: Counterfeit currency forensics with multi-stage validation
    - **Graph Intelligence**: Fraud graph analytics & mule network detection
    - **Geospatial**: Cybercrime hotspot mapping & patrol route optimization
    
    ## WebSocket
    - `/api/v1/interceptor/ws/stream` - Live interception streaming
    """,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "operational",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "modules": [
            "interceptor",
            "sentinel",
            "graph_intel",
            "geospatial",
        ],
        "database": "sqlite",
        "neo4j_enabled": settings.NEO4J_ENABLED,
    }


# ============================================================================
# Register Routers
# ============================================================================

from .routers.interceptor import router as interceptor_router
from .routers.sentinel import router as sentinel_router
from .routers.graph_intel import router as graph_intel_router
from .routers.geospatial import router as geospatial_router

app.include_router(interceptor_router)
app.include_router(sentinel_router)
app.include_router(graph_intel_router)
app.include_router(geospatial_router)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )