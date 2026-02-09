"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import invitation, profile, upload, admin

api_router = APIRouter()

# 用户端API
api_router.include_router(
    invitation.router,
    prefix="/invitation",
    tags=["邀请码"]
)

api_router.include_router(
    profile.router,
    prefix="/profile",
    tags=["用户资料"]
)

api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["文件上传"]
)

# 管理端API
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["管理后台"]
)