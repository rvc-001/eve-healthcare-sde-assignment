"""
Auth router — mirrors Forehand's routes/v1/userRoutes.ts structure.

Routes:
  POST /auth/signup  → register a new user
  POST /auth/login   → login, returns JWT
  GET  /auth/me      → get current user (protected)

The router stays thin: it validates input (Pydantic), calls the service,
and formats the response using send_response() — same pattern as Forehand's
routes calling sendResponse() after DB service calls.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import signup, login, AuthError
from app.utils.response import send_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    summary="Register a new user",
    status_code=201,
)
def signup_route(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - Email must be unique.
    - Password must be at least 6 characters.
    - Returns a JWT access token immediately (no separate login step needed).
    """
    try:
        user, token = signup(db, payload)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return send_response(
        success=True,
        message="Account created successfully.",
        data=TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        ).model_dump(),
    )


@router.post(
    "/login",
    summary="Login with email and password",
)
def login_route(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.
    Returns a JWT access token on success.
    """
    try:
        user, token = login(db, payload)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return send_response(
        success=True,
        message="Login successful.",
        data=TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        ).model_dump(),
    )


@router.get(
    "/me",
    summary="Get current authenticated user",
)
def me_route(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.
    Requires a valid Bearer token.

    Mirrors Forehand's protectedApi usage — get_current_user() dependency
    validates the JWT and injects the User model automatically.
    """
    return send_response(
        success=True,
        message="User retrieved successfully.",
        data=UserResponse.model_validate(current_user).model_dump(),
    )
