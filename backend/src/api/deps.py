from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session, select

from src.core.db import get_session
from src.core.security import decode_access_token
from src.models.user import User

security = HTTPBearer()


def get_current_user_from_request(request: Request) -> User:
    """Get current user from request headers (for middleware)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header[len("Bearer ") :]

    # Get session for this request
    session_generator = get_session()
    session = next(session_generator)
    try:
        return get_user_from_token(session, token)
    finally:
        session.close()


def get_user_from_token(session: Session, token: str) -> User:
    """Get user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
        )

    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Session = Depends(get_session),
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    return get_user_from_token(session, token)
