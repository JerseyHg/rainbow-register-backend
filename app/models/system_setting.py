"""
系统设置数据库模型
用于存储运行时可动态修改的配置项（如 AI 审核开关）
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class SystemSetting(Base):
    """系统设置表（键值对）"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True, comment="配置项名称")
    value = Column(Text, nullable=False, comment="配置项值")
    description = Column(String(200), comment="配置项说明")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50), comment="最后修改人")

    def __repr__(self):
        return f"<SystemSetting(key={self.key}, value={self.value})>"
