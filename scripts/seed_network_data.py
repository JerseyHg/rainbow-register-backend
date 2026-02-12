#!/usr/bin/env python3
"""
生成邀请关系网络的模拟数据
用法: python scripts/seed_network_data.py

会在数据库中创建 ~25 个用户，形成 3-4 层的邀请树，用于测试关系网络页面。
运行前请确保数据库已初始化（python scripts/init_db.py）。
"""
import sys
import os
import random
from datetime import datetime, timedelta

# 确保可以导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import SessionLocal, engine, Base
from app.models.user_profile import UserProfile
from app.models.invitation_code import InvitationCode
from app.services.invitation import generate_invitation_code

# ========== 模拟用户数据池 ==========
MOCK_USERS = [
    {"name": "小明", "gender": "男", "age": 25, "height": 175, "weight": 68, "work_location": "北京朝阳", "industry": "互联网", "constellation": "天秤座", "mbti": "INFJ"},
    {"name": "阿杰", "gender": "男", "age": 28, "height": 180, "weight": 75, "work_location": "上海浦东", "industry": "金融", "constellation": "射手座", "mbti": "ENTJ"},
    {"name": "小雨", "gender": "女", "age": 23, "height": 165, "weight": 50, "work_location": "深圳南山", "industry": "设计", "constellation": "双鱼座", "mbti": "INFP"},
    {"name": "大伟", "gender": "男", "age": 30, "height": 178, "weight": 72, "work_location": "广州天河", "industry": "教育", "constellation": "狮子座", "mbti": "ENFJ"},
    {"name": "小林", "gender": "男", "age": 26, "height": 172, "weight": 65, "work_location": "杭州西湖", "industry": "电商", "constellation": "处女座", "mbti": "ISTJ"},
    {"name": "小美", "gender": "女", "age": 24, "height": 162, "weight": 48, "work_location": "成都锦江", "industry": "传媒", "constellation": "天蝎座", "mbti": "ENFP"},
    {"name": "阿豪", "gender": "男", "age": 27, "height": 182, "weight": 78, "work_location": "北京海淀", "industry": "科技", "constellation": "白羊座", "mbti": "ENTP"},
    {"name": "思思", "gender": "女", "age": 25, "height": 168, "weight": 52, "work_location": "上海徐汇", "industry": "咨询", "constellation": "金牛座", "mbti": "INTJ"},
    {"name": "小凯", "gender": "男", "age": 29, "height": 176, "weight": 70, "work_location": "深圳福田", "industry": "律师", "constellation": "水瓶座", "mbti": "INTP"},
    {"name": "阿文", "gender": "男", "age": 24, "height": 170, "weight": 62, "work_location": "武汉武昌", "industry": "医疗", "constellation": "巨蟹座", "mbti": "ISFJ"},
    {"name": "小琳", "gender": "女", "age": 22, "height": 160, "weight": 46, "work_location": "南京鼓楼", "industry": "会计", "constellation": "双子座", "mbti": "ESFP"},
    {"name": "阿强", "gender": "男", "age": 31, "height": 185, "weight": 82, "work_location": "北京东城", "industry": "建筑", "constellation": "摩羯座", "mbti": "ESTJ"},
    {"name": "小丹", "gender": "女", "age": 26, "height": 166, "weight": 53, "work_location": "杭州余杭", "industry": "运营", "constellation": "天秤座", "mbti": "ESFJ"},
    {"name": "大鹏", "gender": "男", "age": 28, "height": 179, "weight": 74, "work_location": "广州番禺", "industry": "制造", "constellation": "射手座", "mbti": "ISTP"},
    {"name": "小雪", "gender": "女", "age": 23, "height": 163, "weight": 49, "work_location": "成都高新", "industry": "艺术", "constellation": "双鱼座", "mbti": "ISFP"},
    {"name": "阿龙", "gender": "男", "age": 27, "height": 177, "weight": 71, "work_location": "上海静安", "industry": "广告", "constellation": "狮子座", "mbti": "ESTP"},
    {"name": "小慧", "gender": "女", "age": 25, "height": 164, "weight": 51, "work_location": "深圳宝安", "industry": "人力", "constellation": "处女座", "mbti": "INFJ"},
    {"name": "阿宇", "gender": "男", "age": 26, "height": 174, "weight": 67, "work_location": "北京丰台", "industry": "游戏", "constellation": "天蝎座", "mbti": "INTP"},
    {"name": "小倩", "gender": "女", "age": 24, "height": 167, "weight": 50, "work_location": "重庆渝北", "industry": "旅游", "constellation": "白羊座", "mbti": "ENFP"},
    {"name": "阿哲", "gender": "男", "age": 29, "height": 181, "weight": 76, "work_location": "杭州萧山", "industry": "物流", "constellation": "金牛座", "mbti": "ENTJ"},
    {"name": "小月", "gender": "女", "age": 22, "height": 161, "weight": 47, "work_location": "厦门思明", "industry": "新媒体", "constellation": "巨蟹座", "mbti": "INFP"},
    {"name": "阿飞", "gender": "男", "age": 30, "height": 183, "weight": 80, "work_location": "武汉洪山", "industry": "汽车", "constellation": "水瓶座", "mbti": "ENTP"},
    {"name": "小萱", "gender": "女", "age": 25, "height": 165, "weight": 52, "work_location": "南京建邺", "industry": "食品", "constellation": "双子座", "mbti": "ESFJ"},
    {"name": "阿辉", "gender": "男", "age": 28, "height": 176, "weight": 73, "work_location": "广州越秀", "industry": "贸易", "constellation": "摩羯座", "mbti": "ISTJ"},
    {"name": "小婷", "gender": "女", "age": 23, "height": 162, "weight": 48, "work_location": "上海长宁", "industry": "时尚", "constellation": "天秤座", "mbti": "ESFP"},
]

# 审核状态分布（质量好的邀请人倾向于邀请更多approved的人）
STATUS_CHOICES = ['approved', 'approved', 'approved', 'published', 'rejected', 'pending']
# "坏"邀请人的分布
BAD_STATUS_CHOICES = ['rejected', 'rejected', 'pending', 'approved']


def clear_mock_data(db):
    """清除已有的模拟数据（openid 以 mock_ 开头的）"""
    db.query(InvitationCode).filter(InvitationCode.notes.like('%模拟数据%')).delete(synchronize_session=False)
    db.query(UserProfile).filter(UserProfile.openid.like('mock_%')).delete(synchronize_session=False)
    db.commit()
    print("✅ 已清除旧的模拟数据")


def create_user(db, user_data, serial_num, status, invited_by_id=None, invitation_code_used=None, referred_by=None, base_time=None):
    """创建一个模拟用户"""
    profile = UserProfile(
        openid=f"mock_{serial_num}_{random.randint(1000, 9999)}",
        serial_number=str(serial_num).zfill(3),
        name=user_data["name"],
        gender=user_data["gender"],
        age=user_data["age"],
        height=user_data["height"],
        weight=user_data["weight"],
        work_location=user_data["work_location"],
        industry=user_data["industry"],
        constellation=user_data.get("constellation"),
        mbti=user_data.get("mbti"),
        marital_status="未婚",
        body_type=random.choice(["匀称", "偏瘦", "微胖", "运动型"]),
        hometown=random.choice(["湖南长沙", "广东广州", "四川成都", "浙江杭州", "江苏南京", "福建厦门", "湖北武汉"]),
        hobbies=random.sample(["健身", "读书", "旅行", "摄影", "音乐", "电影", "烹饪", "游泳", "跑步", "画画"], k=random.randint(2, 5)),
        lifestyle=random.choice(["早睡早起", "夜猫子", "规律作息", "随性"]),
        coming_out_status=random.choice(["已出柜", "半出柜", "未出柜"]),
        status=status,
        invited_by=invited_by_id,
        invitation_code_used=invitation_code_used,
        referred_by=referred_by,
        invitation_quota=2 if status in ('approved', 'published') else 0,
        photos=[],
        create_time=base_time or datetime.utcnow(),
        reviewed_at=(base_time + timedelta(days=random.randint(1, 3))) if base_time and status in ('approved', 'published', 'rejected') else None,
        reviewed_by="admin" if status in ('approved', 'published', 'rejected') else None,
        rejection_reason="资料不完整，请补充后重新提交" if status == 'rejected' else None,
        admin_contact="casper_gb",
    )
    db.add(profile)
    db.flush()  # 获取 ID
    return profile


def create_invitation(db, code, created_by, created_by_type, used_by_openid=None, used_by_id=None, is_used=False, base_time=None):
    """创建邀请码"""
    inv = InvitationCode(
        code=code,
        created_by=created_by,
        created_by_type=created_by_type,
        is_used=is_used,
        used_by=used_by_id,
        used_by_openid=used_by_openid,
        used_at=(base_time + timedelta(hours=random.randint(1, 48))) if is_used and base_time else None,
        notes="模拟数据",
        create_time=base_time or datetime.utcnow(),
        expire_at=(base_time + timedelta(days=7)) if base_time else None,
    )
    db.add(inv)
    db.flush()
    return inv


def seed_data():
    """生成模拟邀请关系网络"""
    db = SessionLocal()

    try:
        clear_mock_data(db)

        # 获取当前最大 serial_number
        last = db.query(UserProfile).filter(
            ~UserProfile.openid.like('mock_%')
        ).order_by(UserProfile.id.desc()).first()
        start_serial = 1
        if last and last.serial_number:
            try:
                start_serial = int(last.serial_number) + 1
            except:
                pass

        serial = start_serial
        base_time = datetime.utcnow() - timedelta(days=60)
        user_pool = list(MOCK_USERS)
        random.shuffle(user_pool)

        created_profiles = []

        print("\n🌳 开始生成邀请关系树...\n")

        # ====== 第0层: 管理员直接邀请的种子用户 (3人) ======
        print("【第0层】管理员直邀种子用户")
        layer_0 = []
        for i in range(3):
            user_data = user_pool.pop(0)
            code = generate_invitation_code()
            status = 'approved' if i < 2 else 'published'
            time_offset = base_time + timedelta(days=i * 2)

            # 管理员创建邀请码
            inv = create_invitation(db, code, 0, "admin", is_used=True, base_time=time_offset)
            # 创建用户
            profile = create_user(db, user_data, serial, status,
                                  invitation_code_used=code, referred_by="管理员",
                                  base_time=time_offset)
            inv.used_by = profile.id
            inv.used_by_openid = profile.openid

            layer_0.append(profile)
            created_profiles.append(profile)
            print(f"  ├── {profile.serial_number} {profile.name} ({status})")
            serial += 1

        # ====== 第1层: 种子用户邀请的人 (每人邀请 2-3 人) ======
        print("\n【第1层】种子用户邀请")
        layer_1 = []
        for parent in layer_0:
            # 决定这个用户的"邀请质量" — 第一个种子用户质量高，第三个质量差
            is_good = parent == layer_0[0]
            is_bad = parent == layer_0[2]
            num_invites = random.randint(2, 3)

            for j in range(num_invites):
                if not user_pool:
                    break
                user_data = user_pool.pop(0)
                code = generate_invitation_code()
                time_offset = base_time + timedelta(days=random.randint(5, 15))

                if is_good:
                    status = random.choice(['approved', 'approved', 'published'])
                elif is_bad:
                    status = random.choice(BAD_STATUS_CHOICES)
                else:
                    status = random.choice(STATUS_CHOICES)

                # 用户创建邀请码
                inv = create_invitation(db, code, parent.id, "user", is_used=True, base_time=time_offset)
                profile = create_user(db, user_data, serial, status,
                                      invited_by_id=parent.id,
                                      invitation_code_used=code,
                                      referred_by=f"{parent.name}（{parent.serial_number}）",
                                      base_time=time_offset)
                inv.used_by = profile.id
                inv.used_by_openid = profile.openid

                # 给已通过的用户也创建邀请码(未使用)
                if status in ('approved', 'published'):
                    for _ in range(2):
                        unused_code = generate_invitation_code()
                        create_invitation(db, unused_code, profile.id, "user", is_used=False, base_time=time_offset)

                layer_1.append(profile)
                created_profiles.append(profile)
                print(f"  ├── {parent.serial_number} {parent.name} → {profile.serial_number} {profile.name} ({status})")
                serial += 1

        # ====== 第2层: 第1层中 approved 的用户继续邀请 ======
        print("\n【第2层】二级邀请")
        layer_2 = []
        approved_layer1 = [p for p in layer_1 if p.status in ('approved', 'published')]
        for parent in approved_layer1[:4]:  # 最多取4个人继续邀请
            num_invites = random.randint(1, 2)
            for j in range(num_invites):
                if not user_pool:
                    break
                user_data = user_pool.pop(0)
                code = generate_invitation_code()
                time_offset = base_time + timedelta(days=random.randint(20, 35))
                status = random.choice(STATUS_CHOICES)

                inv = create_invitation(db, code, parent.id, "user", is_used=True, base_time=time_offset)
                profile = create_user(db, user_data, serial, status,
                                      invited_by_id=parent.id,
                                      invitation_code_used=code,
                                      referred_by=f"{parent.name}（{parent.serial_number}）",
                                      base_time=time_offset)
                inv.used_by = profile.id
                inv.used_by_openid = profile.openid

                if status in ('approved', 'published'):
                    for _ in range(2):
                        unused_code = generate_invitation_code()
                        create_invitation(db, unused_code, profile.id, "user", is_used=False, base_time=time_offset)

                layer_2.append(profile)
                created_profiles.append(profile)
                print(f"  ├── {parent.serial_number} {parent.name} → {profile.serial_number} {profile.name} ({status})")
                serial += 1

        # ====== 第3层: 更深一层 ======
        print("\n【第3层】三级邀请")
        approved_layer2 = [p for p in layer_2 if p.status in ('approved', 'published')]
        for parent in approved_layer2[:2]:
            if not user_pool:
                break
            user_data = user_pool.pop(0)
            code = generate_invitation_code()
            time_offset = base_time + timedelta(days=random.randint(40, 55))
            status = random.choice(['approved', 'pending'])

            inv = create_invitation(db, code, parent.id, "user", is_used=True, base_time=time_offset)
            profile = create_user(db, user_data, serial, status,
                                  invited_by_id=parent.id,
                                  invitation_code_used=code,
                                  referred_by=f"{parent.name}（{parent.serial_number}）",
                                  base_time=time_offset)
            inv.used_by = profile.id
            inv.used_by_openid = profile.openid
            created_profiles.append(profile)
            print(f"  ├── {parent.serial_number} {parent.name} → {profile.serial_number} {profile.name} ({status})")
            serial += 1

        db.commit()

        # ====== 统计 ======
        total = len(created_profiles)
        approved = sum(1 for p in created_profiles if p.status in ('approved', 'published'))
        rejected = sum(1 for p in created_profiles if p.status == 'rejected')
        pending = sum(1 for p in created_profiles if p.status == 'pending')

        print(f"\n{'='*60}")
        print(f"✅ 模拟数据生成完成！")
        print(f"{'='*60}")
        print(f"  总用户数: {total}")
        print(f"  已通过/已发布: {approved}")
        print(f"  已拒绝: {rejected}")
        print(f"  待审核: {pending}")
        print(f"  邀请层级: 4层 (管理员 → 种子 → 二级 → 三级)")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
