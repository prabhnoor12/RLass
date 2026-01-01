from sqlalchemy.orm import Session
from ..models.authorization import Role, UserRole
from ..schemas.authorization import RoleCreate, UserRoleCreate
from typing import Optional, List

def create_role(db: Session, role_in: RoleCreate) -> Role:
    db_role = Role(**role_in.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()

def list_roles(db: Session) -> List[Role]:
    return db.query(Role).all()

def assign_role_to_user(db: Session, user_role_in: UserRoleCreate) -> UserRole:
    db_user_role = UserRole(**user_role_in.dict())
    db.add(db_user_role)
    db.commit()
    return db_user_role

def get_user_roles(db: Session, user_id: int) -> List[UserRole]:
    return db.query(UserRole).filter(UserRole.user_id == user_id).all()
