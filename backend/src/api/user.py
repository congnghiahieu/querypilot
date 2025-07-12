import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from src.api.auth import get_current_user
from src.core.db import get_session
from src.core.iam_service import get_iam_service
from src.core.settings import APP_SETTINGS
from src.models.user import User, UserSettings

user_router = APIRouter(prefix="/user", tags=["User"])

# Mock data for datasources (in production, this would be in database)
datasources_db = {
    "financial": {
        "name": "Financial Database",
        "description": "Company financial data",
        "tables": ["transactions", "accounts", "budgets"],
        "access_level": "restricted",
    },
    "sales": {
        "name": "Sales Database",
        "description": "Sales and customer data",
        "tables": ["customers", "orders", "products"],
        "access_level": "public",
    },
    "hr_basic": {
        "name": "HR Basic",
        "description": "Basic HR information",
        "tables": ["employees", "departments"],
        "access_level": "internal",
    },
    "hr_sensitive": {
        "name": "HR Sensitive",
        "description": "Sensitive HR data",
        "tables": ["salaries", "performance_reviews"],
        "access_level": "confidential",
    },
}


class UserSettingsResponse(BaseModel):
    vai_tro: str
    chi_nhanh: str
    pham_vi: str
    du_lieu: str
    datasource_permissions: List[str]


class UserSettingsUpdate(BaseModel):
    vai_tro: str
    chi_nhanh: str
    pham_vi: str
    du_lieu: str
    datasource_permissions: List[str]


class DataSourceInfo(BaseModel):
    id: str
    name: str
    description: str
    tables: List[str]
    access_level: str
    has_access: bool


@user_router.get("/settings", response_model=UserSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """Get user settings"""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    if not user_settings:
        # Create default settings if none exist
        user_settings = UserSettings(
            user_id=current_user.id,
            vai_tro="Nhân viên",
            chi_nhanh="Hà Nội",
            pham_vi="Cá nhân",
            du_lieu="Dữ liệu cơ bản",
            datasource_permissions='["financial"]',
        )
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    return UserSettingsResponse(
        vai_tro=user_settings.vai_tro,
        chi_nhanh=user_settings.chi_nhanh,
        pham_vi=user_settings.pham_vi,
        du_lieu=user_settings.du_lieu,
        datasource_permissions=json.loads(user_settings.datasource_permissions),
    )


@user_router.post("/settings")
def update_settings(
    settings: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update user settings"""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        session.add(user_settings)

    user_settings.vai_tro = settings.vai_tro
    user_settings.chi_nhanh = settings.chi_nhanh
    user_settings.pham_vi = settings.pham_vi
    user_settings.du_lieu = settings.du_lieu
    user_settings.datasource_permissions = json.dumps(settings.datasource_permissions)

    session.commit()

    # Update IAM permissions if in AWS environment
    if APP_SETTINGS.is_aws:
        iam_service = get_iam_service()
        if iam_service and hasattr(current_user, "cognito_user_id"):
            iam_result = iam_service.update_user_role_permissions(
                user_id=current_user.cognito_user_id,
                username=current_user.username,
                new_permissions=settings.datasource_permissions,
            )

            if not iam_result["success"]:
                print(f"Warning: Could not update IAM permissions: {iam_result['error']}")

    return {"message": "Settings updated successfully"}


@user_router.get("/datasources", response_model=List[DataSourceInfo])
def get_datasources(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """Get all datasources with user access information"""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    user_permissions = []
    if user_settings:
        user_permissions = json.loads(user_settings.datasource_permissions)

    datasources = []
    for ds_id, ds_info in datasources_db.items():
        datasources.append(
            DataSourceInfo(
                id=ds_id,
                name=ds_info["name"],
                description=ds_info["description"],
                tables=ds_info["tables"],
                access_level=ds_info["access_level"],
                has_access=ds_id in user_permissions,
            )
        )

    return datasources


@user_router.get("/datasources/accessible", response_model=List[DataSourceInfo])
def get_accessible_datasources(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """Get only datasources that user has access to"""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    user_permissions = []
    if user_settings:
        user_permissions = json.loads(user_settings.datasource_permissions)

    datasources = []
    for ds_id in user_permissions:
        if ds_id in datasources_db:
            ds_info = datasources_db[ds_id]
            datasources.append(
                DataSourceInfo(
                    id=ds_id,
                    name=ds_info["name"],
                    description=ds_info["description"],
                    tables=ds_info["tables"],
                    access_level=ds_info["access_level"],
                    has_access=True,
                )
            )

    return datasources


@user_router.post("/datasources/{datasource_id}/request-access")
def request_datasource_access(
    datasource_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Request access to a datasource"""
    if datasource_id not in datasources_db:
        raise HTTPException(status_code=404, detail="Datasource not found")

    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    user_permissions = []
    if user_settings:
        user_permissions = json.loads(user_settings.datasource_permissions)

    if datasource_id in user_permissions:
        return {"message": "Access already granted"}

    return {
        "message": "Access request submitted for review",
        "datasource": datasources_db[datasource_id]["name"],
        "status": "pending",
    }


@user_router.get("/profile")
def get_user_profile(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    """Get user profile information"""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    ).first()

    accessible_datasources = []
    if user_settings:
        accessible_datasources = json.loads(user_settings.datasource_permissions)

    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email or "",
        "full_name": current_user.full_name or "",
        "role": current_user.role,
        "settings": {
            "vai_tro": user_settings.vai_tro if user_settings else "Nhân viên",
            "chi_nhanh": user_settings.chi_nhanh if user_settings else "Hà Nội",
            "pham_vi": user_settings.pham_vi if user_settings else "Cá nhân",
            "du_lieu": user_settings.du_lieu if user_settings else "Dữ liệu cơ bản",
        },
        "accessible_datasources": accessible_datasources,
        "total_datasources": len(datasources_db),
        "access_level": user_settings.du_lieu if user_settings else "basic",
    }


@user_router.get("/iam-role-info")
def get_user_iam_role_info(
    current_user: User = Depends(get_current_user),
):
    """Get user IAM role information (AWS only)"""
    if not APP_SETTINGS.is_aws:
        raise HTTPException(
            status_code=400, detail="IAM role info only available in AWS environment"
        )

    if not hasattr(current_user, "cognito_user_id") or not current_user.cognito_user_id:
        raise HTTPException(status_code=400, detail="User not associated with Cognito")

    iam_service = get_iam_service()
    if not iam_service:
        raise HTTPException(status_code=500, detail="IAM service not available")

    result = iam_service.get_user_role_info(
        user_id=current_user.cognito_user_id, username=current_user.username
    )

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
