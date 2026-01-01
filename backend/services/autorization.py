
from sqlalchemy.orm import Session
from typing import Optional, List
from ..crud import authorization as crud_authorization
from ..models.authorization import Role, UserRole
from ..schemas.authorization import RoleCreate, RoleRead, UserRoleCreate, UserRoleRead
import logging

logger = logging.getLogger("authorization_service")

def create_role_with_check(db: Session, role_in: RoleCreate) -> Role:
	"""
	Create a new role if it does not already exist.
	Raises ValueError if role name already exists.
	"""
	existing = crud_authorization.get_role_by_name(db, role_in.name)
	if existing:
		logger.warning(f"Role '{role_in.name}' already exists.")
		raise ValueError(f"Role '{role_in.name}' already exists.")
	logger.info(f"Creating role: {role_in.name}")
	return crud_authorization.create_role(db, role_in)

def get_role(db: Session, name: str) -> Optional[Role]:
	"""
	Retrieve a role by name.
	"""
	return crud_authorization.get_role_by_name(db, name)

def list_all_roles(db: Session) -> List[Role]:
	"""
	List all roles in the system.
	"""
	return crud_authorization.list_roles(db)

def assign_role_to_user_with_check(db: Session, user_role_in: UserRoleCreate) -> UserRole:
	"""
	Assign a role to a user if not already assigned.
	Raises ValueError if already assigned.
	"""
	existing_roles = crud_authorization.get_user_roles(db, user_role_in.user_id)
	for ur in existing_roles:
		if ur.role_id == user_role_in.role_id:
			logger.warning(f"User {user_role_in.user_id} already has role {user_role_in.role_id}.")
			raise ValueError(f"User {user_role_in.user_id} already has role {user_role_in.role_id}.")
	logger.info(f"Assigning role {user_role_in.role_id} to user {user_role_in.user_id}")
	return crud_authorization.assign_role_to_user(db, user_role_in)

def get_roles_for_user(db: Session, user_id: int) -> List[UserRole]:
	"""
	Get all roles assigned to a user.
	"""
	return crud_authorization.get_user_roles(db, user_id)

def user_has_role(db: Session, user_id: int, role_name: str) -> bool:
	"""
	Check if a user has a specific role by name.
	"""
	roles = crud_authorization.get_user_roles(db, user_id)
	for ur in roles:
		role = db.query(Role).filter(Role.id == ur.role_id).first()
		if role and role.name == role_name:
			return True
	return False

def remove_role_from_user(db: Session, user_id: int, role_id: int) -> bool:
	"""
	Remove a role from a user. Returns True if removed, False if not found.
	"""
	user_roles = crud_authorization.get_user_roles(db, user_id)
	for ur in user_roles:
		if ur.role_id == role_id:
			db.delete(ur)
			db.commit()
			logger.info(f"Removed role {role_id} from user {user_id}")
			return True
	logger.warning(f"Role {role_id} not found for user {user_id}")
	return False
