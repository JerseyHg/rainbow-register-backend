"""
用户资料CRUD操作
"""
from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from typing import Optional, List
from datetime import datetime


def get_profile_by_openid(db: Session, openid: str) -> Optional[UserProfile]:
    """通过openid获取资料"""
    return db.query(UserProfile).filter(UserProfile.openid == openid).first()


def get_profile_by_id(db: Session, profile_id: int) -> Optional[UserProfile]:
    """通过ID获取资料"""
    return db.query(UserProfile).filter(UserProfile.id == profile_id).first()


def create_profile(db: Session, openid: str, data: dict) -> UserProfile:
    """创建用户资料"""
    profile = UserProfile(
        openid=openid,
        **data
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(db: Session, profile_id: int, data: dict) -> Optional[UserProfile]:
    """更新资料"""
    profile = get_profile_by_id(db, profile_id)
    if not profile:
        return None

    for key, value in data.items():
        setattr(profile, key, value)

    profile.update_time = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile_id: int) -> bool:
    """删除用户资料"""
    profile = get_profile_by_id(db, profile_id)
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True


def get_pending_profiles(db: Session, skip: int = 0, limit: int = 20) -> List[UserProfile]:
    """获取待审核列表"""
    return db.query(UserProfile).filter(
        UserProfile.status == 'pending'
    ).order_by(UserProfile.create_time.desc()).offset(skip).limit(limit).all()


def get_last_serial_number(db: Session) -> int:
    """获取最后一个编号"""
    profile = db.query(UserProfile).filter(
        UserProfile.serial_number.isnot(None)
    ).order_by(UserProfile.id.desc()).first()

    if profile and profile.serial_number:
        try:
            return int(profile.serial_number)
        except:
            return 0
    return 0


def approve_profile(
        db: Session,
        profile_id: int,
        reviewed_by: str,
        notes: str = None
) -> Optional[UserProfile]:
    """通过审核"""
    profile = get_profile_by_id(db, profile_id)
    if not profile:
        return None

    profile.status = 'approved'
    profile.reviewed_by = reviewed_by
    profile.review_notes = notes
    profile.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def reject_profile(
        db: Session,
        profile_id: int,
        reviewed_by: str,
        reason: str
) -> Optional[UserProfile]:
    """拒绝审核"""
    profile = get_profile_by_id(db, profile_id)
    if not profile:
        return None

    profile.status = 'rejected'
    profile.reviewed_by = reviewed_by
    profile.rejection_reason = reason
    profile.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile
