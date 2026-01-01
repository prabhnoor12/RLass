from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from .api.api_key import router as api_key
from .api.usage_log import router as usage_log
from .api.stats import router as stats
from .api.settings import router as settings
from .api.plan import router as plan
from .api.maintenance import router as maintenance
from .api.authorization import router as authorization
from .api.user import router as user
from .api.rate_limit import router as rate_limit
from .api.audit_log import router as audit_log
from .api import paypal_webhook
from .api.usage_dashboard import router as usage_dashboard_router
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
app.include_router(api_key, prefix="/api-key", tags=["API Key"])
app.include_router(usage_log, prefix="/usage-log", tags=["Usage Log"])
app.include_router(stats, prefix="/stats", tags=["Stats"])
app.include_router(settings, prefix="/settings", tags=["Settings"])
app.include_router(plan, prefix="/plan", tags=["Plan"])
app.include_router(maintenance, prefix="/maintenance", tags=["Maintenance"])
app.include_router(authorization, prefix="/authorization", tags=["Authorization"])
app.include_router(user, prefix="/user", tags=["User"])
app.include_router(rate_limit, prefix="/rate-limit", tags=["Rate Limit"])
app.include_router(audit_log, prefix="/audit-log", tags=["Audit Log"])
app.include_router(paypal_webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(usage_dashboard_router, prefix="/usage-dashboard", tags=["Usage Dashboard"])

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
