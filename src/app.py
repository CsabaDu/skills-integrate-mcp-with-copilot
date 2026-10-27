"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

logger = logging.getLogger(__name__)
session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    session_secret = secrets.token_urlsafe(32)
    logger.warning(
        "SESSION_SECRET is not set; sessions will not survive restarts or "
        "work across multiple application workers"
    )

try:
    teacher_credentials = json.loads(os.getenv("TEACHER_CREDENTIALS", "{}"))
except json.JSONDecodeError as error:
    raise RuntimeError("TEACHER_CREDENTIALS must be a JSON object") from error

if not isinstance(teacher_credentials, dict) or any(
    not isinstance(username, str)
    or not username
    or not isinstance(password_hash, str)
    for username, password_hash in teacher_credentials.items()
):
    raise RuntimeError(
        "TEACHER_CREDENTIALS must map non-empty usernames to password hashes"
    )


def _validate_password_hash(password_hash: str) -> None:
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
        iteration_count = int(iterations)
    except ValueError as error:
        raise RuntimeError("Invalid teacher password hash configuration") from error

    if (
        algorithm != "pbkdf2_sha256"
        or iteration_count < 600_000
        or not salt
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise RuntimeError("Invalid teacher password hash configuration")


for configured_password_hash in teacher_credentials.values():
    _validate_password_hash(configured_password_hash)

cookie_secure_value = os.getenv("SESSION_COOKIE_SECURE", "true").lower()
if cookie_secure_value not in {"true", "false"}:
    raise RuntimeError("SESSION_COOKIE_SECURE must be 'true' or 'false'")

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="teacher_session",
    max_age=8 * 60 * 60,
    same_site="lax",
    https_only=cookie_secure_value == "true",
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


def _verify_password(password: str, password_hash: str) -> bool:
    _, iterations, salt, expected_digest = password_hash.split("$", 3)
    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), int(iterations)
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)


def require_teacher(request: Request) -> None:
    if not request.session.get("teacher"):
        raise HTTPException(status_code=401, detail="Teacher login required")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/status")
def get_auth_status(request: Request):
    username = request.session.get("teacher")
    return {"authenticated": bool(username), "username": username}


@app.post("/auth/login")
def login(credentials: LoginRequest, request: Request):
    if not teacher_credentials:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured on this server",
        )

    configured_hash = teacher_credentials.get(credentials.username)
    if configured_hash is None or not _verify_password(
        credentials.password, configured_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session.clear()
    request.session["teacher"] = credentials.username
    return {"message": "Logged in successfully", "username": credentials.username}


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@app.get("/activities")
def get_activities():
    return activities


@app.post(
    "/activities/{activity_name}/signup",
    dependencies=[Depends(require_teacher)],
)
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete(
    "/activities/{activity_name}/unregister",
    dependencies=[Depends(require_teacher)],
)
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
