"""
邀请码CRUD操作
"""
from sqlalchemy.orm import Session
from app.models.invitation_code import InvitationCode
from datetime import datetime
from typing import Optional, List


def get_invitation_by_code(db: Session, code: str) -> Optional[InvitationCode]:
    """通过code获取邀请码"""
    return db.query(InvitationCode).filter(InvitationCode.code == code).first()


def create_invitation_code(
        db: Session,
        code: str,
        created_by: int = 0,
        created_by_type: str = "admin",
        notes: str = None,
        expire_at: datetime = None
) -> InvitationCode:
    """创建邀请码"""
    invitation = InvitationCode(
        code=code,
        created_by=created_by,
        created_by_type=created_by_type,
        notes=notes,
        expire_at=expire_at
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def mark_invitation_as_used(
        db: Session,
        code: str,
        used_by_openid: str,
        user_id: int = None
) -> bool:
    """标记邀请码为已使用"""
    invitation = get_invitation_by_code(db, code)
    if not invitation:
        return False

    invitation.is_used = True
    invitation.used_by = user_id
    invitation.used_by_openid = used_by_openid
    invitation.used_at = datetime.utcnow()

    db.commit()
    return True


def get_user_invitation_codes(db: Session, user_id: int) -> List[InvitationCode]:
    """获取用户的邀请码"""
    return db.query(InvitationCode).filter(
        InvitationCode.created_by == user_id,
        InvitationCode.created_by_type == "user"
    ).all()