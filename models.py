from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text, Float
)
from sqlalchemy.orm import relationship
import enum

from database import Base


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CardType(str, enum.Enum):
    hint = "hint"
    bug_detector = "bug_detector"
    double_points = "double_points"
    extra_time = "extra_time"
    freeze_opponent = "freeze_opponent"
    skip_challenge = "skip_challenge"


class EventType(str, enum.Enum):
    treasure_hunt = "treasure_hunt"
    speed_round = "speed_round"
    lightning_challenge = "lightning_challenge"
    global_bonus = "global_bonus"


class TutorRole(str, enum.Enum):
    tutor = "tutor"
    admin = "admin"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    score = Column(Integer, default=0, nullable=False)
    coins = Column(Integer, default=100, nullable=False)
    double_points_active = Column(Boolean, default=False)
    is_frozen = Column(Boolean, default=False)
    frozen_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="team")
    team_cards = relationship("TeamCard", back_populates="team")
    achievements = relationship("Achievement", back_populates="team")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    planet_name = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(16), nullable=False)  # easy / medium / hard
    points = Column(Integer, nullable=False)
    coins_reward = Column(Integer, default=10, nullable=False)
    examples = Column(Text, nullable=True)
    starter_code = Column(Text, nullable=True)
    challenge_type = Column(String(16), default="code", nullable=False, server_default="code")
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="challenge")
    test_cases = relationship("TestCase", back_populates="challenge", order_by="TestCase.order_index")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    stdin = Column(Text, nullable=False, default="")       # piped to the program's stdin
    expected_output = Column(Text, nullable=False)         # exact stdout expected (stripped)
    is_hidden = Column(Boolean, default=False)             # hidden = shown as "Hidden test" to student
    order_index = Column(Integer, default=0)

    challenge = relationship("Challenge", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.pending)
    points_awarded = Column(Integer, default=0)
    tutor_comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    team = relationship("Team", back_populates="submissions")
    challenge = relationship("Challenge", back_populates="submissions")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    card_type = Column(Enum(CardType), nullable=False)
    description = Column(Text, nullable=False)
    cost_coins = Column(Integer, nullable=False)
    icon = Column(String(8), default="🃏")

    team_cards = relationship("TeamCard", back_populates="card")


class TeamCard(Base):
    __tablename__ = "team_cards"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    quantity = Column(Integer, default=1)
    used_count = Column(Integer, default=0)

    team = relationship("Team", back_populates="team_cards")
    card = relationship("Card", back_populates="team_cards")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    multiplier = Column(Float, default=1.0)
    bonus_points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    badge_name = Column(String(64), nullable=False)
    badge_icon = Column(String(8), default="🏆")
    description = Column(Text, nullable=True)
    earned_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="achievements")


class TutorAccount(Base):
    __tablename__ = "tutor_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(TutorRole), default=TutorRole.tutor)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(64), nullable=False)  # e.g. "Big O", "Sorting", "Data Structures"
    question = Column(Text, nullable=False)
    joke_hint = Column(Text, nullable=True)         # optional fun hint / joke
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct = Column(String(1), nullable=False)     # 'a', 'b', 'c', or 'd'
    explanation = Column(Text, nullable=True)       # shown after answering
    points = Column(Integer, default=10)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    attempts = relationship("QuizAttempt", back_populates="question")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    chosen = Column(String(1), nullable=False)      # 'a', 'b', 'c', or 'd'
    is_correct = Column(Boolean, nullable=False)
    points_awarded = Column(Integer, default=0)
    answered_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
    question = relationship("QuizQuestion", back_populates="attempts")
