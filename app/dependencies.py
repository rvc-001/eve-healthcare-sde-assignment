"""
FastAPI dependencies — mirrors Forehand's controller.ts split of publicApi / protectedApi.

Forehand's protectedApi uses .derive() to extract and validate the Supabase JWT,
then injects the `user` object into all downstream handlers.

Our equivalent uses FastAPI's Depends() system:
  - get_db()         → injects a DB session (mirrors .decorate("db", db))
  - get_current_user() → extracts + validates JWT Bearer token, returns User model
                         (mirrors protectedApi's .derive() block)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

# Bearer scheme — automatically reads the Authorization: Bearer <token> header
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Protected dependency — validates the JWT token and returns the current user.

    Mirrors Forehand's protectedApi .derive() block:
        const { data: { user }, error } = await supabase.auth.getUser(token)
        if (error || !user) return status(401, "Unauthorized")
        return { user }

    Raises HTTP 401 if:
      - No Authorization header is present
      - Token is missing, malformed, or expired
      - User ID from token does not exist in our database
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
