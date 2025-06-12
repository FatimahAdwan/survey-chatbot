from sqlalchemy.orm import Session
from models import QuestionSet
from datetime import datetime
from models import SurveyResponse

def save_question_set(db: Session, data: dict):
    question = QuestionSet(**data)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

def get_by_hash_key(db: Session, hash_key: str):
    return db.query(QuestionSet).filter(QuestionSet.hash_key == hash_key).first()


# for repsonse db

def save_survey_result(db, session_id, role, goal1, goal2, goal3, responses):
    result = SurveyResponse(
        session_id=session_id,
        role=role,
        goal1=goal1,
        goal2=goal2,
        goal3=goal3,
        responses="\n".join(responses)
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
