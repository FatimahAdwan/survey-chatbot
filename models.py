from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import uuid
from db import Base

class QuestionSet(Base):
    __tablename__ = "question_sets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)
    normalized_goals = Column(Text, nullable=False)
    hash_key = Column(String(255), unique=True, nullable=False)
    questions_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from db import Base

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True) # keep checking for max length
    role = Column(String)
    goal1 = Column(String)
    goal2 = Column(String)
    goal3 = Column(String)
    responses = Column(Text)  # Store as newline-separated string
    timestamp = Column(DateTime, default=datetime.utcnow)

