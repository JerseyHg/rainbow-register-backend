"""
用户资料相关Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ExpectationSchema(BaseModel):
    """期待对象"""
    relationship: Optional[str] = None
    body_type: Optional[str] = None
    appearance: Optional[str] = None
    age_range: Optional[str] = None
    habits: Optional[str] = None
    personality: Optional[str] = None
    location: Optional[str] = None
    children: Optional[str] = None
    other: Optional[str] = None


class ProfileSubmitRequest(BaseModel):
    """提交资料请求"""
    # 基本信息
    name: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., min_length=1, max_length=10)
    age: int = Field(..., ge=18, le=80)
    height: int = Field(..., ge=140, le=220)
    weight: int = Field(..., ge=30, le=200)
    marital_status: Optional[str] = None
    body_type: Optional[str] = None

    # 地域信息
    hometown: Optional[str] = None
    work_location: Optional[str] = None
    industry: Optional[str] = None

    # 个人特征
    constellation: Optional[str] = None
    mbti: Optional[str] = None
    health_condition: Optional[str] = None
    housing_status: Optional[str] = None

    # ===== 新增字段 =====
    dating_purpose: Optional[str] = None      # 交友目的
    want_children: Optional[str] = None       # 是否需要孩子
    wechat_id: Optional[str] = None           # 微信号
    # ===== 新增字段结束 =====

    # 兴趣爱好
    hobbies: List[str] = []
    lifestyle: Optional[str] = None

    # 出柜状态
    coming_out_status: Optional[str] = None

    # 期待对象
    expectation: Optional[ExpectationSchema] = None

    # 特殊说明
    special_requirements: Optional[str] = None

    # 照片
    photos: List[str] = []


class ProfileResponse(BaseModel):
    """资料响应"""
    id: int
    serial_number: Optional[str]
    status: str
    create_time: str
    published_at: Optional[str] = None
