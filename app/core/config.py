"""
应用配置管理
Register Backend
"""
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    """应用配置类"""

    APP_NAME: str = "Register Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./rainbow_register.db"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7200

    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    UPLOAD_DIR: str = "./uploads/photos"
    MAX_UPLOAD_SIZE: int = 5242880
    ALLOWED_EXTENSIONS: Union[List[str], str] = "jpg,jpeg,png,webp"

    # ★ 腾讯云 COS 配置
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_REGION: str = "ap-shanghai"
    COS_BUCKET: str = "tbowo-1259330613"
    COS_DOMAIN: str = "https://tbowo-1259330613.cos.ap-shanghai.myqcloud.com"
    COS_UPLOAD_PREFIX: str = "photos"  # COS中的目录前缀

    INVITATION_CODE_LENGTH: int = 6
    INVITATION_EXPIRE_DAYS: int = 7
    DEFAULT_INVITATION_QUOTA: int = 2

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change_this_password"

    CORS_ORIGINS: Union[List[str], str] = "*"

    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
