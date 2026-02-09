"""
管理员相关API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_admin
from app.core.security import verify_password, create_access_token
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, ApproveRequest, RejectRequest
from app.schemas.common import ResponseModel
from app.crud import crud_admin, crud_profile, crud_invitation
from app.services.post_generator import generate_post_content
from app.services.invitation import generate_invitation_code, calculate_expire_time
from app.core.config import settings
from datetime import timedelta

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
        request: AdminLoginRequest,
        db: Session = Depends(get_db)
):
    """
    管理员登录
    """
    # 1. 查找管理员
    admin = crud_admin.get_admin_by_username(db, request.username)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 2. 验证密码
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 3. 检查是否激活
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    # 4. 生成token
    access_token = create_access_token(
        data={"sub": admin.username, "admin_id": admin.id}
    )

    # 5. 更新最后登录时间
    crud_admin.update_last_login(db, admin.id)

    return AdminLoginResponse(
        success=True,
        message="登录成功",
        token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/profiles/pending", response_model=ResponseModel)
async def get_pending_profiles(
        page: int = 1,
        limit: int = 20,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    获取待审核列表
    """
    skip = (page - 1) * limit

    profiles = crud_profile.get_pending_profiles(db, skip=skip, limit=limit)

    data = []
    for profile in profiles:
        data.append({
            "id": profile.id,
            "serial_number": profile.serial_number,
            "name": profile.name,
            "gender": profile.gender,
            "age": profile.age,
            "work_location": profile.work_location,
            "create_time": profile.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": profile.status
        })

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "total": len(data),
            "page": page,
            "limit": limit,
            "list": data
        }
    )


@router.get("/profile/{profile_id}/detail", response_model=ResponseModel)
async def get_profile_detail(
        profile_id: int,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    获取资料详情
    """
    profile = crud_profile.get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    # 转换为dict
    profile_dict = {
        "id": profile.id,
        "openid": profile.openid,
        "serial_number": profile.serial_number,
        "name": profile.name,
        "gender": profile.gender,
        "age": profile.age,
        "height": profile.height,
        "weight": profile.weight,
        "marital_status": profile.marital_status,
        "body_type": profile.body_type,
        "hometown": profile.hometown,
        "work_location": profile.work_location,
        "industry": profile.industry,
        "constellation": profile.constellation,
        "mbti": profile.mbti,
        "health_condition": profile.health_condition,
        "housing_status": profile.housing_status,
        "hobbies": profile.hobbies,
        "lifestyle": profile.lifestyle,
        "coming_out_status": profile.coming_out_status,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
        "photos": profile.photos,
        "status": profile.status,
        "rejection_reason": profile.rejection_reason,
        "create_time": profile.create_time.strftime("%Y-%m-%d %H:%M:%S") if profile.create_time else None,
        "reviewed_at": profile.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if profile.reviewed_at else None,
        "reviewed_by": profile.reviewed_by,
        "review_notes": profile.review_notes,
        "invitation_code_used": profile.invitation_code_used,
        "admin_contact": profile.admin_contact
    }

    return ResponseModel(
        success=True,
        message="获取成功",
        data=profile_dict
    )


@router.get("/profile/{profile_id}/preview-post", response_model=ResponseModel)
async def preview_post(
        profile_id: int,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    预览公众号文案
    """
    profile = crud_profile.get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    # 转换为dict用于生成文案
    profile_dict = {
        "serial_number": profile.serial_number,
        "gender": profile.gender,
        "age": profile.age,
        "height": profile.height,
        "weight": profile.weight,
        "marital_status": profile.marital_status,
        "body_type": profile.body_type,
        "hometown": profile.hometown,
        "work_location": profile.work_location,
        "industry": profile.industry,
        "health_condition": profile.health_condition,
        "constellation": profile.constellation,
        "mbti": profile.mbti,
        "coming_out_status": profile.coming_out_status,
        "lifestyle": profile.lifestyle,
        "hobbies": profile.hobbies,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
        "admin_contact": profile.admin_contact,
        "photos": profile.photos
    }

    # 生成文案
    post = generate_post_content(profile_dict)

    return ResponseModel(
        success=True,
        message="生成成功",
        data=post
    )


@router.post("/profile/{profile_id}/approve", response_model=ResponseModel)
async def approve_profile(
        profile_id: int,
        request: ApproveRequest,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    通过审核
    """
    profile = crud_profile.get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    if profile.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许审核"
        )

    # 通过审核
    crud_profile.approve_profile(
        db=db,
        profile_id=profile_id,
        reviewed_by=admin.get('sub'),
        notes=request.notes
    )

    # 为用户生成邀请码
    generated_codes = []
    for _ in range(settings.DEFAULT_INVITATION_QUOTA):
        code = generate_invitation_code()
        expire_at = calculate_expire_time()

        crud_invitation.create_invitation_code(
            db=db,
            code=code,
            created_by=profile.id,
            created_by_type="user",
            notes=f"用户{profile.serial_number}的邀请码",
            expire_at=expire_at
        )
        generated_codes.append(code)

    # 更新用户的邀请配额
    crud_profile.update_profile(
        db=db,
        profile_id=profile.id,
        data={"invitation_quota": settings.DEFAULT_INVITATION_QUOTA}
    )

    return ResponseModel(
        success=True,
        message="审核通过",
        data={
            "generated_codes": generated_codes
        }
    )


@router.post("/profile/{profile_id}/reject", response_model=ResponseModel)
async def reject_profile(
        profile_id: int,
        request: RejectRequest,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    拒绝审核
    """
    profile = crud_profile.get_profile_by_id(db, profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    if profile.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许审核"
        )

    # 拒绝审核
    crud_profile.reject_profile(
        db=db,
        profile_id=profile_id,
        reviewed_by=admin.get('sub'),
        reason=request.reason
    )

    return ResponseModel(
        success=True,
        message="已拒绝"
    )


@router.post("/invitation/generate", response_model=ResponseModel)
async def generate_invitations(
        count: int = 10,
        expire_days: int = 7,
        notes: str = None,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    批量生成邀请码
    """
    if count > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="单次最多生成100个邀请码"
        )

    generated_codes = []
    expire_at = calculate_expire_time() if expire_days > 0 else None

    for _ in range(count):
        code = generate_invitation_code()

        crud_invitation.create_invitation_code(
            db=db,
            code=code,
            created_by=0,
            created_by_type="admin",
            notes=notes or "管理员生成",
            expire_at=expire_at
        )

        generated_codes.append(code)

    return ResponseModel(
        success=True,
        message=f"成功生成{count}个邀请码",
        data={
            "codes": generated_codes,
            "count": count
        }
    )