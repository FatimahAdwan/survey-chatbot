from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import uuid

from db import Base, engine

class QuestionSet(Base):
    __tablename__ = "question_sets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)
    normalized_goals = Column(Text, nullable=False)
    hash_key = Column(String(255), unique=True, nullable=False)
    questions_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    role = Column(String)
    goal1 = Column(String)
    goal2 = Column(String)
    goal3 = Column(String)
    responses = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


def initialize_database():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
