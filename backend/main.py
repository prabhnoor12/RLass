
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from .api import api_key, usage_log, stats, settings, plan, maintenance, authorization, user, rate_limit
import logging

app = FastAPI(
    title="RLaaS Backend API",
    description="A robust, modular API for RLaaS platform, including rate limiting, analytics, user management, and more.",
    version="1.0.0",
    contact={
        "name": "RLaaS Team",
        "email": "support@rlaas.com"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers for each API module
app.include_router(api_key.router, prefix="/api-key", tags=["API Key"])
app.include_router(usage_log.router, prefix="/usage-log", tags=["Usage Log"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(plan.router, prefix="/plan", tags=["Plan"])
app.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
app.include_router(authorization.router, prefix="/authorization", tags=["Authorization"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(rate_limit.router, prefix="/rate-limit", tags=["Rate Limit"])

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Custom exception handler for 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})

# Custom OpenAPI schema (optional branding)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://yourdomain.com/logo.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi

# Root endpoint with info
@app.get("/")
def read_root():
    return {
        "message": "Welcome to RLaaS Backend API!",
        "docs": "/docs",
        "health": "/health",
        "version": app.version
    }