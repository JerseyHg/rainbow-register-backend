"""
依赖注入
"""
from typing import Generator
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.security import verify_token


def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_openid(authorization: str = Header(None)) -> str:
    """
    从请求头获取用户openid
    用户端API使用
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    return authorization


def get_current_admin(authorization: str = Header(None)) -> dict:
    """
    验证管理员token
    管理端API使用
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    # 移除 "Bearer " 前缀
    token = authorization.replace("Bearer ", "")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return payload