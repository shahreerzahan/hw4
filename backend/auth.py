"""Create-account / log-in: password hashing, signed session cookies, and the /api/auth routes.

Passwords are never stored. We store a salted PBKDF2-HMAC-SHA256 hash in the format the seed
database already uses, so seed users (like the test user) and new users log in the same way:

    legacy (seed data):  pbkdf2_sha256$<salt>$<hex digest>                 -> 120,000 iterations
    new accounts:        pbkdf2_sha256$<iterations>$<salt>$<hex digest>    -> 600,000 iterations
"""
import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import time

from dotenv import load_dotenv
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from db import ROOT, get_db

load_dotenv(ROOT / ".env")
log = logging.getLogger("campus_customs.auth")

ALGORITHM = "pbkdf2_sha256"
LEGACY_ITERATIONS = 120_000  # what the seed database uses (no count stored in the hash)
ITERATIONS = 600_000         # OWASP-recommended work factor for new hashes
MIN_PASSWORD_LENGTH = 8

COOKIE_NAME = "cc_session"
SESSION_SECONDS = 7 * 24 * 3600
SESSION_SECRET = os.getenv("SESSION_SECRET") or ""
if not SESSION_SECRET:
    # Without a fixed secret, sessions still work but reset whenever the server restarts.
    SESSION_SECRET = secrets.token_hex(32)
    log.warning("SESSION_SECRET not set in .env; using a temporary one.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Password hashing ----------

def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 3 and parts[0] == ALGORITHM:
        _, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    elif len(parts) == 4 and parts[0] == ALGORITHM and parts[1].isdigit():
        _, iterations_str, salt, digest = parts
        iterations = int(iterations_str)
    else:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), digest)


# Used when the email doesn't exist, so a wrong email takes as long as a wrong password.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- Session cookie (signed, so it can't be forged) ----------

def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_SECONDS}"
    raw = f"{payload}.{_sign(payload)}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def read_session_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        user_id, expires, sig = base64.urlsafe_b64decode(token.encode()).decode().split(".")
    except (ValueError, UnicodeDecodeError):
        return None
    if not hmac.compare_digest(_sign(f"{user_id}.{expires}"), sig) or int(expires) < time.time():
        return None
    return int(user_id)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        make_session_token(user_id),
        max_age=SESSION_SECONDS,
        httponly=True,  # page JavaScript can't read it
        samesite="lax",
    )


# ---------- Users ----------

class RegisterIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def public_user(row: sqlite3.Row) -> dict:
    """The user fields safe to send to the browser (never the password hash)."""
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return {"id": row["id"], "first_name": first, "last_name": last, "email": row["email"]}


def get_user(user_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def current_user_id(cc_session: str | None) -> int | None:
    """User id from the session cookie, or None if not logged in."""
    user_id = read_session_token(cc_session)
    return user_id if user_id is not None and get_user(user_id) else None


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterIn, response: Response) -> dict:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.strip().lower()
    if not first or not last:
        raise HTTPException(400, "Please enter your first and last name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Try logging in.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, hash_password(body.password), first, last),
        )
        user_id = cur.lastrowid

    set_session_cookie(response, user_id)
    return {"user": public_user(get_user(user_id))}


@router.post("/login")
def login(body: LoginIn, response: Response) -> dict:
    email = body.email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()

    if row is None:
        verify_password(body.password, _DUMMY_HASH)
        ok = False
    else:
        ok = verify_password(body.password, row["password_hash"])
    if not ok:
        # Same message either way, so nobody can probe which emails have accounts.
        raise HTTPException(401, "Incorrect email or password.")

    set_session_cookie(response, row["id"])
    return {"user": public_user(row)}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict:
    user_id = current_user_id(cc_session)
    return {"user": public_user(get_user(user_id)) if user_id else None}
