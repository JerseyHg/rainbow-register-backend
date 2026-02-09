"""
管理员CRUD操作
"""
from sqlalchemy.orm import Session
from app.models.admin_user import AdminUser
from app.core.security import get_password_hash
from typing import Optional
from datetime import datetime


def get_admin_by_username(db: Session, username: str) -> Optional[AdminUser]:
    """通过用户名获取管理员"""
    return db.query(AdminUser).filter(AdminUser.username == username).first()


def create_admin(db: Session, username: str, password: str) -> AdminUser:
    """创建管理员"""
    admin = AdminUser(
        username=username,
        password_hash=get_password_hash(password)
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def update_last_login(db: Session, admin_id: int):
    """更新最后登录时间"""
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin:
        admin.last_login = datetime.utcnow()
        db.commit()