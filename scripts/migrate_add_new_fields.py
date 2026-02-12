"""
数据库迁移脚本 - 添加新字段
运行方式: python scripts/migrate_add_new_fields.py

新增字段:
1. dating_purpose  - 交友目的
2. want_children   - 是否需要孩子
3. wechat_id       - 微信号
4. referred_by     - 推荐人
"""
import sqlite3
import os
import sys

# 数据库路径（根据你的实际路径调整）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rainbow_register.db")


def migrate():
    """执行迁移"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        print("   如果是首次部署，直接运行 init_db.py 即可（新模型已包含这些字段）")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取现有列
    cursor.execute("PRAGMA table_info(user_profiles)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("dating_purpose", "VARCHAR(50)", "交友目的"),
        ("want_children", "VARCHAR(20)", "是否需要孩子"),
        ("wechat_id", "VARCHAR(50)", "微信号"),
        ("referred_by", "VARCHAR(100)", "推荐人"),
    ]

    added = 0
    for col_name, col_type, comment in new_columns:
        if col_name in existing_columns:
            print(f"  ⏭️  字段 {col_name} 已存在，跳过")
        else:
            sql = f"ALTER TABLE user_profiles ADD COLUMN {col_name} {col_type}"
            cursor.execute(sql)
            print(f"  ✅ 添加字段: {col_name} ({col_type}) -- {comment}")
            added += 1

    conn.commit()
    conn.close()

    print(f"\n{'=' * 50}")
    if added > 0:
        print(f"✅ 迁移完成！新增了 {added} 个字段")
    else:
        print("ℹ️  所有字段都已存在，无需迁移")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移 - 添加新字段")
    print("=" * 50)
    migrate()
