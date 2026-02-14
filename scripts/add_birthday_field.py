#!/usr/bin/env python3
"""
数据库迁移脚本：添加 birthday 和 activity_expectation 字段
运行方式: python scripts/add_birthday_field.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import engine
from sqlalchemy import text, inspect


def check_column_exists(inspector, table_name, column_name):
    """检查列是否已存在"""
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def main():
    inspector = inspect(engine)
    table_name = "user_profiles"

    print("=" * 60)
    print("Rainbow Register - 数据库迁移")
    print("添加 birthday 和 activity_expectation 字段")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. 添加 birthday 列
        if check_column_exists(inspector, table_name, 'birthday'):
            print("⏭  birthday 字段已存在，跳过")
        else:
            try:
                conn.execute(text(
                    "ALTER TABLE user_profiles ADD COLUMN birthday VARCHAR(10)"
                ))
                print("✅ 已添加 birthday 字段")
            except Exception as e:
                print(f"❌ 添加 birthday 字段失败: {e}")

        # 2. 添加 activity_expectation 列
        if check_column_exists(inspector, table_name, 'activity_expectation'):
            print("⏭  activity_expectation 字段已存在，跳过")
        else:
            try:
                conn.execute(text(
                    "ALTER TABLE user_profiles ADD COLUMN activity_expectation TEXT"
                ))
                print("✅ 已添加 activity_expectation 字段")
            except Exception as e:
                print(f"❌ 添加 activity_expectation 字段失败: {e}")

        conn.commit()

    print("\n🎉 数据库迁移完成！")
    print("\n提示：")
    print("  - 已有用户的 birthday 字段为空，age 和 constellation 保持不变")
    print("  - 新用户填写生日后，age 和 constellation 将自动计算")
    print("  - activity_expectation 替代了原来的 idealLife 功能")


if __name__ == "__main__":
    main()
