"""
Main FastAPI application entry point — mirrors Forehand's src/index.ts.

Forehand pattern:
    const app = new Elysia()
        .use(logger())
        .use(cors(...))
        .use(apiV1)
        .listen(port)

Our equivalent:
    app = FastAPI(...)
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(auth_router, prefix="/v1")
    # run via: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.centres import router as centres_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.utils.response import send_response

# ---------------------------------------------------------------------------
# Lifespan — runs on startup/shutdown (replaces deprecated @app.on_event)
# Used to create tables in dev (Alembic handles prod migrations)
# ---------------------------------------------------------------------------
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so Base knows about them before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified / created.")
    
    # Initialize caching (Phase 10 Bonus)
    # Try Redis first (for Docker env), fallback to InMemory if running locally without Redis
    try:
        redis = aioredis.from_url("redis://redis:6379", encoding="utf8", decode_responses=True)
        # Quick ping to test connection
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="eve-cache")
        print("🚀 Cache initialized with Redis backend.")
    except Exception:
        FastAPICache.init(InMemoryBackend(), prefix="eve-cache")
        print("🚀 Cache initialized with InMemory fallback (Redis not found).")
        
    yield
    print("🛑 Shutting down.")


# ---------------------------------------------------------------------------
# App instance — mirrors Forehand's new Elysia() with metadata for Swagger UI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="EVE Healthcare API",
    description=(
        "Backend service for diagnostic test bookings and simulated payments. "
        "Built for the EVE Healthcare SDE Intern assignment."
    ),
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc UI
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — mirrors Forehand's cors() middleware with origin allowlist
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler — mirrors Forehand's .onError() block
# Returns a consistent { success, message } envelope for unhandled errors
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=send_response(success=False, message="Internal Server Error"),
    )


# ---------------------------------------------------------------------------
# Routers — mirrors Forehand's apiV1.group("v1", ...) with .use(userRoutes)
# ---------------------------------------------------------------------------
API_PREFIX = "/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(centres_router, prefix=API_PREFIX)
app.include_router(bookings_router, prefix=API_PREFIX)
app.include_router(payments_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health check — mirrors Forehand's .get("/", () => "Hello World")
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    return send_response(success=True, message="EVE Healthcare API is running.")

@app.get("/health", tags=["Health"])
def explicit_health_check():
    """Explicit health check endpoint for Uptime Robot."""
    return send_response(success=True, message="EVE Healthcare API is healthy.")
