"""
邀请码相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InvitationVerifyRequest(BaseModel):
    """验证邀请码请求"""
    invitation_code: str = Field(..., description="邀请码")
    wx_code: str = Field(..., description="微信登录code")


class InvitationVerifyResponse(BaseModel):
    """验证邀请码响应"""
    success: bool
    message: str
    openid: Optional[str] = None
    has_profile: bool = False


class MyCodesResponse(BaseModel):
    """我的邀请码响应"""
    code: str
    is_used: bool
    created_at: str