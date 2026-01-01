
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.user_manager import create_user, get_user, update_user
from ..schemas.user import UserCreate, UserRead
from ..database import get_db
from typing import Optional

router = APIRouter()


@router.post("/create", response_model=UserRead)
def create(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.get("/get/{user_id}", response_model=UserRead)
def get(user_id: str, db: Session = Depends(get_db)):
    return get_user(db, user_id)


@router.put("/update/{user_id}", response_model=UserRead)
def update(user_id: str, email: Optional[str] = None, password: Optional[str] = None, is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    return update_user(db, user_id, email, password, is_active)
