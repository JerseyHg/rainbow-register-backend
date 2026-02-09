#!/usr/bin/env python3
"""
Rainbow Register Backend - 应用启动脚本
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"🌈 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print("-" * 50)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )