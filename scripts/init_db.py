"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import Base, engine
from app.models import UserProfile, InvitationCode, AdminUser
from app.core.security import get_password_hash
from app.core.config import settings
from sqlalchemy.orm import Session


def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("开始初始化数据库...")
    print("=" * 60)

    # 创建所有表
    print("\n1. 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")

    # 创建默认管理员
    print("\n2. 创建默认管理员账号...")
    db = Session(bind=engine)

    try:
        # 检查是否已存在管理员
        existing_admin = db.query(AdminUser).filter(
            AdminUser.username == settings.ADMIN_USERNAME
        ).first()

        if existing_admin:
            print(f"⚠️  管理员账号 '{settings.ADMIN_USERNAME}' 已存在")
        else:
            admin = AdminUser(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD)
            )
            db.add(admin)
            db.commit()
            print(f"✅ 管理员账号创建成功")
            print(f"   用户名: {settings.ADMIN_USERNAME}")
            print(f"   密码: {settings.ADMIN_PASSWORD}")
            print(f"   ⚠️  请及时修改默认密码！")

    except Exception as e:
        print(f"❌ 创建管理员失败: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("数据库初始化完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 运行应用: python run.py")
    print("2. 访问API文档: http://localhost:8000/docs")
    print("3. 使用管理员账号登录")
    print("=" * 60)


if __name__ == "__main__":
    init_database()