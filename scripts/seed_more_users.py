#!/usr/bin/env python3
"""
生成更多模拟用户数据（测试地图 + 邀请网络）
用法: python scripts/seed_more_users.py

在现有数据基础上追加 ~25 个用户，分布在不同城市，用于测试地图功能。
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import SessionLocal
from app.models.user_profile import UserProfile
from app.models.invitation_code import InvitationCode
from app.services.invitation import generate_invitation_code

# ========== 新用户数据 - 分布在各种城市 ==========
NEW_USERS = [
    {"name": "小宇", "gender": "男", "age": 24, "height": 173, "weight": 66, "work_location": "宜昌西陵", "hometown": "湖北宜昌", "industry": "水电"},
    {"name": "阿涛", "gender": "男", "age": 27, "height": 178, "weight": 72, "work_location": "厦门湖里", "hometown": "福建泉州", "industry": "外贸"},
    {"name": "小晴", "gender": "女", "age": 23, "height": 163, "weight": 49, "work_location": "长沙岳麓", "hometown": "湖南衡阳", "industry": "教育"},
    {"name": "阿磊", "gender": "男", "age": 29, "height": 181, "weight": 76, "work_location": "西安雁塔", "hometown": "陕西咸阳", "industry": "航天"},
    {"name": "小璐", "gender": "女", "age": 25, "height": 166, "weight": 52, "work_location": "昆明盘龙", "hometown": "云南大理", "industry": "旅游"},
    {"name": "阿超", "gender": "男", "age": 26, "height": 175, "weight": 69, "work_location": "青岛市南", "hometown": "山东烟台", "industry": "海运"},
    {"name": "小芳", "gender": "女", "age": 22, "height": 160, "weight": 46, "work_location": "南京鼓楼", "hometown": "江苏扬州", "industry": "医药"},
    {"name": "阿鑫", "gender": "男", "age": 28, "height": 176, "weight": 71, "work_location": "大连沙河口", "hometown": "辽宁锦州", "industry": "软件"},
    {"name": "小颖", "gender": "女", "age": 24, "height": 164, "weight": 50, "work_location": "苏州工业园", "hometown": "安徽合肥", "industry": "半导体"},
    {"name": "阿翔", "gender": "男", "age": 30, "height": 183, "weight": 79, "work_location": "郑州金水", "hometown": "河南洛阳", "industry": "物流"},
    {"name": "小诗", "gender": "女", "age": 23, "height": 161, "weight": 47, "work_location": "珠海香洲", "hometown": "广东湛江", "industry": "生物"},
    {"name": "阿峰", "gender": "男", "age": 27, "height": 179, "weight": 74, "work_location": "襄阳樊城", "hometown": "湖北随州", "industry": "汽车"},
    {"name": "小云", "gender": "女", "age": 25, "height": 165, "weight": 51, "work_location": "合肥蜀山", "hometown": "安徽芜湖", "industry": "科研"},
    {"name": "阿轩", "gender": "男", "age": 26, "height": 174, "weight": 68, "work_location": "佛山禅城", "hometown": "广东梅州", "industry": "陶瓷"},
    {"name": "小薇", "gender": "女", "age": 24, "height": 162, "weight": 48, "work_location": "贵阳观山湖", "hometown": "贵州遵义", "industry": "大数据"},
    {"name": "阿勇", "gender": "男", "age": 31, "height": 180, "weight": 77, "work_location": "济南历下", "hometown": "山东济宁", "industry": "金融"},
    {"name": "小楠", "gender": "女", "age": 22, "height": 159, "weight": 45, "work_location": "东莞南城", "hometown": "广西桂林", "industry": "电子"},
    {"name": "阿健", "gender": "男", "age": 28, "height": 177, "weight": 73, "work_location": "无锡滨湖", "hometown": "江苏盐城", "industry": "物联网"},
    {"name": "小瑶", "gender": "女", "age": 26, "height": 167, "weight": 53, "work_location": "南宁青秀", "hometown": "广西柳州", "industry": "地产"},
    {"name": "阿斌", "gender": "男", "age": 25, "height": 172, "weight": 67, "work_location": "沈阳和平", "hometown": "吉林长春", "industry": "机械"},
    {"name": "小敏", "gender": "女", "age": 23, "height": 163, "weight": 49, "work_location": "福州鼓楼", "hometown": "福建莆田", "industry": "跨境电商"},
    {"name": "阿杰二", "gender": "男", "age": 29, "height": 182, "weight": 78, "work_location": "上海虹口", "hometown": "江苏南通", "industry": "航运"},
    {"name": "小燕", "gender": "女", "age": 24, "height": 164, "weight": 50, "work_location": "北京通州", "hometown": "河北保定", "industry": "影视"},
    {"name": "阿伟二", "gender": "男", "age": 27, "height": 176, "weight": 70, "work_location": "深圳龙华", "hometown": "湖南长沙", "industry": "AI"},
    {"name": "小茹", "gender": "女", "age": 25, "height": 165, "weight": 52, "work_location": "哈尔滨南岗", "hometown": "黑龙江齐齐哈尔", "industry": "冰雪旅游"},
]

STATUS_POOL = ['approved', 'approved', 'approved', 'published', 'published', 'rejected', 'pending', 'pending']


def seed_more():
    db = SessionLocal()
    try:
        # 获取当前最大 serial_number
        last = db.query(UserProfile).order_by(UserProfile.id.desc()).first()
        serial = 1
        if last and last.serial_number:
            try:
                serial = int(last.serial_number) + 1
            except:
                serial = last.id + 1

        # 获取现有的 approved 用户作为潜在邀请人
        existing_approved = db.query(UserProfile).filter(
            UserProfile.status.in_(['approved', 'published'])
        ).all()

        base_time = datetime.utcnow() - timedelta(days=30)
        created = []

        print(f"\n🌍 开始追加用户数据（起始编号: {serial}）...\n")

        for i, user_data in enumerate(NEW_USERS):
            time_offset = base_time + timedelta(days=random.randint(0, 28), hours=random.randint(0, 23))
            status = random.choice(STATUS_POOL)

            # 随机选一个邀请人（70% 概率有邀请人，30% 管理员直邀）
            inviter = None
            invited_by_id = None
            referred_by = None
            invitation_code_used = None

            all_potential_inviters = existing_approved + [p for p in created if p.status in ('approved', 'published')]

            if all_potential_inviters and random.random() < 0.7:
                inviter = random.choice(all_potential_inviters)
                invited_by_id = inviter.id
                referred_by = f"{inviter.name}（{inviter.serial_number}）"
                # 创建邀请码
                code = generate_invitation_code()
                inv = InvitationCode(
                    code=code, created_by=inviter.id, created_by_type="user",
                    is_used=True, used_at=time_offset + timedelta(hours=random.randint(1, 12)),
                    notes="追加模拟数据", create_time=time_offset,
                    expire_at=time_offset + timedelta(days=7),
                )
                db.add(inv)
                db.flush()
                invitation_code_used = code
            else:
                # 管理员直邀
                referred_by = "管理员"
                code = generate_invitation_code()
                inv = InvitationCode(
                    code=code, created_by=0, created_by_type="admin",
                    is_used=True, used_at=time_offset + timedelta(hours=random.randint(1, 12)),
                    notes="追加模拟数据", create_time=time_offset,
                    expire_at=time_offset + timedelta(days=7),
                )
                db.add(inv)
                db.flush()
                invitation_code_used = code

            profile = UserProfile(
                openid=f"mock_extra_{serial}_{random.randint(10000, 99999)}",
                serial_number=str(serial).zfill(3),
                name=user_data["name"],
                gender=user_data["gender"],
                age=user_data["age"],
                height=user_data["height"],
                weight=user_data["weight"],
                work_location=user_data["work_location"],
                hometown=user_data["hometown"],
                industry=user_data["industry"],
                constellation=random.choice(["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]),
                mbti=random.choice(["INFJ", "INFP", "ENFJ", "ENFP", "INTJ", "INTP", "ENTJ", "ENTP", "ISFJ", "ISFP", "ESFJ", "ESFP", "ISTJ", "ISTP", "ESTJ", "ESTP"]),
                marital_status="未婚",
                body_type=random.choice(["匀称", "偏瘦", "微胖", "运动型"]),
                hobbies=random.sample(["健身", "读书", "旅行", "摄影", "音乐", "电影", "烹饪", "游泳", "跑步", "画画", "瑜伽", "篮球", "登山", "骑行"], k=random.randint(2, 5)),
                lifestyle=random.choice(["早睡早起", "夜猫子", "规律作息", "随性"]),
                coming_out_status=random.choice(["已出柜", "半出柜", "未出柜"]),
                status=status,
                invited_by=invited_by_id,
                invitation_code_used=invitation_code_used,
                referred_by=referred_by,
                invitation_quota=2 if status in ('approved', 'published') else 0,
                photos=[],
                create_time=time_offset,
                reviewed_at=(time_offset + timedelta(days=random.randint(1, 3))) if status in ('approved', 'published', 'rejected') else None,
                reviewed_by="admin" if status in ('approved', 'published', 'rejected') else None,
                rejection_reason="资料不完整" if status == 'rejected' else None,
                admin_contact="casper_gb",
            )
            db.add(profile)
            db.flush()

            # 给通过的用户也生成未使用的邀请码
            if status in ('approved', 'published'):
                for _ in range(2):
                    unused_code = generate_invitation_code()
                    db.add(InvitationCode(
                        code=unused_code, created_by=profile.id, created_by_type="user",
                        is_used=False, notes="追加模拟数据", create_time=time_offset,
                        expire_at=time_offset + timedelta(days=7),
                    ))

            # 更新邀请码的 used_by
            if invitation_code_used:
                inv_record = db.query(InvitationCode).filter(InvitationCode.code == invitation_code_used).first()
                if inv_record:
                    inv_record.used_by = profile.id
                    inv_record.used_by_openid = profile.openid

            created.append(profile)
            inviter_info = f"← {inviter.name}(#{inviter.serial_number})" if inviter else "← 管理员"
            print(f"  #{str(serial).zfill(3)} {user_data['name']:4s}  {user_data['work_location']:10s}  {status:10s}  {inviter_info}")
            serial += 1

        db.commit()

        # 统计
        approved = sum(1 for p in created if p.status in ('approved', 'published'))
        rejected = sum(1 for p in created if p.status == 'rejected')
        pending = sum(1 for p in created if p.status == 'pending')
        cities = set(u["work_location"].split()[0] if " " in u["work_location"] else u["work_location"][:2] for u in NEW_USERS)

        print(f"\n{'=' * 60}")
        print(f"✅ 追加完成！")
        print(f"{'=' * 60}")
        print(f"  新增用户: {len(created)}")
        print(f"  通过/发布: {approved}")
        print(f"  拒绝: {rejected}")
        print(f"  待审核: {pending}")
        print(f"  覆盖城市: {len(cities)} 个")
        print(f"  城市列表: {', '.join(sorted(cities))}")
        print(f"{'=' * 60}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_more()
