"""
管理员相关Schema
"""
from pydantic import BaseModel
from typing import Optional


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """管理员登录响应"""
    success: bool
    message: str
    token: Optional[str] = None
    expires_in: Optional[int] = None


class ApproveRequest(BaseModel):
    """审核通过请求"""
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    """审核拒绝请求"""
    reason: str