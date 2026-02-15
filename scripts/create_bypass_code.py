"""
创建审核放行邀请码
运行方式: python scripts/create_bypass_code.py
"""
import sys
import os
from pathlib import Path
from datetime import timedelta, datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.base import SessionLocal
from app.crud.crud_invitation import create_invitation_code, get_invitation_by_code
from app.core.config import settings


def main():
    bypass_codes = settings.REVIEW_BYPASS_CODES
    if not bypass_codes:
        print("❌ .env 中未配置 REVIEW_BYPASS_CODES，请先添加配置")
        print("   例如: REVIEW_BYPASS_CODES=TEST01")
        return

    db = SessionLocal()
    try:
        for code in bypass_codes:
            existing = get_invitation_by_code(db, code)
            if existing:
                print(f"⏭  邀请码 {code} 已存在（is_used={existing.is_used}）")
                # 如果已被使用，重置为未使用
                if existing.is_used:
                    existing.is_used = False
                    existing.used_by = None
                    existing.used_by_openid = None
                    existing.used_at = None
                    existing.expire_at = datetime.utcnow() + timedelta(days=30)
                    db.commit()
                    print(f"   ✅ 已重置为未使用，有效期延长30天")
            else:
                expire_at = datetime.utcnow() + timedelta(days=30)
                create_invitation_code(
                    db=db,
                    code=code,
                    created_by=0,
                    created_by_type="admin",
                    notes="微信审核放行邀请码（自动通过审核）",
                    expire_at=expire_at,
                )
                print(f"✅ 放行邀请码 {code} 创建成功（有效期30天）")

        print("\n🎉 完成！提交微信审核时，将放行邀请码写在审核备注中即可。")
        print(f"   放行邀请码列表: {', '.join(bypass_codes)}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
