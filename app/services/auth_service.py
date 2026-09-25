"""
Auth service — business logic for signup and login.
Keeps route handlers thin by isolating DB queries and domain rules here.
Mirrors Forehand's services/ pattern (separate from routes/).
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest
from app.utils.security import hash_password, verify_password, create_access_token


class AuthError(Exception):
    """Domain-level auth error with an HTTP-friendly status code."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def signup(db: Session, payload: SignupRequest) -> tuple[User, str]:
    """
    Register a new user.

    Returns:
        (user, access_token) tuple on success.

    Raises:
        AuthError(409) if the email is already registered.
    """
    # Check for duplicate email first (gives a clearer error than IntegrityError)
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise AuthError("A user with this email already exists.", status_code=409)

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise AuthError("A user with this email already exists.", status_code=409)

    token = create_access_token({"sub": user.id})
    return user, token


def login(db: Session, payload: LoginRequest) -> tuple[User, str]:
    """
    Authenticate a user with email + password.

    Returns:
        (user, access_token) tuple on success.

    Raises:
        AuthError(401) if credentials are invalid.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    # Use verify_password even when user is None to prevent timing attacks
    dummy_hash = "$2b$12$notarealhashxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    if user is None:
        verify_password(payload.password, dummy_hash)
        raise AuthError("Invalid email or password.", status_code=401)

    if not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid email or password.", status_code=401)

    token = create_access_token({"sub": user.id})
    return user, token
