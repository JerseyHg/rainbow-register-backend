"""
用户资料相关API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_openid
from app.schemas.profile import ProfileSubmitRequest, ProfileResponse
from app.schemas.common import ResponseModel
from app.crud import crud_profile, crud_invitation
from app.utils.helpers import generate_serial_number, calculate_age, calculate_constellation
from app.models.invitation_code import InvitationCode
from app.core.config import settings
from app.services.invitation import generate_invitation_code, calculate_expire_time
import logging

from app.crud.crud_settings import get_setting_bool
from fastapi import BackgroundTasks
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


def _run_ai_review_background(profile_id: int):
    """
    后台执行 AI 审核
    ★ 开关判断在 trigger_ai_review 内部通过数据库查询完成
    ★ 如果开关关闭，trigger 会直接返回 skip，不会调用 AI
    """
    from app.db.base import SessionLocal
    from app.services.ai_review_trigger import trigger_ai_review
    from app.core.config import settings

    # 即使开关在数据库中，也需要 API_KEY 才有意义
    if not settings.AI_API_KEY:
        return

    db = None
    loop = None
    try:
        db = SessionLocal()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(trigger_ai_review(db, profile_id))
        logger.info(f"AI后台审核: profile_id={profile_id}, action={result['action']}")
    except Exception as e:
        logger.error(f"AI后台审核失败: profile_id={profile_id}, error={e}")
    finally:
        if db:
            db.close()
        if loop:
            loop.close()


def _cleanup_user_cos_photos(openid: str):
    """
    ★ 清理用户在COS上的所有照片
    删除 photos/{openid}/ 目录下所有文件
    静默失败，不影响主流程
    """
    try:
        if not settings.COS_SECRET_ID or not settings.COS_DOMAIN:
            return

        from qcloud_cos import CosConfig, CosS3Client

        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        client = CosS3Client(config)

        prefix = f"{settings.COS_UPLOAD_PREFIX}/{openid}/"

        response = client.list_objects(
            Bucket=settings.COS_BUCKET,
            Prefix=prefix,
            MaxKeys=100,
        )

        contents = response.get('Contents', [])
        if contents:
            delete_objects = [{'Key': obj['Key']} for obj in contents]
            client.delete_objects(
                Bucket=settings.COS_BUCKET,
                Delete={'Object': delete_objects, 'Quiet': 'true'},
            )
            logger.info(f"清理COS照片成功: {openid}, 共 {len(delete_objects)} 个文件")
    except Exception as e:
        logger.warning(f"清理COS照片失败（不影响删除操作）: {e}")


@router.post("/submit", response_model=ResponseModel)
async def submit_profile(
        request: ProfileSubmitRequest,
        background_tasks: BackgroundTasks,
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    提交用户资料
    """
    existing_profile = crud_profile.get_profile_by_openid(db, openid)

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经提交过资料，请使用更新接口"
        )

    last_number = crud_profile.get_last_serial_number(db)
    serial_number = generate_serial_number(last_number)

    profile_data = request.dict()
    profile_data['serial_number'] = serial_number
    profile_data['status'] = 'pending'

    if profile_data.get('birthday'):
        try:
            profile_data['age'] = calculate_age(profile_data['birthday'])
            profile_data['constellation'] = calculate_constellation(profile_data['birthday'])
        except (ValueError, TypeError):
            pass

    invitation = db.query(InvitationCode).filter(
        InvitationCode.used_by_openid == openid
    ).first()

    if invitation:
        profile_data['invitation_code_used'] = invitation.code
        if invitation.created_by_type == 'user' and invitation.created_by:
            referrer = crud_profile.get_profile_by_id(db, invitation.created_by)
            if referrer:
                profile_data['referred_by'] = f"{referrer.name}（{referrer.serial_number}）"
                profile_data['invited_by'] = referrer.id
            else:
                profile_data['referred_by'] = f"用户ID:{invitation.created_by}"
        elif invitation.created_by_type == 'admin':
            profile_data['referred_by'] = "管理员"

    if profile_data.get('expectation') and hasattr(profile_data['expectation'], 'dict'):
        profile_data['expectation'] = profile_data['expectation'].dict()

    profile = crud_profile.create_profile(db, openid, profile_data)

    # ★ 检查是否为审核放行邀请码（用于微信审核场景 - 自动通过）
    used_code = profile_data.get('invitation_code_used', '')
    bypass_codes = settings.REVIEW_BYPASS_CODES
    if bypass_codes and used_code.upper() in [c.upper() for c in bypass_codes]:
        # 自动通过审核
        crud_profile.approve_profile(
            db=db,
            profile_id=profile.id,
            reviewed_by="AUTO_BYPASS",
            notes="审核放行邀请码自动通过"
        )
        # 生成邀请码配额
        for _ in range(settings.DEFAULT_INVITATION_QUOTA):
            code = generate_invitation_code()
            expire_at = calculate_expire_time()
            crud_invitation.create_invitation_code(
                db=db, code=code, created_by=profile.id, created_by_type="user",
                notes=f"用户{profile.serial_number}的邀请码（放行）", expire_at=expire_at
            )
        crud_profile.update_profile(db=db, profile_id=profile.id,
                                    data={"invitation_quota": settings.DEFAULT_INVITATION_QUOTA})
        logger.info(f"放行邀请码自动通过: {used_code}, profile_id={profile.id}")

        return ResponseModel(
            success=True,
            message="提交成功，已自动通过审核",
            data={
                "profile_id": profile.id,
                "serial_number": profile.serial_number
            }
        )

    # ★ 检查是否为审核拒绝测试邀请码（用于微信审核场景 - 自动拒绝）
    reject_codes = settings.REVIEW_REJECT_CODES
    if reject_codes and used_code.upper() in [c.upper() for c in reject_codes]:
        crud_profile.reject_profile(
            db=db,
            profile_id=profile.id,
            reviewed_by="AUTO_TEST",
            reason="信息不完整，请补充以下内容后重新提交：\n\n1. 感情状态（如：单身、离异等）\n2. 健康状况\n3. 住房情况\n4. 交友目的\n5. 出柜状态"
        )
        logger.info(f"拒绝测试邀请码自动拒绝: {used_code}, profile_id={profile.id}")

        return ResponseModel(
            success=True,
            message="提交成功",
            data={
                "profile_id": profile.id,
                "serial_number": profile.serial_number
            }
        )

    background_tasks.add_task(_run_ai_review_background, profile.id)

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
            "invitation_quota": profile.invitation_quota,
            "name": profile.name,
            "gender": profile.gender,
            "birthday": profile.birthday,
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
            "wechat_id": profile.wechat_id,
            "hobbies": profile.hobbies,
            "lifestyle": profile.lifestyle,
            "activity_expectation": profile.activity_expectation,
            "special_requirements": profile.special_requirements,
            "photos": profile.photos,
        }
    )


@router.put("/update", response_model=ResponseModel)
async def update_profile(
        request: ProfileSubmitRequest,
        background_tasks: BackgroundTasks,
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

    if profile.status not in ['pending', 'rejected']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许修改"
        )

    update_data = request.dict()

    if update_data.get('birthday'):
        try:
            update_data['age'] = calculate_age(update_data['birthday'])
            update_data['constellation'] = calculate_constellation(update_data['birthday'])
        except (ValueError, TypeError):
            pass

    if profile.status == 'rejected':
        update_data['status'] = 'pending'
        update_data['rejection_reason'] = None

    if update_data.get('expectation'):
        update_data['expectation'] = update_data['expectation'].dict()

    updated_profile = crud_profile.update_profile(db, profile.id, update_data)

    background_tasks.add_task(_run_ai_review_background, updated_profile.id)

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

    if profile.status not in ['approved', 'published']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许下架"
        )

    crud_profile.update_profile(db, profile.id, {"status": "archived"})

    return ResponseModel(
        success=True,
        message="已下架"
    )


@router.delete("/delete", response_model=ResponseModel)
async def delete_profile(
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    删除资料
    ★ 支持 pending、rejected、approved、published 状态
    ★ 删除时自动清理COS上该用户所有照片
    """
    profile = crud_profile.get_profile_by_openid(db, openid)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="资料不存在"
        )

    allowed_statuses = ['pending', 'rejected', 'approved', 'published']
    if profile.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态({profile.status})不允许删除"
        )

    # ★ 清理COS上该用户的所有照片（按目录批量删除）
    _cleanup_user_cos_photos(openid)

    # 删除数据库记录
    crud_profile.delete_profile(db, profile.id)

    return ResponseModel(
        success=True,
        message="已删除"
    )


@router.get("/ai-review-enabled", response_model=ResponseModel)
async def get_ai_review_enabled(db: Session = Depends(get_db)):
    """
    公开端点：查询 AI 自动审核是否开启
    小程序前端用于判断是否需要预填模板
    """
    enabled = get_setting_bool(db, "ai_auto_review")
    return ResponseModel(success=True, message="ok", data={"enabled": enabled})
