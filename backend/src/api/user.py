from fastapi import APIRouter

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.get("/settings")
def get_settings():
    return {
        "vai_tro": "Nhân viên",
        "chi_nhanh": "Hà Nội",
        "pham_vi": "Cá nhân",
        "du_lieu": "Dữ liệu cơ bản",
    }


@user_router.post("/settings")
def update_settings():
    return {"msg": "updated"}
