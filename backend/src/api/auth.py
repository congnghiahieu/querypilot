from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlmodel import Session, select

from src.api.deps import get_current_user
from src.core.cognito_auth import get_cognito_service
from src.core.db import get_session
from src.core.iam_service import get_iam_service
from src.core.security import create_access_token, hash_password, verify_password
from src.core.settings import APP_SETTINGS
from src.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    role: str = "user"


@auth_router.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user"""

    if APP_SETTINGS.is_aws:
        # AWS Cognito registration
        cognito_service = get_cognito_service()
        if not cognito_service:
            raise HTTPException(status_code=500, detail="Cognito service not available")

        # Register in Cognito
        cognito_result = cognito_service.sign_up(
            username=user.username,
            password=user.password,
            email=user.email,
            full_name=user.full_name,
        )

        if not cognito_result["success"]:
            raise HTTPException(status_code=400, detail=cognito_result["error"])

        # Create user in local database
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password="",  # Not needed for Cognito users
            role="user",
            cognito_user_id=cognito_result["user_sub"],
        )

        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        # Create IAM role for the user
        iam_service = get_iam_service()
        if iam_service:
            iam_result = iam_service.create_user_role(
                user_id=cognito_result["user_sub"], username=user.username, user_level="basic"
            )

            if not iam_result["success"]:
                print(f"Warning: Could not create IAM role: {iam_result['error']}")

        return {
            "message": "User registered successfully. Check email for verification.",
            "user_id": str(db_user.id),
            "confirmation_required": True,
        }
    else:
        # Local registration
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
            )

        # Create new user with hashed password
        hashed_password = hash_password(user.password)
        new_user = User(
            username=user.username,
            hashed_password=hashed_password,
            email=user.email,
            full_name=user.full_name,
            role="user",
            is_active=True,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return UserResponse(
            id=str(new_user.id),
            username=new_user.username,
            email=new_user.email or "",
            full_name=new_user.full_name or "",
            created_at=new_user.created_at,
            role=new_user.role,
        )


@auth_router.post("/confirm-signup")
def confirm_signup(confirmation: dict):
    """Confirm user signup (AWS Cognito only)"""
    if not APP_SETTINGS.is_aws:
        raise HTTPException(
            status_code=400, detail="Confirmation only available for AWS environment"
        )

    cognito_service = get_cognito_service()
    if not cognito_service:
        raise HTTPException(status_code=500, detail="Cognito service not available")

    result = cognito_service.confirm_sign_up(
        username=confirmation["username"], confirmation_code=confirmation["confirmation_code"]
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": "User confirmed successfully"}


@auth_router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    """Login user"""

    if APP_SETTINGS.is_aws:
        # AWS Cognito login
        cognito_service = get_cognito_service()
        if not cognito_service:
            raise HTTPException(status_code=500, detail="Cognito service not available")

        result = cognito_service.sign_in(username=user.username, password=user.password)

        if not result["success"]:
            raise HTTPException(status_code=401, detail=result["error"])

        # Get user from local database
        db_user = session.exec(select(User).where(User.username == user.username)).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found in local database")

        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user_info": result["user_info"],
            "id_token": result["id_token"],
            "refresh_token": result["refresh_token"],
            "expires_in": result["expires_in"],
        }
    else:
        # Local login
        db_user = session.exec(select(User).where(User.username == user.username)).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
            )

        # Create access token
        access_token_expires = timedelta(hours=24)
        access_token = create_access_token(
            data={"sub": db_user.username, "user_id": str(db_user.id)},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds(),
            "user": UserResponse(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email or "",
                full_name=db_user.full_name or "",
                created_at=db_user.created_at,
                role=db_user.role,
            ),
        }


@auth_router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    """Logout user"""

    if APP_SETTINGS.is_aws:
        cognito_service = get_cognito_service()
        if cognito_service:
            result = cognito_service.sign_out(token)
            if not result["success"]:
                print(f"Warning: Could not sign out from Cognito: {result['error']}")

    return {"message": "Logged out successfully"}


@auth_router.post("/refresh")
def refresh_token(refresh_data: dict, session: Session = Depends(get_session)):
    """Refresh access token"""

    if APP_SETTINGS.is_aws:
        cognito_service = get_cognito_service()
        if not cognito_service:
            raise HTTPException(status_code=500, detail="Cognito service not available")

        result = cognito_service.refresh_token(
            refresh_token=refresh_data["refresh_token"], username=refresh_data["username"]
        )

        if not result["success"]:
            raise HTTPException(status_code=401, detail=result["error"])

        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "id_token": result["id_token"],
            "expires_in": result["expires_in"],
        }
    else:
        # Local refresh (implement if needed)
        raise HTTPException(status_code=400, detail="Refresh not implemented for local auth")


@auth_router.post("/forgot-password")
def forgot_password(request: dict):
    """Initiate forgot password flow"""

    if APP_SETTINGS.is_aws:
        cognito_service = get_cognito_service()
        if not cognito_service:
            raise HTTPException(status_code=500, detail="Cognito service not available")

        result = cognito_service.forgot_password(request["username"])

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"message": "Password reset code sent to email"}
    else:
        raise HTTPException(
            status_code=400, detail="Forgot password not implemented for local auth"
        )


@auth_router.post("/reset-password")
def reset_password(request: dict):
    """Reset password with confirmation code"""

    if APP_SETTINGS.is_aws:
        cognito_service = get_cognito_service()
        if not cognito_service:
            raise HTTPException(status_code=500, detail="Cognito service not available")

        result = cognito_service.confirm_forgot_password(
            username=request["username"],
            confirmation_code=request["confirmation_code"],
            new_password=request["new_password"],
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(status_code=400, detail="Password reset not implemented for local auth")


@auth_router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email or "",
        full_name=current_user.full_name or "",
        created_at=current_user.created_at,
        role=current_user.role,
    )
