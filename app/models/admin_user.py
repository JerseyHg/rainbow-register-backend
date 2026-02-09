"""
管理员用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class AdminUser(Base):
    """管理员表"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")

    role = Column(String(20), default='admin', comment="角色")

    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login = Column(DateTime(timezone=True), comment="最后登录时间")

    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<AdminUser(username={self.username}, role={self.role})>"