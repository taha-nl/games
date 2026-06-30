"""
JSON API router — consumed by the React frontend.
All routes are prefixed with /api.
The existing HTML routes stay intact during migration.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from auth import (
    get_current_team,
    get_current_tutor,
    hash_password,
    require_admin,
    verify_password,
)
from database import get_db, SessionLocal
from models import (
    Achievement,
    Card,
    CardType,
    Challenge,
    Event,
    QuizAttempt,
    QuizQuestion,
    Submission,
    SubmissionStatus,
    Team,
    TeamCard,
    TestCase,
    TutorAccount,
)
from routers.leaderboard import get_leaderboard_data
from websocket_manager import manager

router = APIRouter(prefix="/api")


# ─── helpers ───────────────────────────────────────────────────────────────

def _team_dict(t: Team) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "score": t.score,
        "coins": t.coins,
        "is_frozen": t.is_frozen,
        "frozen_until": t.frozen_until.isoformat() if t.frozen_until else None,
        "double_points_active": t.double_points_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

def _challenge_dict(c: Challenge) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "planet_name": c.planet_name,
        "description": c.description,
        "difficulty": c.difficulty,
        "points": c.points,
        "coins_reward": c.coins_reward,
        "challenge_type": c.challenge_type or "code",
        "examples": c.examples,
        "starter_code": c.starter_code,
        "is_active": c.is_active,
        "order_index": c.order_index,
    }

def _submission_dict(s: Submission) -> dict:
    return {
        "id": s.id,
        "team_id": s.team_id,
        "team_name": s.team.name if s.team else None,
        "challenge_id": s.challenge_id,
        "challenge_title": s.challenge.title if s.challenge else None,
        "code": s.code,
        "status": s.status.value if hasattr(s.status, "value") else s.status,
        "points_awarded": s.points_awarded,
        "tutor_comment": s.tutor_comment,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "reviewed_at": s.reviewed_at.isoformat() if s.reviewed_at else None,
        "double_points_active": s.team.double_points_active if s.team else False,
    }

def _event_dict(e: Event) -> dict | None:
    if not e:
        return None
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
        "multiplier": e.multiplier,
        "bonus_points": e.bonus_points,
        "is_active": e.is_active,
        "started_at": e.started_at.isoformat() if e.started_at else None,
    }

def _question_dict(q: QuizQuestion) -> dict:
    return {
        "id": q.id,
        "category": q.category,
        "question": q.question,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "correct": q.correct,
        "explanation": q.explanation,
        "joke_hint": q.joke_hint,
        "points": q.points,
        "is_active": q.is_active,
    }

async def _broadcast_leaderboard():
    db = SessionLocal()
    try:
        data = get_leaderboard_data(db)
        await manager.broadcast({"type": "leaderboard", "data": data})
    finally:
        db.close()


# ─── auth ──────────────────────────────────────────────────────────────────

@router.get("/auth/me")
async def auth_me(request: Request, db: Session = Depends(get_db)):
    team_id = request.session.get("team_id")
    tutor_id = request.session.get("tutor_id")

    if team_id:
        team = db.query(Team).filter(Team.id == team_id).first()
        if team:
            return {"team": _team_dict(team)}

    if tutor_id:
        tutor = db.query(TutorAccount).filter(TutorAccount.id == tutor_id).first()
        if tutor:
            return {
                "tutor": {
                    "id": tutor.id,
                    "username": tutor.username,
                    "role": tutor.role.value if hasattr(tutor.role, "value") else tutor.role,
                }
            }

    return {"team": None, "tutor": None}


@router.post("/auth/login")
async def api_login(
    request: Request,
    team_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team or not verify_password(password, team.password_hash):
        raise HTTPException(status_code=401, detail="Invalid team name or password")
    request.session["team_id"] = team.id
    return {"team": _team_dict(team)}


@router.post("/auth/logout")
async def api_logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.post("/auth/tutor/login")
async def api_tutor_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    tutor = db.query(TutorAccount).filter(TutorAccount.username == username).first()
    if not tutor or not verify_password(password, tutor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    request.session["tutor_id"] = tutor.id
    request.session["tutor_role"] = tutor.role.value
    return {
        "tutor": {
            "id": tutor.id,
            "username": tutor.username,
            "role": tutor.role.value if hasattr(tutor.role, "value") else tutor.role,
        }
    }


@router.post("/auth/tutor/logout")
async def api_tutor_logout(request: Request):
    request.session.clear()
    return {"ok": True}


# ─── dashboard ─────────────────────────────────────────────────────────────

@router.get("/dashboard")
async def api_dashboard(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    if team.is_frozen and team.frozen_until and team.frozen_until < datetime.utcnow():
        team.is_frozen = False
        team.frozen_until = None
        db.commit()

    rank = db.query(Team).filter(Team.score > team.score).count() + 1

    team_cards = (
        db.query(TeamCard)
        .filter(TeamCard.team_id == team.id, TeamCard.quantity > 0)
        .all()
    )
    achievements = db.query(Achievement).filter(Achievement.team_id == team.id).all()

    approved_ids = [
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.approved)
        .all()
    ]
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_active == True)
        .order_by(Challenge.order_index)
        .all()
    )
    active_event = db.query(Event).filter(Event.is_active == True).first()
    pending_count = (
        db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.pending)
        .count()
    )

    return {
        "team": _team_dict(team),
        "rank": rank,
        "challenges": [_challenge_dict(c) for c in challenges],
        "approved_ids": approved_ids,
        "pending_count": pending_count,
        "achievements": [
            {"id": a.id, "badge_name": a.badge_name, "badge_icon": a.badge_icon, "description": a.description}
            for a in achievements
        ],
        "team_cards": [
            {
                "id": tc.id,
                "quantity": tc.quantity,
                "card": {
                    "id": tc.card.id,
                    "name": tc.card.name,
                    "icon": tc.card.icon,
                    "card_type": tc.card.card_type.value if hasattr(tc.card.card_type, "value") else tc.card.card_type,
                    "description": tc.card.description,
                },
            }
            for tc in team_cards
        ],
        "active_event": _event_dict(active_event),
    }


# ─── challenges ────────────────────────────────────────────────────────────

@router.get("/challenges")
async def api_challenges(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_active == True)
        .order_by(Challenge.order_index)
        .all()
    )
    approved_ids = [
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.approved)
        .all()
    ]
    pending_ids = [
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.pending)
        .all()
    ]
    return {
        "challenges": [_challenge_dict(c) for c in challenges],
        "approved_ids": approved_ids,
        "pending_ids": pending_ids,
    }


@router.get("/challenges/{challenge_id}")
async def api_challenge_detail(
    challenge_id: int,
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.is_active == True).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    last_submission = (
        db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.challenge_id == challenge_id)
        .order_by(Submission.submitted_at.desc())
        .first()
    )
    already_approved = bool(last_submission and last_submission.status == SubmissionStatus.approved)
    active_event = db.query(Event).filter(Event.is_active == True).first()

    d = _challenge_dict(challenge)
    d["test_cases"] = [
        {"id": tc.id, "stdin": tc.stdin, "expected_output": tc.expected_output, "is_hidden": tc.is_hidden}
        for tc in challenge.test_cases
        if not tc.is_hidden
    ]

    return {
        "challenge": d,
        "already_approved": already_approved,
        "active_event": _event_dict(active_event),
        "last_submission": (
            {
                "code": last_submission.code,
                "status": last_submission.status.value if hasattr(last_submission.status, "value") else last_submission.status,
                "tutor_comment": last_submission.tutor_comment,
            }
            if last_submission
            else None
        ),
    }


@router.post("/submit")
async def api_submit(
    request: Request,
    challenge_id: int = Form(...),
    code: str = Form(...),
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    if team.is_frozen and team.frozen_until and team.frozen_until > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"🥶 Your team is frozen until {team.frozen_until.strftime('%H:%M:%S')}!",
        )

    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404)

    existing = (
        db.query(Submission)
        .filter(
            Submission.team_id == team.id,
            Submission.challenge_id == challenge_id,
            Submission.status == SubmissionStatus.approved,
        )
        .first()
    )
    if existing:
        return {"status": "already_approved", "message": "Already solved!"}

    if challenge.test_cases:
        from routers.runner import _run_once
        failed = []
        for tc in challenge.test_cases:
            result = _run_once(code, tc.stdin)
            actual = result["stdout"].strip()
            expected = tc.expected_output.strip()
            ok = (not result["timed_out"]) and (result["exit_code"] == 0) and (actual == expected)
            if not ok:
                failed.append(tc.id)

        if failed:
            raise HTTPException(
                status_code=422,
                detail=f"❌ {len(failed)} test case(s) failed. Fix your solution and run all tests before submitting.",
            )

        submission = Submission(
            team_id=team.id,
            challenge_id=challenge_id,
            code=code,
            status=SubmissionStatus.approved,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Replicate auto-approve logic
        from routers.challenges import _auto_approve
        await _auto_approve(submission, team, challenge, db)
        return {"status": "approved", "message": f"🚀 All tests passed! +{submission.points_awarded} fuel!"}

    submission = Submission(
        team_id=team.id,
        challenge_id=challenge_id,
        code=code,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    return {"status": "pending", "message": "Submitted for review!"}


# ─── leaderboard ───────────────────────────────────────────────────────────

@router.get("/leaderboard")
async def api_leaderboard(request: Request, db: Session = Depends(get_db)):
    team_id = request.session.get("team_id")
    return {"leaderboard": get_leaderboard_data(db), "team_id": team_id}


# ─── cards ─────────────────────────────────────────────────────────────────

@router.get("/cards/shop")
async def api_card_shop(
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    cards = db.query(Card).all()
    owned = {tc.card_id: tc.quantity for tc in db.query(TeamCard).filter(TeamCard.team_id == team.id).all()}
    return {
        "cards": [
            {
                "id": c.id,
                "name": c.name,
                "icon": c.icon,
                "description": c.description,
                "cost_coins": c.cost_coins,
                "card_type": c.card_type.value if hasattr(c.card_type, "value") else c.card_type,
            }
            for c in cards
        ],
        "owned": owned,
        "team_coins": team.coins,
    }


@router.post("/cards/buy/{card_id}")
async def api_buy_card(
    card_id: int,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404)
    if team.coins < card.cost_coins:
        raise HTTPException(status_code=400, detail="Not enough coins")

    team.coins -= card.cost_coins
    team_card = db.query(TeamCard).filter(TeamCard.team_id == team.id, TeamCard.card_id == card_id).first()
    if team_card:
        team_card.quantity += 1
    else:
        team_card = TeamCard(team_id=team.id, card_id=card_id, quantity=1)
        db.add(team_card)
    db.commit()
    return {"success": True, "message": f"Bought {card.name}!", "new_coins": team.coins}


@router.post("/cards/use/{team_card_id}")
async def api_use_card(
    team_card_id: int,
    target_team_id: int = Form(None),
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    team_card = db.query(TeamCard).filter(TeamCard.id == team_card_id, TeamCard.team_id == team.id).first()
    if not team_card or team_card.quantity < 1:
        raise HTTPException(status_code=400, detail="Card not available")

    card = team_card.card
    effect_msg = ""

    if card.card_type == CardType.double_points:
        team.double_points_active = True
        effect_msg = "⚡ Double Points activated!"
    elif card.card_type == CardType.freeze_opponent:
        if not target_team_id:
            raise HTTPException(status_code=400, detail="Select a target team")
        target = db.query(Team).filter(Team.id == target_team_id).first()
        if not target or target.id == team.id:
            raise HTTPException(status_code=400, detail="Invalid target")
        target.is_frozen = True
        target.frozen_until = datetime.utcnow() + timedelta(minutes=5)
        db.commit()
        await manager.send_to_team(target.id, {"type": "freeze", "message": f"🥶 Frozen for 5 minutes by {team.name}!"})
        effect_msg = f"❄️ Team {target.name} frozen for 5 minutes!"
    elif card.card_type == CardType.hint:
        effect_msg = "💡 Hint card used! A tutor will send a hint shortly."
    elif card.card_type == CardType.bug_detector:
        effect_msg = "🐛 Bug Detector used! A tutor will point out a bug shortly."
    elif card.card_type == CardType.extra_time:
        effect_msg = "⏰ Extra Time granted! (Tutor notified)"
    elif card.card_type == CardType.skip_challenge:
        effect_msg = "⏭️ Skip Challenge activated!"

    team_card.quantity -= 1
    team_card.used_count += 1
    db.commit()

    if effect_msg:
        await manager.send_to_team(team.id, {"type": "card_effect", "message": effect_msg})

    return {"success": True, "message": effect_msg}


# ─── quiz ──────────────────────────────────────────────────────────────────

@router.get("/quiz")
async def api_quiz_home(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.is_active == True)
        .order_by(QuizQuestion.order_index)
        .all()
    )
    correct_ids = [
        a.question_id
        for a in db.query(QuizAttempt)
        .filter(QuizAttempt.team_id == team.id, QuizAttempt.is_correct == True)
        .all()
    ]
    answered_ids = [
        a.question_id
        for a in db.query(QuizAttempt).filter(QuizAttempt.team_id == team.id).all()
    ]
    categories = sorted({q.category for q in questions})
    total_pts = sum(q.points for q in questions if q.id in correct_ids)

    return {
        "questions": [_question_dict(q) for q in questions],
        "correct_ids": correct_ids,
        "answered_ids": answered_ids,
        "categories": categories,
        "total_pts": total_pts,
    }


@router.get("/quiz/{question_id}")
async def api_quiz_question(
    question_id: int,
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id, QuizQuestion.is_active == True).first()
    if not q:
        raise HTTPException(status_code=404)

    attempt = db.query(QuizAttempt).filter(QuizAttempt.team_id == team.id, QuizAttempt.question_id == question_id).first()
    all_questions = db.query(QuizQuestion).filter(QuizQuestion.is_active == True).order_by(QuizQuestion.order_index).all()
    ids = [q2.id for q2 in all_questions]
    idx = ids.index(question_id) if question_id in ids else 0

    return {
        "question": _question_dict(q),
        "attempt": {"chosen": attempt.chosen, "is_correct": attempt.is_correct, "points_awarded": attempt.points_awarded} if attempt else None,
        "q_number": idx + 1,
        "q_total": len(ids),
        "prev_id": ids[idx - 1] if idx > 0 else None,
        "next_id": ids[idx + 1] if idx + 1 < len(ids) else None,
    }


@router.post("/quiz/{question_id}/answer")
async def api_quiz_answer(
    question_id: int,
    request: Request,
    answer: str = Form(...),
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id, QuizQuestion.is_active == True).first()
    if not q:
        raise HTTPException(status_code=404)

    existing = db.query(QuizAttempt).filter(QuizAttempt.team_id == team.id, QuizAttempt.question_id == question_id).first()
    if existing:
        return {"correct": existing.is_correct, "points_awarded": existing.points_awarded, "explanation": q.explanation}

    chosen = answer.lower().strip()
    if chosen not in ("a", "b", "c", "d"):
        raise HTTPException(status_code=422, detail="Answer must be a, b, c, or d")

    is_correct = chosen == q.correct
    pts = q.points if is_correct else 0

    attempt = QuizAttempt(
        team_id=team.id, question_id=question_id, chosen=chosen,
        is_correct=is_correct, points_awarded=pts, answered_at=datetime.utcnow(),
    )
    db.add(attempt)
    if is_correct:
        team.score += pts
        team.coins += max(pts // 2, 5)
    db.commit()

    return {"correct": is_correct, "points_awarded": pts, "explanation": q.explanation}


# ─── tutor ─────────────────────────────────────────────────────────────────

@router.get("/tutor/submissions")
async def api_tutor_submissions(
    status_filter: str = "pending",
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    query = db.query(Submission)
    if status_filter != "all":
        query = query.filter(Submission.status == status_filter)
    submissions = query.order_by(Submission.submitted_at.desc()).limit(100).all()
    return {
        "submissions": [_submission_dict(s) for s in submissions],
        "pending_count": db.query(Submission).filter(Submission.status == SubmissionStatus.pending).count(),
        "status_filter": status_filter,
    }


@router.get("/tutor/submissions/{submission_id}")
async def api_tutor_submission_detail(
    submission_id: int,
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404)
    return {
        "submission": _submission_dict(s),
        "challenge": _challenge_dict(s.challenge) if s.challenge else None,
    }


@router.post("/tutor/submissions/{submission_id}/approve")
async def api_approve_submission(
    submission_id: int,
    comment: str = Form(""),
    bonus_points: int = Form(0),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404)

    team = db.query(Team).filter(Team.id == s.team_id).first()
    challenge = db.query(Challenge).filter(Challenge.id == s.challenge_id).first()
    base_points = challenge.points + bonus_points

    if team.double_points_active:
        base_points *= 2
        team.double_points_active = False

    active_event = db.query(Event).filter(Event.is_active == True).first()
    if active_event and active_event.multiplier > 1.0:
        base_points = int(base_points * active_event.multiplier)

    s.status = SubmissionStatus.approved
    s.points_awarded = base_points
    s.tutor_comment = comment
    s.reviewed_at = datetime.utcnow()
    team.score += base_points
    db.commit()

    from routers.tutor import _check_and_grant_achievements
    _check_and_grant_achievements(team, db)
    await _broadcast_leaderboard()
    await manager.send_to_team(team.id, {
        "type": "score_update",
        "points": base_points,
        "challenge": challenge.title,
        "message": f"✅ '{challenge.title}' approved! +{base_points} fuel!",
    })
    return {"success": True}


@router.post("/tutor/submissions/{submission_id}/reject")
async def api_reject_submission(
    submission_id: int,
    comment: str = Form(""),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404)

    s.status = SubmissionStatus.rejected
    s.tutor_comment = comment
    s.reviewed_at = datetime.utcnow()
    db.commit()

    await manager.send_to_team(s.team_id, {
        "type": "rejection",
        "challenge": s.challenge.title,
        "message": f"❌ Solution for '{s.challenge.title}' needs revision. {comment}",
    })
    return {"success": True}


@router.post("/tutor/hint/{team_id}")
async def api_send_hint(
    team_id: int,
    hint_text: str = Form(...),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    await manager.send_to_team(team_id, {"type": "hint", "message": f"💡 Hint: {hint_text}"})
    return {"success": True}


# ─── admin ─────────────────────────────────────────────────────────────────

@router.get("/admin/stats")
async def api_admin_stats(admin=Depends(require_admin), db: Session = Depends(get_db)):
    active_event = db.query(Event).filter(Event.is_active == True).first()
    return {
        "total_teams": db.query(Team).count(),
        "total_challenges": db.query(Challenge).count(),
        "pending_submissions": db.query(Submission).filter(Submission.status == SubmissionStatus.pending).count(),
        "approved_submissions": db.query(Submission).filter(Submission.status == SubmissionStatus.approved).count(),
        "active_event": _event_dict(active_event),
    }


@router.get("/admin/teams")
async def api_admin_teams(admin=Depends(require_admin), db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.score.desc()).all()
    return {"teams": [_team_dict(t) for t in teams]}


@router.post("/admin/teams")
async def api_admin_create_team(
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
    db.refresh(team)
    return {"team": _team_dict(team)}


@router.delete("/admin/teams/{team_id}")
async def api_admin_delete_team(
    team_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    db.delete(team)
    db.commit()
    return {"success": True}


@router.post("/admin/award_points")
async def api_award_points(
    team_id: int = Form(...),
    points: int = Form(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    team.score += points
    db.commit()
    await _broadcast_leaderboard()
    return {"success": True, "new_score": team.score}


@router.post("/admin/award_coins")
async def api_award_coins(
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
    return {"success": True, "new_coins": team.coins}


@router.post("/admin/reset")
async def api_admin_reset(
    confirm: str = Form(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    if confirm != "RESET":
        raise HTTPException(status_code=400, detail="Type RESET to confirm")
    db.query(Team).update({"score": 0, "coins": 100})
    db.commit()
    await _broadcast_leaderboard()
    return {"success": True}


@router.get("/admin/challenges")
async def api_admin_challenges(admin=Depends(require_admin), db: Session = Depends(get_db)):
    challenges = db.query(Challenge).order_by(Challenge.order_index).all()
    result = []
    for c in challenges:
        d = _challenge_dict(c)
        d["test_case_count"] = len(c.test_cases)
        result.append(d)
    return {"challenges": result}


@router.post("/admin/challenges")
async def api_admin_create_challenge(
    title: str = Form(...),
    planet_name: str = Form(...),
    difficulty: str = Form(...),
    points: int = Form(...),
    description: str = Form(...),
    examples: str = Form(""),
    starter_code: str = Form(""),
    coins_reward: int = Form(10),
    challenge_type: str = Form("code"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    max_order = db.query(Challenge).count()
    c = Challenge(
        title=title, planet_name=planet_name, difficulty=difficulty,
        points=points, description=description, examples=examples,
        starter_code=starter_code, coins_reward=coins_reward,
        challenge_type=challenge_type, order_index=max_order,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"challenge": _challenge_dict(c)}


@router.post("/admin/challenges/{challenge_id}/toggle")
async def api_admin_toggle_challenge(
    challenge_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404)
    c.is_active = not c.is_active
    db.commit()
    return {"is_active": c.is_active}


@router.get("/admin/challenges/{challenge_id}/test-cases")
async def api_admin_test_cases(
    challenge_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404)
    return {
        "challenge": _challenge_dict(c),
        "test_cases": [
            {"id": tc.id, "stdin": tc.stdin, "expected_output": tc.expected_output, "is_hidden": tc.is_hidden}
            for tc in c.test_cases
        ],
    }


@router.post("/admin/challenges/{challenge_id}/test-cases")
async def api_admin_add_test_case(
    challenge_id: int,
    stdin: str = Form(...),
    expected_output: str = Form(...),
    is_hidden: bool = Form(False),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not c:
        raise HTTPException(status_code=404)
    tc = TestCase(challenge_id=challenge_id, stdin=stdin, expected_output=expected_output, is_hidden=is_hidden)
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return {"id": tc.id, "stdin": tc.stdin, "expected_output": tc.expected_output, "is_hidden": tc.is_hidden}


@router.delete("/admin/challenges/{challenge_id}/test-cases/{tc_id}")
async def api_admin_delete_test_case(
    challenge_id: int,
    tc_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    tc = db.query(TestCase).filter(TestCase.id == tc_id, TestCase.challenge_id == challenge_id).first()
    if not tc:
        raise HTTPException(status_code=404)
    db.delete(tc)
    db.commit()
    return {"success": True}


@router.get("/admin/events")
async def api_admin_events(admin=Depends(require_admin), db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.started_at.desc()).all()
    return {"events": [_event_dict(e) for e in events]}


@router.post("/admin/events")
async def api_admin_create_event(
    title: str = Form(...),
    event_type: str = Form(...),
    multiplier: float = Form(1.0),
    bonus_points: int = Form(0),
    description: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Deactivate current events
    db.query(Event).filter(Event.is_active == True).update({"is_active": False})

    event = Event(
        title=title, description=description, event_type=event_type,
        multiplier=multiplier, bonus_points=bonus_points, is_active=True,
        started_at=datetime.utcnow(),
    )
    db.add(event)

    if bonus_points > 0:
        db.query(Team).update({"score": Team.score + bonus_points})

    db.commit()
    db.refresh(event)

    await manager.broadcast({"type": "event", "title": title, "description": description, "multiplier": multiplier})
    await _broadcast_leaderboard()
    return {"event": _event_dict(event)}


@router.post("/admin/events/{event_id}/end")
async def api_admin_end_event(
    event_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)
    event.is_active = False
    db.commit()
    await manager.broadcast({"type": "event_end", "message": f"Event '{event.title}' has ended."})
    return {"success": True}


@router.get("/admin/quiz")
async def api_admin_quiz(admin=Depends(require_admin), db: Session = Depends(get_db)):
    questions = db.query(QuizQuestion).order_by(QuizQuestion.order_index).all()
    return {"questions": [_question_dict(q) for q in questions]}


@router.post("/admin/quiz")
async def api_admin_create_question(
    category: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct: str = Form(...),
    points: int = Form(10),
    explanation: str = Form(""),
    joke_hint: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    max_order = db.query(QuizQuestion).count()
    q = QuizQuestion(
        category=category, question=question, option_a=option_a, option_b=option_b,
        option_c=option_c, option_d=option_d, correct=correct.lower(), points=points,
        explanation=explanation, joke_hint=joke_hint, order_index=max_order,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"question": _question_dict(q)}


@router.post("/admin/quiz/{question_id}/edit")
async def api_admin_edit_question(
    question_id: int,
    category: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct: str = Form(...),
    points: int = Form(10),
    explanation: str = Form(""),
    joke_hint: str = Form(""),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404)
    q.category = category; q.question = question
    q.option_a = option_a; q.option_b = option_b; q.option_c = option_c; q.option_d = option_d
    q.correct = correct.lower(); q.points = points; q.explanation = explanation; q.joke_hint = joke_hint
    db.commit()
    return {"question": _question_dict(q)}


@router.post("/admin/quiz/{question_id}/toggle")
async def api_admin_toggle_question(
    question_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404)
    q.is_active = not q.is_active
    db.commit()
    return {"is_active": q.is_active}


@router.delete("/admin/quiz/{question_id}")
async def api_admin_delete_question(
    question_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404)
    db.delete(q)
    db.commit()
    return {"success": True}


@router.post("/admin/tutors")
async def api_admin_create_tutor(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("tutor"),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(TutorAccount).filter(TutorAccount.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    tutor = TutorAccount(username=username, password_hash=hash_password(password), role=role)
    db.add(tutor)
    db.commit()
    return {"success": True}
