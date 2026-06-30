import json as _json

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from starlette.middleware.sessions import SessionMiddleware

from database import engine, Base
import models  # noqa: F401 — registers all models with Base

app = FastAPI(title="Space Mission — Coding Competition")

app.add_middleware(SessionMiddleware, secret_key="space-mission-secret-2024-bootcamp")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
# Add tojson filter for use in templates (safe JS embedding)
templates.env.filters["tojson"] = lambda v: _json.dumps(v)
templates.env.globals["min"] = min
templates.env.globals["max"] = max
templates.env.globals["enumerate"] = enumerate


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    from seed import seed_if_empty
    seed_if_empty()
    print("\n🚀 Space Mission Platform ready!")
    print("   → http://localhost:8000")
    print("   → Team login:  /login")
    print("   → Tutor login: /tutor/login")
    print("   → Admin:       admin / admin123\n")


from routers import teams, challenges, leaderboard, cards, admin, tutor, runner, quiz  # noqa: E402

quiz._init_templates(templates)

app.include_router(teams.router)
app.include_router(challenges.router)
app.include_router(leaderboard.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(tutor.router)
app.include_router(runner.router)
app.include_router(quiz.router)
