from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import hash_password, require_admin
from database import get_db, SessionLocal
from models import Achievement, Challenge, Event, EventType, QuizAttempt, QuizQuestion, Submission, SubmissionStatus, Team, TeamCard, TestCase, TutorAccount
from websocket_manager import manager
from routers.leaderboard import get_leaderboard_data

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


async def _broadcast_leaderboard():
    db = SessionLocal()
    try:
        data = get_leaderboard_data(db)
        await manager.broadcast({"type": "leaderboard", "data": data})
    finally:
        db.close()


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    stats = {
        "total_teams": db.query(Team).count(),
        "total_challenges": db.query(Challenge).count(),
        "pending_submissions": db.query(Submission).filter(Submission.status == SubmissionStatus.pending).count(),
        "approved_submissions": db.query(Submission).filter(Submission.status == SubmissionStatus.approved).count(),
        "active_event": db.query(Event).filter(Event.is_active == True).first(),
    }
    teams = db.query(Team).order_by(Team.score.desc()).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "admin": admin, "stats": stats, "teams": teams},
    )


# --- Teams ---
@router.get("/teams", response_class=HTMLResponse)
async def admin_teams(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    teams = db.query(Team).all()
    return templates.TemplateResponse(
        "admin/teams.html",
        {"request": request, "admin": admin, "teams": teams},
    )


@router.post("/teams/create")
async def create_team(
    team_name: str = Form(...),
    password: str = Form(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Team).filter(Team.name == team_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team name already taken")
    team = Team(name=team_name, password_hash=hash_password(password))
    db.add(team)
    db.commit()
    return RedirectResponse("/admin/teams", status_code=302)


@router.post("/teams/{team_id}/delete")
async def delete_team(
    team_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team:
        db.query(Submission).filter(Submission.team_id == team_id).delete()
        db.query(TeamCard).filter(TeamCard.team_id == team_id).delete()
        db.query(Achievement).filter(Achievement.team_id == team_id).delete()
        db.delete(team)
        db.commit()
        await _broadcast_leaderboard()
    return RedirectResponse("/admin/teams", status_code=302)


# --- Challenges ---
@router.get("/challenges", response_class=HTMLResponse)
async def admin_challenges(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    challenges = db.query(Challenge).order_by(Challenge.order_index).all()
    return templates.TemplateResponse(
        "admin/challenges.html",
        {"request": request, "admin": admin, "challenges": challenges},
    )


@router.post("/challenges/create")
async def create_challenge(
    title: str = Form(...),
    planet_name: str = Form(...),
    description: str = Form(...),
    difficulty: str = Form(...),
    points: int = Form(...),
    examples: str = Form(""),
    starter_code: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    max_order = db.query(Challenge).count()
    challenge = Challenge(
        title=title,
        planet_name=planet_name,
        description=description,
        difficulty=difficulty,
        points=points,
        examples=examples,
        starter_code=starter_code,
        order_index=max_order,
    )
    db.add(challenge)
    db.commit()
    return RedirectResponse("/admin/challenges", status_code=302)


@router.get("/challenges/{challenge_id}/test-cases", response_class=HTMLResponse)
async def challenge_test_cases(
    challenge_id: int,
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "admin/test_cases.html",
        {"request": request, "admin": admin, "challenge": challenge, "test_cases": challenge.test_cases},
    )


@router.post("/challenges/{challenge_id}/test-cases/add")
async def add_test_case(
    challenge_id: int,
    stdin: str = Form(""),
    expected_output: str = Form(...),
    is_hidden: bool = Form(False),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    count = db.query(TestCase).filter(TestCase.challenge_id == challenge_id).count()
    tc = TestCase(
        challenge_id=challenge_id,
        stdin=stdin,
        expected_output=expected_output,
        is_hidden=is_hidden,
        order_index=count,
    )
    db.add(tc)
    db.commit()
    return RedirectResponse(f"/admin/challenges/{challenge_id}/test-cases", status_code=302)


@router.post("/challenges/{challenge_id}/test-cases/{tc_id}/delete")
async def delete_test_case(
    challenge_id: int,
    tc_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    tc = db.query(TestCase).filter(TestCase.id == tc_id, TestCase.challenge_id == challenge_id).first()
    if tc:
        db.delete(tc)
        db.commit()
    return RedirectResponse(f"/admin/challenges/{challenge_id}/test-cases", status_code=302)


@router.post("/challenges/{challenge_id}/toggle")
async def toggle_challenge(
    challenge_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if challenge:
        challenge.is_active = not challenge.is_active
        db.commit()
    return RedirectResponse("/admin/challenges", status_code=302)


# --- Points ---
@router.post("/award_points")
async def award_points(
    team_id: int = Form(...),
    points: int = Form(...),
    reason: str = Form("Manual award"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    team.score += points
    db.commit()
    await _broadcast_leaderboard()
    await manager.send_to_team(team.id, {
        "type": "score_update",
        "points": points,
        "message": f"🎁 Admin awarded +{points} fuel! Reason: {reason}",
    })
    return RedirectResponse("/admin", status_code=302)


@router.post("/award_coins")
async def award_coins(
    team_id: int = Form(...),
    coins: int = Form(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    team.coins += coins
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/reset")
async def reset_scores(
    confirm: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if confirm != "RESET":
        raise HTTPException(status_code=400, detail="Type RESET to confirm")
    for team in db.query(Team).all():
        team.score = 0
        team.coins = 100
    db.commit()
    await _broadcast_leaderboard()
    return RedirectResponse("/admin", status_code=302)


# --- Events ---
@router.get("/events", response_class=HTMLResponse)
async def admin_events(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    events = db.query(Event).order_by(Event.started_at.desc()).all()
    return templates.TemplateResponse(
        "admin/events.html",
        {"request": request, "admin": admin, "events": events},
    )


@router.post("/create_event")
async def create_event(
    title: str = Form(...),
    description: str = Form(""),
    event_type: str = Form(...),
    multiplier: float = Form(1.0),
    bonus_points: int = Form(0),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Deactivate all current events
    db.query(Event).filter(Event.is_active == True).update({"is_active": False})

    event = Event(
        title=title,
        description=description,
        event_type=event_type,
        multiplier=multiplier,
        bonus_points=bonus_points,
        is_active=True,
    )
    db.add(event)
    db.commit()

    # If global bonus, apply immediately
    if bonus_points > 0:
        for team in db.query(Team).all():
            team.score += bonus_points
        db.commit()
        await _broadcast_leaderboard()

    await manager.broadcast({
        "type": "event",
        "title": title,
        "description": description or f"New event: {event_type}!",
        "multiplier": multiplier,
    })
    return RedirectResponse("/admin/events", status_code=302)


@router.post("/events/{event_id}/end")
async def end_event(
    event_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        event.is_active = False
        event.ended_at = datetime.utcnow()
        db.commit()
    await manager.broadcast({"type": "event_end", "message": "Event has ended!"})
    return RedirectResponse("/admin/events", status_code=302)


# --- Quiz ---
@router.get("/quiz", response_class=HTMLResponse)
async def admin_quiz(
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    questions = db.query(QuizQuestion).order_by(QuizQuestion.order_index).all()
    return templates.TemplateResponse(
        "admin/quiz.html",
        {"request": request, "admin": admin, "questions": questions},
    )


@router.post("/quiz/create")
async def create_quiz_question(
    category: str = Form(...),
    question: str = Form(...),
    joke_hint: str = Form(""),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct: str = Form(...),
    explanation: str = Form(""),
    points: int = Form(10),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    max_order = db.query(QuizQuestion).count()
    q = QuizQuestion(
        category=category,
        question=question,
        joke_hint=joke_hint or None,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct=correct.lower(),
        explanation=explanation or None,
        points=points,
        order_index=max_order,
    )
    db.add(q)
    db.commit()
    return RedirectResponse("/admin/quiz", status_code=302)


@router.get("/quiz/{question_id}/edit", response_class=HTMLResponse)
async def edit_quiz_question_page(
    question_id: int,
    request: Request,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "admin/quiz.html",
        {"request": request, "admin": admin, "questions": db.query(QuizQuestion).order_by(QuizQuestion.order_index).all(), "editing": q},
    )


@router.post("/quiz/{question_id}/edit")
async def edit_quiz_question(
    question_id: int,
    category: str = Form(...),
    question: str = Form(...),
    joke_hint: str = Form(""),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct: str = Form(...),
    explanation: str = Form(""),
    points: int = Form(10),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404)
    q.category = category
    q.question = question
    q.joke_hint = joke_hint or None
    q.option_a = option_a
    q.option_b = option_b
    q.option_c = option_c
    q.option_d = option_d
    q.correct = correct.lower()
    q.explanation = explanation or None
    q.points = points
    db.commit()
    return RedirectResponse("/admin/quiz", status_code=302)


@router.post("/quiz/{question_id}/toggle")
async def toggle_quiz_question(
    question_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if q:
        q.is_active = not q.is_active
        db.commit()
    return RedirectResponse("/admin/quiz", status_code=302)


@router.post("/quiz/{question_id}/delete")
async def delete_quiz_question(
    question_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if q:
        db.query(QuizAttempt).filter(QuizAttempt.question_id == question_id).delete()
        db.delete(q)
        db.commit()
    return RedirectResponse("/admin/quiz", status_code=302)


# --- Tutor accounts ---
@router.post("/tutors/create")
async def create_tutor(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("tutor"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(TutorAccount).filter(TutorAccount.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    tutor = TutorAccount(username=username, password_hash=hash_password(password), role=role)
    db.add(tutor)
    db.commit()
    return RedirectResponse("/admin/teams", status_code=302)
