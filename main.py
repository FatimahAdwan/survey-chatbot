from datetime import datetime
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from repository import save_question_set, get_by_hash_key, save_survey_result
from openai import OpenAI
import os
import ast
import hashlib

app = FastAPI()

# OpenAI setup
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# DB session helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_hash(role, goals):
    key = role.lower().strip() + "::" + "||".join([g.lower().strip() for g in goals])
    return hashlib.sha256(key.encode()).hexdigest()

def build_prompt(role, goals):
    goals_formatted = "\n".join([f"- {goal}" for goal in goals])
    return f"""
You are a survey question generator.

Your task is to generate 12 thoughtful, open-ended, role-specific survey questions for someone in the role of a {role}.
These questions must align with the following three strategic goals of the organization:

{goals_formatted}

Guidelines:
- Questions should be relevant to the {role}'s responsibilities in supporting these goals.
- Avoid yes/no questions. Use open-ended format or Likert-style.
- Some questions can have follow-up components.
- Ensure the same role with the same goals always get the same set of questions regardless of how the question is been asked.
- Return only the list of questions as a numbered list in plain text.

Example:
1. [Question one]
2. [Question two]
...
"""

def generate_survey_questions(role, goals):
    prompt = build_prompt(role, goals)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates survey questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return [q for q in response.choices[0].message.content.split("\n") if q.strip() and q.strip()[0].isdigit()]

def normalize_goals_via_llm(goals):
    return sorted([goal.lower().strip() for goal in goals])

@app.post("/dialogflow-webhook")
async def dialogflow_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        tag = body.get("fulfillmentInfo", {}).get("tag")
        session = body.get("sessionInfo", {})
        params = session.get("parameters", {})

        role = params.get("role", "").strip()
        goal1 = params.get("goal1", "").strip()
        goal2 = params.get("goal2", "").strip()
        goal3 = params.get("goal3", "").strip()

        raw_questions = params.get("questions_list", [])
        if isinstance(raw_questions, str):
            try:
                questions_list = ast.literal_eval(raw_questions)
            except Exception:
                questions_list = []
        elif isinstance(raw_questions, list):
            questions_list = raw_questions
        elif isinstance(raw_questions, dict) and "listValue" in raw_questions:
            questions_list = [v.get("stringValue", "") for v in raw_questions["listValue"]["values"]]
        else:
            questions_list = []

        raw_responses = params.get("responses_list", [])
        if isinstance(raw_responses, str):
            try:
                responses_list = ast.literal_eval(raw_responses)
            except Exception:
                responses_list = []
        elif isinstance(raw_responses, list):
            responses_list = raw_responses
        elif isinstance(raw_responses, dict) and "listValue" in raw_responses:
            responses_list = [v.get("stringValue", "") for v in raw_responses["listValue"]["values"]]
        else:
            responses_list = []

        user_response = params.get("user_response") or params.get("any")

        if not questions_list and role and goal1 and goal2 and goal3:
            goals = [goal1, goal2, goal3]
            normalized_goals = normalize_goals_via_llm(goals)
            hash_key = generate_hash(role, normalized_goals)

            existing = get_by_hash_key(db, hash_key)
            if existing:
                questions = existing.questions_json.split("\n")
            else:
                questions = generate_survey_questions(role, normalized_goals)
                save_question_set(db, {
                    "role": role,
                    "normalized_goals": ",".join(normalized_goals),
                    "hash_key": hash_key,
                    "questions_json": "\n".join(questions),
                    "created_at": datetime.utcnow()
                })

            return {
                "sessionInfo": {
                    "parameters": {
                        "questions_list": questions,
                        "responses_list": [],
                        "user_response": None,
                        "any": None
                    }
                },
                "fulfillment_response": {
                    "messages": [
                        {"text": {"text": ["Great! Let's begin your survey."]}},
                        {"text": {"text": [questions[0]]}}
                    ]
                }
            }

        elif questions_list:
            if user_response is None or str(user_response).strip() == "":
                return {
                    "fulfillment_response": {
                        "messages": [{"text": {"text": ["Please provide your answer before we continue."]}}]
                    }
                }

            responses_list.append(str(user_response).strip())
            current_index = len(responses_list)

            if current_index < len(questions_list):
                return {
                    "sessionInfo": {
                        "parameters": {
                            "questions_list": questions_list,
                            "responses_list": responses_list,
                            "user_response": None,
                            "any": None
                        }
                    },
                    "fulfillment_response": {
                        "messages": [{"text": {"text": [questions_list[current_index]]}}]
                    }
                }

            else:
                session_id = session.get("session", "").split("/")[-1]
                save_survey_result(
                    db,
                    session_id=session_id,
                    role=role,
                    goal1=goal1,
                    goal2=goal2,
                    goal3=goal3,
                    responses=responses_list
                )

                return {
                    "fulfillment_response": {
                        "messages": [{"text": {"text": ["✅ Thank you! You've completed the survey."]}}]
                    }
                }

        return {
            "fulfillment_response": {
                "messages": [{"text": {"text": ["I will need you to provide your role and three strategic goals"]}}]
            }
        }

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse(
            status_code=500,
            content={
                "fulfillment_response": {
                    "messages": [{"text": {"text": [f"⚠️ Error: {str(e)}"]}}]
                }
            }
        )

# health check route
@app.get("/")
def root():
    return {"message": "Survey chatbot backend is live!"}
