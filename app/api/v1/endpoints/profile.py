"""
用户资料相关API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_openid
from app.schemas.profile import ProfileSubmitRequest, ProfileResponse
from app.schemas.common import ResponseModel
from app.crud import crud_profile, crud_invitation
from app.utils.helpers import generate_serial_number
from app.core.config import settings
from app.services.invitation import generate_invitation_code, calculate_expire_time

router = APIRouter()


@router.post("/submit", response_model=ResponseModel)
async def submit_profile(
        request: ProfileSubmitRequest,
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    提交用户资料
    """
    # 1. 检查用户是否已经提交过资料
    existing_profile = crud_profile.get_profile_by_openid(db, openid)

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经提交过资料，请使用更新接口"
        )

    # 2. 生成编号
    last_number = crud_profile.get_last_serial_number(db)
    serial_number = generate_serial_number(last_number)

    # 3. 准备数据
    profile_data = request.dict()
    profile_data['serial_number'] = serial_number
    profile_data['status'] = 'pending'

    # 将expectation对象转为dict（JSON存储）
    if profile_data.get('expectation'):
        profile_data['expectation'] = profile_data['expectation'].dict()

    # 4. 创建资料
    profile = crud_profile.create_profile(db, openid, profile_data)

    return ResponseModel(
        success=True,
        message="提交成功，等待审核",
        data={
            "profile_id": profile.id,
            "serial_number": profile.serial_number
        }
    )


@router.get("/my", response_model=ResponseModel)
async def get_my_profile(
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    获取我的资料
    """
    profile = crud_profile.get_profile_by_openid(db, openid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "id": profile.id,
            "serial_number": profile.serial_number,
            "status": profile.status,
            "rejection_reason": profile.rejection_reason,
            "create_time": profile.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "published_at": profile.published_at.strftime("%Y-%m-%d %H:%M:%S") if profile.published_at else None,
            "invitation_quota": profile.invitation_quota
        }
    )


@router.put("/update", response_model=ResponseModel)
async def update_profile(
        request: ProfileSubmitRequest,
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    更新资料（仅pending或rejected状态可更新）
    """
    profile = crud_profile.get_profile_by_openid(db, openid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    # 只有pending或rejected状态可以修改
    if profile.status not in ['pending', 'rejected']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许修改"
        )

    # 准备更新数据
    update_data = request.dict()

    # 如果是rejected状态，更新后改为pending
    if profile.status == 'rejected':
        update_data['status'] = 'pending'
        update_data['rejection_reason'] = None

    # 转换expectation
    if update_data.get('expectation'):
        update_data['expectation'] = update_data['expectation'].dict()

    # 更新
    updated_profile = crud_profile.update_profile(db, profile.id, update_data)

    return ResponseModel(
        success=True,
        message="更新成功",
        data={
            "profile_id": updated_profile.id,
            "status": updated_profile.status
        }
    )


@router.post("/archive", response_model=ResponseModel)
async def archive_profile(
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    下架资料
    """
    profile = crud_profile.get_profile_by_openid(db, openid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    # 只有published状态可以下架
    if profile.status != 'published':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已发布的资料可以下架"
        )

    # 更新状态
    crud_profile.update_profile(db, profile.id, {"status": "archived"})

    return ResponseModel(
        success=True,
        message="已下架"
    )