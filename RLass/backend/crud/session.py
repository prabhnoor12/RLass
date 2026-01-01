from sqlalchemy.orm import Session as DBSession
from ..models.session import Session
from ..schemas.session import SessionCreate
from typing import Optional, List
import datetime

def create_session(db: DBSession, session_in: SessionCreate) -> Session:
    db_session = Session(**session_in.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_token(db: DBSession, session_token: str) -> Optional[Session]:
    return db.query(Session).filter(Session.session_token == session_token).first()

def list_sessions(db: DBSession, user_id: Optional[int] = None) -> List[Session]:
    q = db.query(Session)
    if user_id:
        q = q.filter(Session.user_id == user_id)
    return q.all()

def deactivate_session(db: DBSession, session_token: str) -> Optional[Session]:
    db_session = get_session_by_token(db, session_token)
    if db_session:
        db_session.is_active = False
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_expired_sessions(db: DBSession) -> int:
    now = datetime.datetime.now(datetime.UTC)
    deleted = db.query(Session).filter(Session.expires_at < now).delete()
    db.commit()
    return deleted
