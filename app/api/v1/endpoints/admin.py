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
from app.models.user_profile import UserProfile
from app.models.invitation_code import InvitationCode
from datetime import timedelta
from collections import defaultdict
from app.core.city_coordinates import CITY_COORDINATES

from app.crud.crud_settings import get_all_settings, get_setting, set_setting, get_setting_bool
from app.services.ai_review_trigger import trigger_ai_review
from app.services.ai_post_generator import generate_ai_post_html

logger = logging.getLogger(__name__)

router = APIRouter()

def _generate_post_background(profile_id: int):
    """后台异步生成 AI 文案并上传 COS，保存链接到数据库"""
    from app.db.base import SessionLocal
    db = None
    loop = None
    try:
        db = SessionLocal()
        profile = crud_profile.get_profile_by_id(db, profile_id)
        if not profile:
            return

        profile_dict = {
            "serial_number": profile.serial_number,
            "gender": profile.gender, "age": profile.age,
            "height": profile.height, "weight": profile.weight,
            "marital_status": profile.marital_status,
            "body_type": profile.body_type,
            "hometown": profile.hometown,
            "work_location": profile.work_location,
            "industry": profile.industry,
            "health_condition": profile.health_condition,
            "constellation": profile.constellation,
            "mbti": profile.mbti,
            "coming_out_status": profile.coming_out_status,
            "dating_purpose": profile.dating_purpose,
            "want_children": profile.want_children,
            "lifestyle": profile.lifestyle,
            "activity_expectation": profile.activity_expectation,
            "hobbies": profile.hobbies,
            "expectation": profile.expectation,
            "special_requirements": profile.special_requirements,
            "admin_contact": profile.admin_contact,
            "photos": profile.photos,
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_ai_post_html(profile_dict))
        html_content = result["html"]

        # 上传 COS
        cos_url = None
        try:
            from qcloud_cos import CosConfig, CosS3Client
            import uuid
            config = CosConfig(
                Region=settings.COS_REGION,
                SecretId=settings.COS_SECRET_ID,
                SecretKey=settings.COS_SECRET_KEY,
            )
            client = CosS3Client(config)
            file_id = uuid.uuid4().hex[:8]
            cos_key = f"posts/{profile.serial_number}/{file_id}.html"
            client.put_object(
                Bucket=settings.COS_BUCKET,
                Body=html_content.encode("utf-8"),
                Key=cos_key,
                ContentType="text/html; charset=utf-8",
            )
            cos_url = f"{settings.COS_DOMAIN}/{cos_key}"
        except Exception as e:
            logger.warning(f"文案COS上传失败: {e}")

        if cos_url:
            crud_profile.update_profile(db, profile_id, {"post_url": cos_url})
            logger.info(f"AI文案已生成: profile_id={profile_id}, url={cos_url}")
        else:
            logger.warning(f"AI文案COS上传失败: profile_id={profile_id}")

    except Exception as e:
        logger.error(f"后台生成文案失败: profile_id={profile_id}, error={e}")
    finally:
        if db:
            db.close()
        if loop:
            loop.close()

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
        request: AdminLoginRequest,
        db: Session = Depends(get_db)
):
    """管理员登录"""
    admin = crud_admin.get_admin_by_username(db, request.username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    access_token = create_access_token(data={"sub": admin.username, "admin_id": admin.id})
    crud_admin.update_last_login(db, admin.id)

    return AdminLoginResponse(
        success=True, message="登录成功",
        token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/profiles/pending", response_model=ResponseModel)
async def get_pending_profiles(
        page: int = 1, limit: int = 20,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取待审核列表"""
    skip = (page - 1) * limit
    profiles = crud_profile.get_pending_profiles(db, skip=skip, limit=limit)
    data = []
    for profile in profiles:
        data.append({
            "id": profile.id, "serial_number": profile.serial_number,
            "name": profile.name, "gender": profile.gender, "age": profile.age,
            "work_location": profile.work_location,
            "create_time": profile.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": profile.status
        })
    return ResponseModel(success=True, message="获取成功",
                         data={"total": len(data), "page": page, "limit": limit, "list": data})


@router.get("/profiles/list", response_model=ResponseModel)
async def list_profiles(
        status: str = "pending", page: int = 1, limit: int = 20,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """按状态获取资料列表"""
    skip = (page - 1) * limit
    query = db.query(UserProfile)
    if status != "all":
        query = query.filter(UserProfile.status == status)
    profiles = query.order_by(UserProfile.create_time.desc()).offset(skip).limit(limit).all()
    total = query.count()
    data = []
    for profile in profiles:
        data.append({
            "id": profile.id, "serial_number": profile.serial_number,
            "name": profile.name, "gender": profile.gender, "age": profile.age,
            "work_location": profile.work_location,
            "create_time": profile.create_time.strftime("%Y-%m-%d %H:%M:%S") if profile.create_time else None,
            "status": profile.status,
        })
    return ResponseModel(success=True, message="获取成功",
                         data={"total": total, "page": page, "limit": limit, "list": data})


@router.get("/profile/{profile_id}/detail", response_model=ResponseModel)
async def get_profile_detail(
        profile_id: int,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取资料详情"""
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")

    profile_dict = {
        "id": profile.id,
        "openid": profile.openid,
        "serial_number": profile.serial_number,
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
        "housing_status": profile.housing_status,
        "dating_purpose": profile.dating_purpose,
        "want_children": profile.want_children,
        "wechat_id": profile.wechat_id,
        "referred_by": profile.referred_by,
        "hobbies": profile.hobbies,
        "lifestyle": profile.lifestyle,
        "activity_expectation": profile.activity_expectation,
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

    return ResponseModel(success=True, message="获取成功", data=profile_dict)


@router.get("/profile/{profile_id}/preview-post", response_model=ResponseModel)
async def preview_post(
        profile_id: int,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """预览公众号文案 — 优先返回 AI 生成的文案"""
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")

    # ★ 如果有 AI 文案链接，直接返回
    if profile.post_url:
        return ResponseModel(success=True, message="获取成功", data={
            "title": f"档案 №{profile.serial_number}",
            "content": "",
            "post_url": profile.post_url,
            "ai_generated": True,
        })

    # 没有 AI 文案，用旧模板
    profile_dict = {
        "serial_number": profile.serial_number,
        "gender": profile.gender, "age": profile.age,
        "height": profile.height, "weight": profile.weight,
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
        "activity_expectation": profile.activity_expectation,
        "hobbies": profile.hobbies,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
        "admin_contact": profile.admin_contact,
        "photos": profile.photos,
    }
    post = generate_post_content(profile_dict)
    post["post_url"] = None
    post["ai_generated"] = False
    return ResponseModel(success=True, message="生成成功", data=post)


@router.post("/profile/{profile_id}/generate-post", response_model=ResponseModel)
async def generate_post_file(
        profile_id: int,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """手动生成/重新生成 AI 文案 HTML → 上传 COS → 保存链接"""
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="资料不存在")

    profile_dict = {
        "serial_number": profile.serial_number,
        "gender": profile.gender, "age": profile.age,
        "height": profile.height, "weight": profile.weight,
        "marital_status": profile.marital_status,
        "body_type": profile.body_type,
        "hometown": profile.hometown,
        "work_location": profile.work_location,
        "industry": profile.industry,
        "health_condition": profile.health_condition,
        "constellation": profile.constellation,
        "mbti": profile.mbti,
        "coming_out_status": profile.coming_out_status,
        "dating_purpose": profile.dating_purpose,
        "want_children": profile.want_children,
        "lifestyle": profile.lifestyle,
        "activity_expectation": profile.activity_expectation,
        "hobbies": profile.hobbies,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
        "admin_contact": profile.admin_contact,
        "photos": profile.photos,
    }

    result = await generate_ai_post_html(profile_dict)
    html_content = result["html"]

    # 上传到 COS
    cos_url = None
    try:
        from qcloud_cos import CosConfig, CosS3Client
        import uuid
        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        client = CosS3Client(config)
        file_id = uuid.uuid4().hex[:8]
        cos_key = f"posts/{profile.serial_number}/{file_id}.html"
        client.put_object(
            Bucket=settings.COS_BUCKET,
            Body=html_content.encode("utf-8"),
            Key=cos_key,
            ContentType="text/html; charset=utf-8",
        )
        cos_url = f"{settings.COS_DOMAIN}/{cos_key}"

        # ★ 保存链接到数据库
        crud_profile.update_profile(db, profile_id, {"post_url": cos_url})
    except Exception as e:
        logger.warning(f"COS上传失败: {e}")

    return ResponseModel(
        success=True,
        message="文案生成成功",
        data={
            "title": result.get("title", f"档案 №{profile.serial_number}"),
            "ai_generated": result["ai_generated"],
            "html": html_content,
            "download_url": cos_url,
            "serial_number": profile.serial_number,
        },
    )


@router.post("/profile/{profile_id}/approve", response_model=ResponseModel)
async def approve_profile(
        profile_id: int, request: ApproveRequest,
        background_tasks: BackgroundTasks,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """通过审核"""
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
    if profile.status != 'pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"当前状态({profile.status})不允许审核")

    crud_profile.approve_profile(db=db, profile_id=profile_id,
                                 reviewed_by=admin.get('sub'), notes=request.notes)

    generated_codes = []
    for _ in range(settings.DEFAULT_INVITATION_QUOTA):
        code = generate_invitation_code()
        expire_at = calculate_expire_time()
        crud_invitation.create_invitation_code(
            db=db, code=code, created_by=profile.id, created_by_type="user",
            notes=f"用户{profile.serial_number}的邀请码", expire_at=expire_at
        )
        generated_codes.append(code)

    crud_profile.update_profile(db=db, profile_id=profile.id,
                                data={"invitation_quota": settings.DEFAULT_INVITATION_QUOTA})

    # ★ 审核通过后自动生成 AI 文案（后台异步，不阻塞响应）
    background_tasks.add_task(_generate_post_background, profile_id)

    return ResponseModel(success=True, message="审核通过", data={"generated_codes": generated_codes})


@router.post("/profile/{profile_id}/reject", response_model=ResponseModel)
async def reject_profile(
        profile_id: int, request: RejectRequest,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """拒绝审核"""
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
    if profile.status != 'pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"当前状态({profile.status})不允许审核")

    crud_profile.reject_profile(db=db, profile_id=profile_id,
                                reviewed_by=admin.get('sub'), reason=request.reason)
    return ResponseModel(success=True, message="已拒绝")


@router.post("/invitation/generate", response_model=ResponseModel)
async def generate_invitations(
        count: int = 10, expire_days: int = 7, notes: str = None,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """批量生成邀请码"""
    if count > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单次最多生成100个邀请码")

    generated_codes = []
    expire_at = calculate_expire_time() if expire_days > 0 else None
    for _ in range(count):
        code = generate_invitation_code()
        crud_invitation.create_invitation_code(
            db=db, code=code, created_by=0, created_by_type="admin",
            notes=notes or "管理员生成", expire_at=expire_at
        )
        generated_codes.append(code)

    return ResponseModel(success=True, message=f"成功生成{count}个邀请码",
                         data={"codes": generated_codes, "count": count})


@router.get("/dashboard/stats", response_model=ResponseModel)
async def get_dashboard_stats(
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """仪表盘统计"""
    pending = db.query(UserProfile).filter(UserProfile.status == 'pending').count()
    approved = db.query(UserProfile).filter(UserProfile.status == 'approved').count()
    published = db.query(UserProfile).filter(UserProfile.status == 'published').count()
    total_codes = db.query(InvitationCode).count()
    used_codes = db.query(InvitationCode).filter(InvitationCode.is_used == True).count()
    return ResponseModel(success=True, message="获取成功", data={
        "pending": pending, "approved": approved, "published": published,
        "totalCodes": total_codes, "usedCodes": used_codes
    })


@router.get("/invitation/list", response_model=ResponseModel)
async def list_invitations(
        page: int = 1, limit: int = 50,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取邀请码列表"""
    skip = (page - 1) * limit
    invitations = db.query(InvitationCode).order_by(InvitationCode.create_time.desc()).offset(skip).limit(limit).all()
    data = []
    for inv in invitations:
        data.append({
            "code": inv.code, "is_used": inv.is_used, "created_by_type": inv.created_by_type,
            "notes": inv.notes,
            "created_at": inv.create_time.strftime("%Y-%m-%d %H:%M:%S") if inv.create_time else None,
            "used_at": inv.used_at.strftime("%Y-%m-%d %H:%M:%S") if inv.used_at else None,
        })
    return ResponseModel(success=True, message="获取成功", data={"list": data, "total": len(data)})


@router.get("/network/tree", response_model=ResponseModel)
async def get_invitation_network(
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取邀请关系网络树"""
    all_profiles = db.query(UserProfile).order_by(UserProfile.create_time.asc()).all()
    profile_map = {p.id: p for p in all_profiles}

    children_map = {}
    root_profiles = []
    for p in all_profiles:
        if p.invited_by and p.invited_by in profile_map:
            children_map.setdefault(p.invited_by, []).append(p)
        else:
            root_profiles.append(p)

    def calc_quality(user_id):
        children = children_map.get(user_id, [])
        if not children:
            return {"invited_count": 0, "approved_count": 0, "rejected_count": 0,
                    "pending_count": 0, "approval_rate": None, "quality_score": None, "quality_label": "无邀请"}
        approved = sum(1 for c in children if c.status in ('approved', 'published'))
        rejected = sum(1 for c in children if c.status == 'rejected')
        pending = sum(1 for c in children if c.status == 'pending')
        total = len(children)
        reviewed = approved + rejected
        approval_rate = round(approved / reviewed * 100, 1) if reviewed > 0 else None
        if reviewed == 0:
            score, label = None, "待评估"
        elif approval_rate >= 80:
            score, label = "A", "优质"
        elif approval_rate >= 60:
            score, label = "B", "良好"
        elif approval_rate >= 40:
            score, label = "C", "一般"
        else:
            score, label = "D", "较差"
        return {"invited_count": total, "approved_count": approved, "rejected_count": rejected,
                "pending_count": pending, "approval_rate": approval_rate,
                "quality_score": score, "quality_label": label}

    def build_node(profile, depth=0):
        children = children_map.get(profile.id, [])
        quality = calc_quality(profile.id)
        child_nodes = [build_node(c, depth + 1) for c in children]
        descendant_count = sum(cn["descendant_count"] + 1 for cn in child_nodes)
        return {
            "id": profile.id, "serial_number": profile.serial_number,
            "name": profile.name, "gender": profile.gender, "age": profile.age,
            "work_location": profile.work_location, "status": profile.status,
            "create_time": profile.create_time.strftime("%Y-%m-%d") if profile.create_time else None,
            "referred_by": profile.referred_by, "depth": depth,
            "quality": quality, "descendant_count": descendant_count, "children": child_nodes,
        }

    tree = [build_node(p, 0) for p in root_profiles]

    total_users = len(all_profiles)
    total_approved = sum(1 for p in all_profiles if p.status in ('approved', 'published'))
    total_rejected = sum(1 for p in all_profiles if p.status == 'rejected')
    total_pending = sum(1 for p in all_profiles if p.status == 'pending')

    inviters = []
    for p in all_profiles:
        q = calc_quality(p.id)
        if q["invited_count"] > 0:
            inviters.append({"id": p.id, "name": p.name, "serial_number": p.serial_number, **q})
    inviters.sort(key=lambda x: (x["approval_rate"] or 0), reverse=True)

    def max_depth(nodes, current=0):
        if not nodes:
            return current
        return max(max_depth(n.get("children", []), current + 1) for n in nodes)

    stats = {
        "total_users": total_users, "total_approved": total_approved,
        "total_rejected": total_rejected, "total_pending": total_pending,
        "overall_approval_rate": round(total_approved / (total_approved + total_rejected) * 100, 1) if (total_approved + total_rejected) > 0 else 0,
        "max_depth": max_depth(tree),
        "top_inviters": inviters[:5],
        "worst_inviters": list(reversed(inviters[-3:])) if len(inviters) >= 3 else [],
    }
    return ResponseModel(success=True, message="获取成功", data={"tree": tree, "stats": stats})


@router.get("/network/user/{user_id}", response_model=ResponseModel)
async def get_user_network_detail(
        user_id: int,
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取单个用户的邀请网络详情"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")

    invitees = db.query(UserProfile).filter(UserProfile.invited_by == user_id).all()

    inviter = None
    if profile.invited_by:
        inviter_profile = db.query(UserProfile).filter(UserProfile.id == profile.invited_by).first()
        if inviter_profile:
            inviter = {"id": inviter_profile.id, "name": inviter_profile.name,
                       "serial_number": inviter_profile.serial_number, "status": inviter_profile.status}

    invitee_list = []
    for inv in invitees:
        invitee_list.append({
            "id": inv.id, "name": inv.name, "serial_number": inv.serial_number,
            "gender": inv.gender, "age": inv.age, "work_location": inv.work_location,
            "status": inv.status,
            "create_time": inv.create_time.strftime("%Y-%m-%d") if inv.create_time else None,
        })

    approved = sum(1 for i in invitees if i.status in ('approved', 'published'))
    rejected = sum(1 for i in invitees if i.status == 'rejected')
    reviewed = approved + rejected

    return ResponseModel(success=True, message="获取成功", data={
        "user": {
            "id": profile.id, "name": profile.name, "serial_number": profile.serial_number,
            "gender": profile.gender, "age": profile.age, "work_location": profile.work_location,
            "status": profile.status,
            "create_time": profile.create_time.strftime("%Y-%m-%d") if profile.create_time else None,
            "referred_by": profile.referred_by,
        },
        "inviter": inviter, "invitees": invitee_list,
        "quality": {"invited_count": len(invitees), "approved_count": approved,
                     "rejected_count": rejected,
                     "approval_rate": round(approved / reviewed * 100, 1) if reviewed > 0 else None}
    })


def extract_city(work_location: str) -> str | None:
    """从 work_location 提取城市名"""
    if not work_location:
        return None
    loc = work_location.strip()
    for city_name in sorted(CITY_COORDINATES.keys(), key=len, reverse=True):
        if loc.startswith(city_name):
            return city_name
    if len(loc) >= 3 and loc[:3] in CITY_COORDINATES:
        return loc[:3]
    if len(loc) >= 2 and loc[:2] in CITY_COORDINATES:
        return loc[:2]
    return loc


@router.get("/map/users", response_model=ResponseModel)
async def get_map_users(
        admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)
):
    """获取用户地理分布数据"""
    all_profiles = db.query(UserProfile).filter(
        UserProfile.work_location.isnot(None), UserProfile.work_location != ""
    ).all()

    city_groups = defaultdict(list)
    for p in all_profiles:
        city = extract_city(p.work_location)
        if city:
            city_groups[city].append(p)

    cities = []
    for city_name, profiles in city_groups.items():
        coords = CITY_COORDINATES.get(city_name)
        lat = coords[0] if coords else None
        lng = coords[1] if coords else None
        status_counts = {"approved": 0, "published": 0, "pending": 0, "rejected": 0}
        users = []
        for p in profiles:
            if p.status in status_counts:
                status_counts[p.status] += 1
            users.append({
                "id": p.id, "name": p.name, "serial_number": p.serial_number,
                "gender": p.gender, "age": p.age, "status": p.status,
                "work_location": p.work_location, "industry": p.industry,
            })
        cities.append({"city": city_name, "lat": lat, "lng": lng, "count": len(profiles),
                        "status_counts": status_counts, "users": users})

    cities.sort(key=lambda x: x["count"], reverse=True)
    total_users = sum(c["count"] for c in cities)
    total_cities = len([c for c in cities if c["lat"]])

    return ResponseModel(success=True, message="获取成功", data={
        "cities": cities,
        "stats": {"total_users": total_users, "total_cities": total_cities,
                  "top_city": cities[0]["city"] if cities else None,
                  "top_city_count": cities[0]["count"] if cities else 0}
    })

# ============================================================
# 新增端点：系统设置（AI审核开关等）
# ============================================================

@router.get("/settings", response_model=ResponseModel)
async def get_system_settings(
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """获取所有系统设置"""
    all_settings = get_all_settings(db)
    return ResponseModel(success=True, message="获取成功", data=all_settings)

@router.post("/settings/{key}", response_model=ResponseModel)
async def update_system_setting(
        key: str,
        request: dict,  # {"value": "true"}
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """更新单个系统设置"""
    value = request.get("value")
    if value is None:
        raise HTTPException(status_code=400, detail="缺少 value 参数")

    row = set_setting(db, key=key, value=str(value), updated_by=admin.get("sub", "admin"))
    return ResponseModel(success=True, message=f"设置 {key} 已更新", data={
        "key": row.key,
        "value": row.value,
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else None,
    })


@router.get("/settings/ai-review/status", response_model=ResponseModel)
async def get_ai_review_status(
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """获取 AI 审核开关状态（便捷端点）"""
    enabled = get_setting_bool(db, "ai_auto_review")
    return ResponseModel(success=True, message="获取成功", data={"enabled": enabled})


@router.post("/settings/ai-review/toggle", response_model=ResponseModel)
async def toggle_ai_review(
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """切换 AI 审核开关"""
    current = get_setting_bool(db, "ai_auto_review")
    new_value = "false" if current else "true"
    set_setting(db, key="ai_auto_review", value=new_value, updated_by=admin.get("sub", "admin"))

    status_text = "已开启" if new_value == "true" else "已关闭"
    return ResponseModel(success=True, message=f"AI 自动审核{status_text}", data={
        "enabled": new_value == "true",
    })

# ============================================================
# 新增端点：手动触发 AI 审核
# ============================================================

@router.post("/profile/{profile_id}/ai-review", response_model=ResponseModel)
async def manual_ai_review(
        profile_id: int,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """
    手动触发单个资料的 AI 审核
    ★ 注意：手动触发不受开关限制，始终执行
    """
    from app.services.ai_review import auto_review_profile
    from app.crud import crud_profile as _crud

    profile = _crud.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="资料不存在")
    if profile.status != "pending":
        raise HTTPException(status_code=400, detail=f"当前状态({profile.status})不允许审核")

    # 直接调用 AI 审核核心逻辑（绕过开关检查）
    profile_data = {
        "name": profile.name, "gender": profile.gender, "age": profile.age,
        "height": profile.height, "weight": profile.weight,
        "marital_status": profile.marital_status, "body_type": profile.body_type,
        "hometown": profile.hometown, "work_location": profile.work_location,
        "industry": profile.industry, "constellation": profile.constellation,
        "mbti": profile.mbti, "health_condition": profile.health_condition,
        "housing_status": profile.housing_status, "dating_purpose": profile.dating_purpose,
        "want_children": profile.want_children, "wechat_id": profile.wechat_id,
        "coming_out_status": profile.coming_out_status, "hobbies": profile.hobbies,
        "lifestyle": profile.lifestyle, "activity_expectation": profile.activity_expectation,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
    }

    action, reason, extracted = await auto_review_profile(profile_data)

    if action == "reject":
        _crud.reject_profile(db, profile_id, reviewed_by="AI_MANUAL", reason=reason)
        return ResponseModel(success=True, message="AI已拒绝", data={"action": "reject", "reason": reason})
    elif action == "pass":
        if extracted:
            update_data = {}
            for field in ["marital_status", "health_condition", "housing_status",
                          "dating_purpose", "want_children", "coming_out_status"]:
                new_val = extracted.get(field)
                old_val = getattr(profile, field, None)
                if new_val and isinstance(new_val, str) and new_val.strip() and not old_val:
                    update_data[field] = new_val.strip()
            if extracted.get("expectation"):
                import json
                old_exp = profile.expectation or {}
                if isinstance(old_exp, str):
                    try: old_exp = json.loads(old_exp)
                    except: old_exp = {}
                merged = {**old_exp}
                for k, v in extracted["expectation"].items():
                    if v and isinstance(v, str) and v.strip() and not merged.get(k):
                        merged[k] = v.strip()
                update_data["expectation"] = merged
            update_data["review_notes"] = "AI手动审核-已提取补充信息"
            if update_data:
                _crud.update_profile(db, profile_id, update_data)
        return ResponseModel(success=True, message="AI审核通过，等待终审",
                             data={"action": "pass", "extracted_fields": extracted})
    else:
        return ResponseModel(success=True, message="AI分析异常", data={"action": "error"})


@router.post("/ai-review/batch", response_model=ResponseModel)
async def batch_ai_review(
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """批量对所有 pending 资料触发 AI 审核（不受开关限制）"""
    pending = crud_profile.get_pending_profiles(db, skip=0, limit=100)
    results = {"total": len(pending), "rejected": 0, "passed": 0, "errors": 0, "details": []}

    for p in pending:
        try:
            # 手动批量触发也绕过开关
            result = await trigger_ai_review.__wrapped__(db, p.id) if hasattr(trigger_ai_review, '__wrapped__') else await trigger_ai_review(db, p.id)
            action = result["action"]
            if action == "reject":
                results["rejected"] += 1
            elif action == "pass":
                results["passed"] += 1
            else:
                results["errors"] += 1
            results["details"].append({"id": p.id, "name": p.name, "action": action})
        except Exception as e:
            logger.error(f"批量审核失败 id={p.id}: {e}")
            results["errors"] += 1
            results["details"].append({"id": p.id, "name": p.name, "action": "error"})

    return ResponseModel(success=True, message="批量审核完成", data=results)

@router.post("/profile/{profile_id}/generate-post", response_model=ResponseModel)
async def generate_post_file(
        profile_id: int,
        admin: dict = Depends(get_current_admin),
        db: Session = Depends(get_db),
):
    """
    AI 生成公众号文案 HTML 文件，上传到 COS
    返回下载链接
    """
    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="资料不存在")

    # 构造 profile dict
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
        "dating_purpose": profile.dating_purpose,
        "want_children": profile.want_children,
        "lifestyle": profile.lifestyle,
        "activity_expectation": profile.activity_expectation,
        "hobbies": profile.hobbies,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
        "admin_contact": profile.admin_contact,
        "photos": profile.photos,
    }

    # 生成 HTML
    result = await generate_ai_post_html(profile_dict)
    html_content = result["html"]
    title = result["title"]

    # 上传到 COS
    cos_url = None
    try:
        from qcloud_cos import CosConfig, CosS3Client
        from io import BytesIO
        import uuid

        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        client = CosS3Client(config)

        file_id = uuid.uuid4().hex[:8]
        cos_key = f"posts/{profile.serial_number}/{file_id}.html"

        client.put_object(
            Bucket=settings.COS_BUCKET,
            Body=html_content.encode("utf-8"),
            Key=cos_key,
            ContentType="text/html; charset=utf-8",
        )

        cos_url = f"{settings.COS_DOMAIN}/{cos_key}"
        logger.info(f"文案已上传: {cos_url}")

    except Exception as e:
        logger.warning(f"COS上传失败（返回HTML内容）: {e}")

    return ResponseModel(
        success=True,
        message="文案生成成功",
        data={
            "title": title,
            "ai_generated": result["ai_generated"],
            "html": html_content,
            "download_url": cos_url,
            "serial_number": profile.serial_number,
        },
    )
