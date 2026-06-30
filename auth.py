from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import Team, TutorAccount

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_current_team(request: Request, db: Session = Depends(get_db)) -> Team:
    team_id = request.session.get("team_id")
    if not team_id:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        request.session.clear()
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return team


def get_current_team_optional(request: Request, db: Session = Depends(get_db)):
    team_id = request.session.get("team_id")
    if not team_id:
        return None
    return db.query(Team).filter(Team.id == team_id).first()


def get_current_tutor(request: Request, db: Session = Depends(get_db)) -> TutorAccount:
    tutor_id = request.session.get("tutor_id")
    if not tutor_id:
        raise HTTPException(status_code=302, headers={"Location": "/tutor/login"})
    tutor = db.query(TutorAccount).filter(TutorAccount.id == tutor_id).first()
    if not tutor:
        request.session.clear()
        raise HTTPException(status_code=302, headers={"Location": "/tutor/login"})
    return tutor


def require_admin(request: Request, db: Session = Depends(get_db)) -> TutorAccount:
    tutor = get_current_tutor(request, db)
    if tutor.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return tutor
