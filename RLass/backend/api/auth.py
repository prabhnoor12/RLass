from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.auth_service import issue_token, validate_token, revoke_token, cleanup_expired_tokens
from ..schemas.auth import AuthTokenCreate
from ..database import get_db

router = APIRouter()

@router.post("/issue")
def issue_auth_token(token_in: AuthTokenCreate, db: Session = Depends(get_db)):
	token = issue_token(db, token_in)
	if not token:
		raise HTTPException(status_code=400, detail="Failed to issue token")
	return token

@router.get("/validate/{token}")
def validate_auth_token(token: str, check_expiry: bool = True, db: Session = Depends(get_db)):
	result = validate_token(db, token, check_expiry)
	if not result:
		raise HTTPException(status_code=401, detail="Invalid or expired token")
	return result

@router.post("/revoke/{token}")
def revoke_auth_token(token: str, db: Session = Depends(get_db)):
	result = revoke_token(db, token)
	if not result:
		raise HTTPException(status_code=404, detail="Token not found or already revoked")
	return result

@router.delete("/cleanup-expired")
def cleanup_expired(db: Session = Depends(get_db)):
	deleted = cleanup_expired_tokens(db)
	return {"deleted": deleted}
