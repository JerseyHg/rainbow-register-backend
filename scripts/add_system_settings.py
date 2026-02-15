#!/usr/bin/env python3
"""
数据库迁移脚本：创建 system_settings 表 + 初始化默认设置
运行方式: python scripts/add_system_settings.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import engine, SessionLocal
from app.models.system_setting import SystemSetting
from app.crud.crud_settings import init_default_settings
from sqlalchemy import inspect


def main():
    print("=" * 60)
    print("Rainbow Register - 数据库迁移")
    print("创建 system_settings 表")
    print("=" * 60)

    inspector = inspect(engine)

    # 1. 创建表（如果不存在）
    if "system_settings" in inspector.get_table_names():
        print("⏭  system_settings 表已存在")
    else:
        SystemSetting.__table__.create(bind=engine)
        print("✅ system_settings 表创建成功")

    # 2. 初始化默认设置
    db = SessionLocal()
    try:
        init_default_settings(db)
        print("✅ 默认设置初始化完成")

        # 打印当前设置
        settings = db.query(SystemSetting).all()
        print("\n当前系统设置：")
        for s in settings:
            print(f"  {s.key} = {s.value}  ({s.description})")
    finally:
        db.close()

    print("\n🎉 迁移完成！")
    print("提示：可在管理后台「设置」页面动态切换 AI 审核开关")


if __name__ == "__main__":
    main()
