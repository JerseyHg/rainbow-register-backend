"""
Rainbow Register Backend - FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LGBT+ 交友平台后端服务 - 彩虹注册系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# 根路径
@app.get("/")
async def root():
    """欢迎页面"""
    return {
        "message": f"🌈 欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

# 启动事件
@app.on_event("startup")
async def startup_event():
    print(f"🚀 {settings.APP_NAME} is starting...")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    print(f"👋 {settings.APP_NAME} is shutting down...")