"""
创建管理员账号脚本
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import SessionLocal
from app.crud.crud_admin import create_admin, get_admin_by_username
from getpass import getpass


def create_admin_interactive():
    """交互式创建管理员"""
    print("=" * 60)
    print("创建管理员账号")
    print("=" * 60)

    username = input("\n请输入用户名: ").strip()

    if not username:
        print("❌ 用户名不能为空")
        return

    db = SessionLocal()

    try:
        # 检查是否已存在
        existing = get_admin_by_username(db, username)
        if existing:
            print(f"❌ 用户名 '{username}' 已存在")
            return

        # 输入密码
        password = getpass("请输入密码: ")
        password_confirm = getpass("请再次输入密码: ")

        if password != password_confirm:
            print("❌ 两次密码不一致")
            return

        if len(password) < 6:
            print("❌ 密码至少6个字符")
            return

        # 创建管理员
        admin = create_admin(db, username, password)

        print("\n✅ 管理员创建成功！")
        print(f"   用户名: {admin.username}")
        print(f"   ID: {admin.id}")

    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_interactive()