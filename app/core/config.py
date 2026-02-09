"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Rainbow Register Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./rainbow_register.db"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7200

    # 微信配置
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads/photos"
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]

    # 邀请码配置
    INVITATION_CODE_LENGTH: int = 6
    INVITATION_EXPIRE_DAYS: int = 7
    DEFAULT_INVITATION_QUOTA: int = 2

    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()