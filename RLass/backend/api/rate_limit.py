
from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.check import CheckRequest, CheckResponse
from ..schemas.rate_limit import RateLimitConfigCreate, RateLimitConfigRead
from ..services.rate_limiter import check_and_log_rate_limit, summarize_usage_for_api_key, get_rate_limit_config
from ..crud import rate_limit as crud_rate_limit
from ..utils.response import success_response, error_response
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter()

@router.post("/check", response_model=CheckResponse)
def check_rate_limit_endpoint(request: CheckRequest, db: Session = Depends(get_db)):
    # Use dynamic config from DB
    config = get_rate_limit_config(db, request.api_key, request.endpoint)
    if not config:
        return error_response(message="No rate limit config found.", status_code=status.HTTP_404_NOT_FOUND)
    allowed, remaining, reset = check_and_log_rate_limit(db, request.api_key, request.identifier, request.endpoint)
    if allowed:
        return success_response({
            "allowed": True,
            "remaining": remaining,
            "reset": reset
        })
    else:
        return error_response(
            message="Rate limit exceeded.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            data={
                "allowed": False,
                "remaining": remaining,
                "reset": reset
            }
        )

@router.get("/usage/summary/{api_key}")
def get_usage_summary(api_key: str, endpoint: str = None, db: Session = Depends(get_db)):
    """
    Analytics: Get usage summary for an API key (optionally for an endpoint).
    """
    summary = summarize_usage_for_api_key(db, api_key, endpoint)
    return success_response(summary)

@router.get("/rate-limit/config/{api_key}", response_model=list[RateLimitConfigRead])
def get_rate_limit_configs(api_key: str, db: Session = Depends(get_db)):
    """
    Get all rate limit configs for an API key.
    """
    configs = crud_rate_limit.list_rate_limits(db, api_key)
    return configs

@router.put("/rate-limit/config/{api_key}", response_model=RateLimitConfigRead)
def update_rate_limit_config(api_key: str, endpoint: str, limit: int, period_seconds: int, db: Session = Depends(get_db)):
    """
    Dynamic adjustment: Update rate limit config for an API key and endpoint.
    """
    config = crud_rate_limit.update_rate_limit(db, api_key, endpoint, limit, period_seconds)
    if not config:
        raise HTTPException(status_code=404, detail="Rate limit config not found.")
    return config
