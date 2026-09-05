from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.transactions import router as transactions_router
from app.routes.alerts import router as alerts_router
from app.routes.metrics import router as metrics_router
from app.routes.analytics import router as analytics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Sentinel is a cost-aware payment-transaction fraud triage system. "
        "It ranks alerts by expected loss, explains evidence to analysts, "
        "exposes linked-entity risk, and routes uncertain cases to human review."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Next.js frontend and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(transactions_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(metrics_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "modelVersion": settings.MODEL_VERSION,
        "pipelineStatus": "operational",
    }
