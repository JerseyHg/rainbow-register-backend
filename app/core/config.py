"""
应用配置管理
Rainbow Register Backend
"""
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    """应用配置类"""

    # ========== 应用基本配置 ==========
    APP_NAME: str = "Rainbow Register Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ========== 数据库配置 ==========
    DATABASE_URL: str = "sqlite:///./rainbow_register.db"

    # ========== JWT认证配置 ==========
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7200  # 2小时

    # ========== 微信小程序配置 ==========
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # ========== 文件上传配置 ==========
    UPLOAD_DIR: str = "./uploads/photos"
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_EXTENSIONS: Union[List[str], str] = "jpg,jpeg,png,webp"

    # ========== 邀请码配置 ==========
    INVITATION_CODE_LENGTH: int = 6
    INVITATION_EXPIRE_DAYS: int = 7
    DEFAULT_INVITATION_QUOTA: int = 2

    # ========== 管理员配置 ==========
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change_this_password"

    # ========== CORS配置 ==========
    CORS_ORIGINS: Union[List[str], str] = "*"

    # ========== 字段验证器 ==========

    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        """解析允许的文件扩展名"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS允许的来源"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外字段而不是报错

# 创建全局配置实例
settings = Settings()

# 打印配置信息（调试用）
if __name__ == "__main__":
    print("=" * 60)
    print("Configuration Settings")
    print("=" * 60)
    print(f"App Name: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Allowed Extensions: {settings.ALLOWED_EXTENSIONS}")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Admin Username: {settings.ADMIN_USERNAME}")
    print("=" * 60)