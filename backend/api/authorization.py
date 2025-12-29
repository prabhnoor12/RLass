from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.autorization import (
    create_role_with_check, get_role, list_all_roles, assign_role_to_user_with_check, get_roles_for_user, user_has_role, remove_role_from_user
)
from ..schemas.authorization import RoleCreate, UserRoleCreate
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.post("/role/create")
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return create_role_with_check(db, role)

@router.get("/role/get")
def get_role_by_name(name: str, db: Session = Depends(get_db)):
    return get_role(db, name)

@router.get("/role/list")
def list_roles(db: Session = Depends(get_db)):
    return list_all_roles(db)

@router.post("/user-role/assign")
def assign_role(user_role: UserRoleCreate, db: Session = Depends(get_db)):
    return assign_role_to_user_with_check(db, user_role)

@router.get("/user-role/list/{user_id}")
def get_user_roles_api(user_id: int, db: Session = Depends(get_db)):
    return get_roles_for_user(db, user_id)

@router.get("/user-role/has-role")
def has_role(user_id: int, role_name: str, db: Session = Depends(get_db)):
    return {"has_role": user_has_role(db, user_id, role_name)}

@router.delete("/user-role/remove")
def remove_role(user_id: int, role_id: int, db: Session = Depends(get_db)):
    return {"removed": remove_role_from_user(db, user_id, role_id)}
