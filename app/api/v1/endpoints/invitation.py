"""
邀请码相关API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_openid
from app.schemas.invitation import InvitationVerifyRequest, InvitationVerifyResponse, MyCodesResponse, AutoLoginRequest
from app.schemas.common import ResponseModel
from app.crud import crud_invitation, crud_profile
from app.services.wechat import get_openid_from_code
from datetime import datetime
from typing import List

router = APIRouter()


@router.post("/verify", response_model=InvitationVerifyResponse)
async def verify_invitation(
        request: InvitationVerifyRequest,
        db: Session = Depends(get_db)
):
    """
    验证邀请码并绑定用户
    """
    # 1. 验证邀请码是否存在
    invitation = crud_invitation.get_invitation_by_code(db, request.invitation_code)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码不存在"
        )

    # 2. 检查邀请码是否已使用
    if invitation.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码已被使用"
        )

    # 3. 检查是否过期
    if invitation.expire_at and invitation.expire_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码已过期"
        )

    # 4. 检查是否被禁用
    if not invitation.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邀请码已被禁用: {invitation.disable_reason or '未知原因'}"
        )

    # 5. 通过微信code获取openid
    openid = await get_openid_from_code(request.wx_code)

    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败，请重试"
        )

    # 6. 检查用户是否已经注册过
    existing_profile = crud_profile.get_profile_by_openid(db, openid)
    has_profile = existing_profile is not None

    # 7. 如果是新用户，标记邀请码为已使用
    if not has_profile:
        crud_invitation.mark_invitation_as_used(
            db=db,
            code=request.invitation_code,
            used_by_openid=openid
        )

    return InvitationVerifyResponse(
        success=True,
        message="验证成功",
        openid=openid,
        has_profile=has_profile
    )


@router.post("/apply", response_model=ResponseModel)
async def apply_invitation(db: Session = Depends(get_db)):
    """
    申请邀请码（可选功能）
    """
    # TODO: 实现邀请码申请逻辑
    return ResponseModel(
        success=True,
        message="申请邀请码功能待实现"
    )


@router.get("/my-codes", response_model=ResponseModel)
async def get_my_codes(
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    获取我的邀请码
    """
    # 获取用户资料
    profile = crud_profile.get_profile_by_openid(db, openid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户资料不存在"
        )

    # 只有已发布的用户才有邀请码
    if profile.status not in ('approved', 'published'):
        return ResponseModel(
            success=True,
            message="资料尚未发布，暂无邀请码",
            data={
                "codes": [],
                "total": 0,
                "used": 0,
                "remaining": 0
            }
        )

    # 获取用户的邀请码
    invitations = crud_invitation.get_user_invitation_codes(db, profile.id)

    codes_data = []
    used_count = 0

    for inv in invitations:
        codes_data.append(MyCodesResponse(
            code=inv.code,
            is_used=inv.is_used,
            created_at=inv.create_time.strftime("%Y-%m-%d %H:%M:%S")
        ))
        if inv.is_used:
            used_count += 1

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "codes": [c.dict() for c in codes_data],
            "total": len(invitations),
            "used": used_count,
            "remaining": len(invitations) - used_count
        }
    )

@router.post("/auto-login", response_model=InvitationVerifyResponse)
async def auto_login(
        request: AutoLoginRequest,
        db: Session = Depends(get_db)
):
    """
    自动登录（老用户通过微信code自动识别）
    """
    # 1. 通过微信code获取openid
    openid = await get_openid_from_code(request.wx_code)

    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败"
        )

    # 2. 检查用户是否已注册
    existing_profile = crud_profile.get_profile_by_openid(db, openid)

    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="非注册用户"
        )

    # 3. 返回用户信息
    return InvitationVerifyResponse(
        success=True,
        message="自动登录成功",
        openid=openid,
        has_profile=True
    )
