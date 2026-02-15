#!/usr/bin/env python3
"""
数据库迁移：添加 post_url 字段
运行: python scripts/add_post_url_field.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import engine
from sqlalchemy import text, inspect

def main():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns("user_profiles")]
    with engine.connect() as conn:
        if 'post_url' in columns:
            print("⏭  post_url 字段已存在，跳过")
        else:
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN post_url TEXT"))
            print("✅ 已添加 post_url 字段")
        conn.commit()
    print("🎉 迁移完成！")

if __name__ == "__main__":
    main()
