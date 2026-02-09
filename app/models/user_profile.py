"""
用户资料数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class UserProfile(Base):
    """用户资料表"""
    __tablename__ = "user_profiles"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 用户标识
    openid = Column(String(100), unique=True, nullable=False, index=True, comment="微信openid")
    serial_number = Column(String(20), unique=True, index=True, comment="编号如051")

    # 基本信息
    name = Column(String(50), nullable=False, comment="姓名/昵称")
    gender = Column(String(10), nullable=False, comment="性别")
    age = Column(Integer, nullable=False, comment="年龄")
    height = Column(Integer, nullable=False, comment="身高cm")
    weight = Column(Integer, nullable=False, comment="体重kg")
    marital_status = Column(String(20), comment="婚姻状况")
    body_type = Column(String(20), comment="体型")

    # 地域信息
    hometown = Column(String(50), comment="籍贯")
    work_location = Column(String(100), comment="工作地")
    industry = Column(String(50), comment="行业")

    # 个人特征
    constellation = Column(String(20), comment="星座")
    mbti = Column(String(10), comment="MBTI")
    health_condition = Column(Text, comment="健康状况")
    housing_status = Column(String(50), comment="住房情况")

    # 兴趣爱好（JSON数组）
    hobbies = Column(JSON, comment="兴趣爱好")
    lifestyle = Column(Text, comment="生活方式")

    # 出柜状态
    coming_out_status = Column(String(50), comment="出柜状态")

    # 期待对象（JSON对象）
    expectation = Column(JSON, comment="期待对象")

    # 特殊说明
    special_requirements = Column(Text, comment="特殊要求")

    # 照片（JSON数组）
    photos = Column(JSON, comment="照片URL列表")

    # 状态管理
    status = Column(
        String(20),
        default='pending',
        index=True,
        comment="状态: pending/approved/published/rejected/archived"
    )
    rejection_reason = Column(Text, comment="拒绝原因")

    # 邀请关系
    invited_by = Column(Integer, comment="邀请人user_id")
    invitation_code_used = Column(String(20), comment="使用的邀请码")
    invitation_quota = Column(Integer, default=0, comment="剩余邀请名额")

    # 时间戳
    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    reviewed_at = Column(DateTime(timezone=True), comment="审核时间")
    published_at = Column(DateTime(timezone=True), comment="发布时间")

    # 审核信息
    reviewed_by = Column(String(50), comment="审核人")
    review_notes = Column(Text, comment="审核备注")

    # 管理员联系方式
    admin_contact = Column(String(50), default='casper_gb', comment="管理员微信")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, serial_number={self.serial_number}, name={self.name})>"