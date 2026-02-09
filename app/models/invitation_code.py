"""
邀请码数据库模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class InvitationCode(Base):
    """邀请码表"""
    __tablename__ = "invitation_codes"

    id = Column(Integer, primary_key=True, index=True)

    # 邀请码
    code = Column(String(20), unique=True, nullable=False, index=True, comment="邀请码")

    # 创建信息
    created_by = Column(Integer, comment="创建者user_id，0表示管理员")
    created_by_type = Column(String(20), comment="创建者类型: admin/user")

    # 使用信息
    used_by = Column(Integer, comment="使用者user_id")
    used_by_openid = Column(String(100), comment="使用者openid")
    is_used = Column(Boolean, default=False, index=True, comment="是否已使用")
    used_at = Column(DateTime(timezone=True), comment="使用时间")

    # 状态
    is_active = Column(Boolean, default=True, index=True, comment="是否可用")
    disable_reason = Column(Text, comment="禁用原因")

    # 有效期
    expire_at = Column(DateTime(timezone=True), comment="过期时间")

    # 备注
    notes = Column(Text, comment="备注")

    # 时间戳
    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<InvitationCode(code={self.code}, is_used={self.is_used})>"