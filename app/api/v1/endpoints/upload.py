"""
文件上传相关API - 完整实现
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_openid
from app.core.config import settings
from app.schemas.common import ResponseModel
import os
import uuid
from pathlib import Path

router = APIRouter()


@router.post("/photo", response_model=ResponseModel)
async def upload_photo(
        file: UploadFile = File(...),
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    上传照片
    """
    # 1. 验证文件类型
    file_ext = file.filename.split('.')[-1].lower()

    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。允许的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. 检查文件大小
    # 读取内容
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大。最大允许: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )

    # 3. 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

    # 4. 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 5. 保存文件
    file_path = upload_dir / unique_filename

    with open(file_path, "wb") as f:
        f.write(content)

    # 6. 生成访问URL
    # 注意：这里假设Nginx配置了 /uploads 路径映射
    file_url = f"/uploads/photos/{unique_filename}"

    return ResponseModel(
        success=True,
        message="上传成功",
        data={
            "url": file_url,
            "filename": unique_filename
        }
    )