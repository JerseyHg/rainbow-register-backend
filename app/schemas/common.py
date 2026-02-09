"""
通用Schema
"""
from pydantic import BaseModel
from typing import Optional, Any


class ResponseModel(BaseModel):
    """通用响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None