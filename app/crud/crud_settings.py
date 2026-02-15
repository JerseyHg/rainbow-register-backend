"""
系统设置 CRUD 操作
"""
from sqlalchemy.orm import Session
from app.models.system_setting import SystemSetting
from typing import Optional, Dict
from datetime import datetime


# ============================================================
# 默认配置项（首次启动时自动写入数据库）
# ============================================================
DEFAULT_SETTINGS = {
    "ai_auto_review": {
        "value": "false",
        "description": "AI 自动审核开关（true/false）",
    },
}


def get_setting(db: Session, key: str) -> Optional[str]:
    """获取单个配置值"""
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        return row.value
    # 如果数据库没有，返回默认值
    default = DEFAULT_SETTINGS.get(key)
    return default["value"] if default else None


def get_setting_bool(db: Session, key: str) -> bool:
    """获取布尔类型配置值"""
    val = get_setting(db, key)
    return val is not None and val.lower() in ("true", "1", "yes", "on")


def set_setting(db: Session, key: str, value: str, updated_by: str = "system") -> SystemSetting:
    """设置配置值（不存在则创建）"""
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        row.value = value
        row.updated_by = updated_by
        row.updated_at = datetime.utcnow()
    else:
        desc = DEFAULT_SETTINGS.get(key, {}).get("description", "")
        row = SystemSetting(key=key, value=value, description=desc, updated_by=updated_by)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_all_settings(db: Session) -> Dict[str, dict]:
    """获取所有配置项"""
    rows = db.query(SystemSetting).all()
    result = {}
    for row in rows:
        result[row.key] = {
            "value": row.value,
            "description": row.description,
            "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S") if row.updated_at else None,
            "updated_by": row.updated_by,
        }
    # 补充默认值中有但数据库没有的项
    for key, default in DEFAULT_SETTINGS.items():
        if key not in result:
            result[key] = {
                "value": default["value"],
                "description": default["description"],
                "updated_at": None,
                "updated_by": None,
            }
    return result


def init_default_settings(db: Session):
    """
    初始化默认设置（仅写入数据库中不存在的项）
    应在应用启动或 init_db 时调用
    """
    for key, default in DEFAULT_SETTINGS.items():
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not existing:
            row = SystemSetting(
                key=key,
                value=default["value"],
                description=default["description"],
                updated_by="system_init",
            )
            db.add(row)
    db.commit()
