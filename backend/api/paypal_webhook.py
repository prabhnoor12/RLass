from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..crud.rate_limit import list_rate_limits, get_rate_limit, create_rate_limit
from ..crud.api_key import get_api_key
from ..models.rate_limit import RateLimitConfig
from ..database import get_db

router = APIRouter()

@router.post("/webhook/paypal", status_code=200)
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    # Example: extract customer_id and quota from PayPal webhook payload
    customer_id = data.get("custom") or data.get("customer_id")
    quota = data.get("quota") or data.get("amount")
    api_key = data.get("api_key")  # Optional: if you want to associate with a specific API key
    if not customer_id or not quota:
        raise HTTPException(status_code=400, detail="Missing customer_id or quota in webhook payload")
    # Find all rate limits for this customer and update quota (limit)
    rate_limits = list_rate_limits(db, customer_id=customer_id)
    if not rate_limits:
        # Optionally, create a new rate limit config for this customer
        if api_key:
            create_rate_limit(db, RateLimitConfig(
                api_key=api_key,
                customer_id=customer_id,
                endpoint=None,
                limit=int(quota),
                period_seconds=30*24*3600  # e.g., 30 days
            ))
        else:
            raise HTTPException(status_code=404, detail="No rate limit found for customer and no api_key provided")
    else:
        for rl in rate_limits:
            rl.limit += int(quota)
        db.commit()
    return {"status": "success"}
