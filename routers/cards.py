from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_team
from database import get_db, SessionLocal
from models import Card, CardType, Team, TeamCard
from websocket_manager import manager
from routers.leaderboard import get_leaderboard_data

router = APIRouter(prefix="/cards")
templates = Jinja2Templates(directory="templates")


@router.get("/shop", response_class=HTMLResponse)
async def card_shop(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    cards = db.query(Card).all()
    owned = {tc.card_id: tc.quantity for tc in db.query(TeamCard).filter(TeamCard.team_id == team.id).all()}
    return templates.TemplateResponse(
        "cards/shop.html",
        {"request": request, "team": team, "cards": cards, "owned": owned},
    )


@router.post("/buy/{card_id}")
async def buy_card(
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

    team_card = (
        db.query(TeamCard)
        .filter(TeamCard.team_id == team.id, TeamCard.card_id == card_id)
        .first()
    )
    if team_card:
        team_card.quantity += 1
    else:
        team_card = TeamCard(team_id=team.id, card_id=card_id, quantity=1)
        db.add(team_card)

    db.commit()
    return RedirectResponse("/cards/shop", status_code=302)


@router.post("/use/{team_card_id}")
async def use_card(
    team_card_id: int,
    target_team_id: int = Form(None),
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    team_card = (
        db.query(TeamCard)
        .filter(TeamCard.id == team_card_id, TeamCard.team_id == team.id)
        .first()
    )
    if not team_card or team_card.quantity < 1:
        raise HTTPException(status_code=400, detail="Card not available")

    card = team_card.card
    effect_msg = ""

    if card.card_type == CardType.double_points:
        team.double_points_active = True
        effect_msg = "⚡ Double Points activated! Your next approval will count double."

    elif card.card_type == CardType.freeze_opponent:
        if not target_team_id:
            raise HTTPException(status_code=400, detail="Select a target team")
        target = db.query(Team).filter(Team.id == target_team_id).first()
        if not target or target.id == team.id:
            raise HTTPException(status_code=400, detail="Invalid target")
        target.is_frozen = True
        target.frozen_until = datetime.utcnow() + timedelta(minutes=5)
        db.commit()
        await manager.send_to_team(target.id, {
            "type": "freeze",
            "message": f"🥶 Your team has been frozen for 5 minutes by {team.name}!",
        })
        effect_msg = f"❄️ Team {target.name} has been frozen for 5 minutes!"

    elif card.card_type == CardType.skip_challenge:
        effect_msg = "⏭️ Skip Challenge activated! Use it on the challenge page."
        team.double_points_active = False  # no stacking

    elif card.card_type == CardType.hint:
        effect_msg = "💡 Hint card used! A tutor will send you a hint shortly."

    elif card.card_type == CardType.bug_detector:
        effect_msg = "🐛 Bug Detector used! A tutor will point out a bug location shortly."

    elif card.card_type == CardType.extra_time:
        effect_msg = "⏰ Extra Time granted! (Tutor notified)"

    team_card.quantity -= 1
    team_card.used_count += 1
    db.commit()

    if effect_msg:
        await manager.send_to_team(team.id, {"type": "card_effect", "message": effect_msg})

    return RedirectResponse("/dashboard", status_code=302)
