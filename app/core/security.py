"""
安全相关：密码加密、JWT生成等
使用 PyJWT 替代 python-jose
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
import jwt  # PyJWT
from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt限制：密码最多72字节
MAX_PASSWORD_LENGTH = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 截断到72字节
    if len(plain_password.encode('utf-8')) > MAX_PASSWORD_LENGTH:
        plain_password = plain_password.encode('utf-8')[:MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    注意：bcrypt限制密码最多72字节
    """
    # 检查并截断密码
    password_bytes = password.encode('utf-8')

    if len(password_bytes) > MAX_PASSWORD_LENGTH:
        # 自动截断到72字节
        password = password_bytes[:MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
        print(f"⚠️  密码超过{MAX_PASSWORD_LENGTH}字节，已自动截断")

    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # PyJWT 用法
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证JWT token"""
    try:
        # PyJWT 用法
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token过期
        return None
    except jwt.InvalidTokenError:
        # Token无效
        return None
    except Exception:
        # 其他错误
        return None