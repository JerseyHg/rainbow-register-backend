"""
文件上传相关API - COS版本
上传照片到腾讯云COS对象存储
目录结构: photos/{user_openid}/{uuid}.{ext}
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_openid
from app.core.config import settings
from app.schemas.common import ResponseModel
from pydantic import BaseModel
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_cos_client():
    """获取COS客户端实例"""
    try:
        from qcloud_cos import CosConfig, CosS3Client

        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        return CosS3Client(config)
    except ImportError:
        logger.error("cos-python-sdk-v5 未安装，请运行: pip install cos-python-sdk-v5")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="COS SDK未安装"
        )
    except Exception as e:
        logger.error(f"COS客户端初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="COS配置错误"
        )


@router.post("/photo", response_model=ResponseModel)
async def upload_photo(
        file: UploadFile = File(...),
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    上传照片到COS
    存储路径: photos/{openid}/{uuid}.{ext}
    """
    # 1. 验证文件类型
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )

    file_ext = file.filename.split('.')[-1].lower()

    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。允许的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. 读取文件内容并检查大小
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大。最大允许: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )

    # 3. ★ 生成路径: photos/{openid}/{uuid}.{ext}
    photo_id = uuid.uuid4().hex
    unique_filename = f"{photo_id}.{file_ext}"
    cos_key = f"{settings.COS_UPLOAD_PREFIX}/{openid}/{unique_filename}"

    # 4. 上传到COS
    try:
        client = _get_cos_client()

        response = client.put_object(
            Bucket=settings.COS_BUCKET,
            Body=content,
            Key=cos_key,
            ContentType=file.content_type or f"image/{file_ext}",
        )

        logger.info(f"COS上传成功: {cos_key}, ETag: {response.get('ETag', '')}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"COS上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="照片上传失败，请稍后重试"
        )

    # 5. 生成访问URL
    file_url = f"{settings.COS_DOMAIN}/{cos_key}"

    return ResponseModel(
        success=True,
        message="上传成功",
        data={
            "url": file_url,
            "filename": unique_filename,
            "cos_key": cos_key,
        }
    )


class DeletePhotoRequest(BaseModel):
    url: str


@router.delete("/photo", response_model=ResponseModel)
async def delete_photo(
        body: DeletePhotoRequest,
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    删除单张照片
    ★ 安全校验：只允许删除自己目录下的照片
    """
    photo_url = body.url

    if not photo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="照片URL不能为空"
        )

    # COS照片
    if settings.COS_DOMAIN and photo_url.startswith(settings.COS_DOMAIN):
        cos_key = photo_url.replace(settings.COS_DOMAIN + "/", "")

        # ★ 安全校验：确保只能删除自己目录下的照片
        expected_prefix = f"{settings.COS_UPLOAD_PREFIX}/{openid}/"
        if not cos_key.startswith(expected_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此照片"
            )

        try:
            client = _get_cos_client()
            client.delete_object(
                Bucket=settings.COS_BUCKET,
                Key=cos_key,
            )
            logger.info(f"COS删除成功: {cos_key}")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"COS删除失败（可能文件不存在）: {e}")

    # 本地照片（兼容旧数据）
    elif photo_url.startswith("/uploads/"):
        import os
        local_path = "." + photo_url
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.info(f"本地文件删除成功: {local_path}")
            except Exception as e:
                logger.warning(f"本地文件删除失败: {e}")

    return ResponseModel(
        success=True,
        message="删除成功"
    )


@router.delete("/photos/all", response_model=ResponseModel)
async def delete_all_photos(
        openid: str = Depends(get_current_user_openid),
        db: Session = Depends(get_db)
):
    """
    ★ 删除用户所有照片（删除档案时调用）
    直接删除 photos/{openid}/ 目录下所有文件
    """
    prefix = f"{settings.COS_UPLOAD_PREFIX}/{openid}/"

    try:
        client = _get_cos_client()

        # 列出该用户目录下所有文件
        response = client.list_objects(
            Bucket=settings.COS_BUCKET,
            Prefix=prefix,
            MaxKeys=100,
        )

        # 批量删除
        contents = response.get('Contents', [])
        if contents:
            delete_objects = [{'Key': obj['Key']} for obj in contents]
            client.delete_objects(
                Bucket=settings.COS_BUCKET,
                Delete={'Object': delete_objects, 'Quiet': 'true'},
            )
            logger.info(f"批量删除成功: {openid} 目录下 {len(delete_objects)} 个文件")
        else:
            logger.info(f"用户 {openid} 目录下无文件")

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"批量删除失败: {e}")

    return ResponseModel(
        success=True,
        message="全部照片已删除"
    )
