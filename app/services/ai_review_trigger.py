"""
AI 审核触发器（v2 - 支持动态开关）
在资料提交/更新后自动触发 AI 审核
★ 通过数据库 system_settings 表的 ai_auto_review 控制开关
"""
import logging
from sqlalchemy.orm import Session
from app.services.ai_review import auto_review_profile
from app.crud import crud_profile
from app.crud.crud_settings import get_setting_bool

logger = logging.getLogger(__name__)


def is_ai_review_enabled(db: Session) -> bool:
    """检查 AI 自动审核是否开启（从数据库读取）"""
    return get_setting_bool(db, "ai_auto_review")


async def trigger_ai_review(db: Session, profile_id: int) -> dict:
    """
    触发 AI 自动审核

    返回:
        {
            "action": "reject" | "pass" | "error" | "skip",
            "message": str,
            "extracted_fields": dict | None
        }
    """
    # ★ 先检查开关
    if not is_ai_review_enabled(db):
        logger.info(f"AI 自动审核已关闭，跳过: profile_id={profile_id}")
        return {"action": "skip", "message": "AI自动审核已关闭", "extracted_fields": None}

    profile = crud_profile.get_profile_by_id(db, profile_id)
    if not profile:
        return {"action": "skip", "message": "资料不存在", "extracted_fields": None}

    if profile.status != "pending":
        return {"action": "skip", "message": f"当前状态({profile.status})无需审核", "extracted_fields": None}

    # 构造 profile_data 字典
    profile_data = {
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
        "dating_purpose": profile.dating_purpose,
        "want_children": profile.want_children,
        "wechat_id": profile.wechat_id,
        "coming_out_status": profile.coming_out_status,
        "hobbies": profile.hobbies,
        "lifestyle": profile.lifestyle,
        "activity_expectation": profile.activity_expectation,
        "expectation": profile.expectation,
        "special_requirements": profile.special_requirements,
    }

    # 调用 AI 审核
    action, reason, extracted = await auto_review_profile(profile_data)

    if action == "reject":
        crud_profile.reject_profile(
            db=db,
            profile_id=profile_id,
            reviewed_by="AI_AUTO_REVIEW",
            reason=reason,
        )
        logger.info(f"AI 自动拒绝: profile_id={profile_id}")
        return {"action": "reject", "message": reason, "extracted_fields": None}

    elif action == "pass":
        if extracted:
            update_data = {}

            for field in ["marital_status", "health_condition", "housing_status",
                          "dating_purpose", "want_children", "coming_out_status"]:
                new_val = extracted.get(field)
                old_val = getattr(profile, field, None)
                if new_val and isinstance(new_val, str) and new_val.strip() and not old_val:
                    update_data[field] = new_val.strip()

            new_exp = extracted.get("expectation")
            if new_exp and isinstance(new_exp, dict):
                import json
                old_exp = profile.expectation or {}
                if isinstance(old_exp, str):
                    try:
                        old_exp = json.loads(old_exp)
                    except (json.JSONDecodeError, TypeError):
                        old_exp = {}

                merged_exp = {**old_exp}
                for k, v in new_exp.items():
                    if v and isinstance(v, str) and v.strip():
                        if not merged_exp.get(k):
                            merged_exp[k] = v.strip()
                update_data["expectation"] = merged_exp

            update_data["review_notes"] = "AI已自动提取补充信息，等待管理员终审"

            if update_data:
                crud_profile.update_profile(db, profile_id, update_data)
                logger.info(f"AI 回填 {len(update_data)} 个字段: profile_id={profile_id}")

        return {
            "action": "pass",
            "message": "AI 审核通过，等待管理员终审",
            "extracted_fields": extracted,
        }

    else:
        crud_profile.update_profile(db, profile_id, {
            "review_notes": "AI审核异常，请管理员手动审核"
        })
        logger.warning(f"AI 审核出错，跳过: profile_id={profile_id}")
        return {"action": "error", "message": "AI审核异常，请管理员手动审核", "extracted_fields": None}
