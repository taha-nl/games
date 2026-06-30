from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_team, get_current_tutor, hash_password, verify_password
from database import get_db
from models import Achievement, Challenge, Event, Submission, SubmissionStatus, Team, TeamCard

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    team_id = request.session.get("team_id")
    if team_id:
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    team_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team or not verify_password(password, team.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid team name or password"},
            status_code=401,
        )
    request.session["team_id"] = team.id
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/tutor/login", response_class=HTMLResponse)
async def tutor_login_page(request: Request):
    return templates.TemplateResponse("tutor/login.html", {"request": request, "error": None})


@router.post("/tutor/login", response_class=HTMLResponse)
async def tutor_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    from models import TutorAccount
    tutor = db.query(TutorAccount).filter(TutorAccount.username == username).first()
    if not tutor or not verify_password(password, tutor.password_hash):
        return templates.TemplateResponse(
            "tutor/login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401,
        )
    request.session["tutor_id"] = tutor.id
    request.session["tutor_role"] = tutor.role.value
    return RedirectResponse("/tutor/submissions", status_code=302)


@router.get("/tutor/logout")
async def tutor_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/tutor/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    # Unfreeze team if frozen_until has passed
    if team.is_frozen and team.frozen_until and team.frozen_until < datetime.utcnow():
        team.is_frozen = False
        team.frozen_until = None
        db.commit()

    # Rank
    teams_above = db.query(Team).filter(Team.score > team.score).count()
    rank = teams_above + 1

    # Cards inventory
    team_cards = (
        db.query(TeamCard)
        .filter(TeamCard.team_id == team.id, TeamCard.quantity > 0)
        .all()
    )

    # Achievements
    achievements = db.query(Achievement).filter(Achievement.team_id == team.id).all()

    # Current challenges solved
    approved_ids = {
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.approved)
        .all()
    }
    challenges = db.query(Challenge).filter(Challenge.is_active == True).order_by(Challenge.order_index).all()

    # Active event
    active_event = db.query(Event).filter(Event.is_active == True).first()

    # Pending submissions count
    pending_count = (
        db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.pending)
        .count()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "team": team,
            "rank": rank,
            "team_cards": team_cards,
            "achievements": achievements,
            "challenges": challenges,
            "approved_ids": approved_ids,
            "active_event": active_event,
            "pending_count": pending_count,
        },
    )
