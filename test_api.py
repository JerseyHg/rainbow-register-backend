"""
API测试脚本
用于快速测试所有API是否正常工作
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


async def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200


async def test_root():
    """测试根路径"""
    print("\n=== 测试根路径 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200


async def test_admin_login():
    """测试管理员登录"""
    print("\n=== 测试管理员登录 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/admin/login",
            json={
                "username": "admin",
                "password": "change_this_password"
            }
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")

        if response.status_code == 200 and data.get("success"):
            return data.get("token")
        return None


async def test_generate_invitations(token: str):
    """测试生成邀请码"""
    print("\n=== 测试生成邀请码 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/admin/invitation/generate",
            params={"count": 3, "notes": "测试生成"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")

        if response.status_code == 200 and data.get("success"):
            codes = data.get("data", {}).get("codes", [])
            return codes[0] if codes else None
        return None


async def test_verify_invitation(code: str):
    """测试验证邀请码"""
    print("\n=== 测试验证邀请码 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/invitation/verify",
            json={
                "invitation_code": code,
                "wx_code": "test_wx_code_123"
            }
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")

        if response.status_code == 200:
            return data.get("openid")
        return None


async def test_submit_profile(openid: str):
    """测试提交资料"""
    print("\n=== 测试提交资料 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/profile/submit",
            json={
                "name": "测试用户",
                "gender": "男性",
                "age": 25,
                "height": 175,
                "weight": 70,
                "marital_status": "未婚",
                "body_type": "型号1",
                "hometown": "北京",
                "work_location": "上海",
                "industry": "IT",
                "hobbies": ["健身", "旅行"],
                "expectation": {
                    "relationship": "交友",
                    "age_range": "23-30"
                },
                "photos": []
            },
            headers={"Authorization": openid}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")

        if response.status_code == 200:
            return data.get("data", {}).get("profile_id")
        return None


async def test_get_pending_profiles(token: str):
    """测试获取待审核列表"""
    print("\n=== 测试获取待审核列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/profiles/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")
        return response.status_code == 200


async def test_preview_post(token: str, profile_id: int):
    """测试预览公众号文案"""
    print("\n=== 测试预览公众号文案 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/profile/{profile_id}/preview-post",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            post = data.get("data", {})
            print(f"\n标题: {post.get('title')}")
            print(f"\n内容:\n{post.get('content')}")
        return response.status_code == 200


async def test_approve_profile(token: str, profile_id: int):
    """测试通过审核"""
    print("\n=== 测试通过审核 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/admin/profile/{profile_id}/approve",
            json={"notes": "测试通过"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")
        return response.status_code == 200


async def main():
    """主测试流程"""
    print("=" * 60)
    print("Rainbow Register Backend - API 测试")
    print("=" * 60)

    # 1. 基础测试
    if not await test_health():
        print("\n❌ 健康检查失败！请确保服务已启动")
        return

    await test_root()

    # 2. 管理员登录
    token = await test_admin_login()
    if not token:
        print("\n❌ 管理员登录失败！请检查配置")
        return

    print(f"\n✅ 获得Token: {token[:20]}...")

    # 3. 生成邀请码
    invitation_code = await test_generate_invitations(token)
    if not invitation_code:
        print("\n❌ 生成邀请码失败！")
        return

    print(f"\n✅ 生成邀请码: {invitation_code}")

    # 4. 验证邀请码
    openid = await test_verify_invitation(invitation_code)
    if not openid:
        print("\n❌ 验证邀请码失败！")
        return

    print(f"\n✅ 获得OpenID: {openid}")

    # 5. 提交资料
    profile_id = await test_submit_profile(openid)
    if not profile_id:
        print("\n❌ 提交资料失败！")
        return

    print(f"\n✅ 提交资料成功，ID: {profile_id}")

    # 6. 获取待审核列表
    await test_get_pending_profiles(token)

    # 7. 预览文案
    await test_preview_post(token, profile_id)

    # 8. 通过审核
    await test_approve_profile(token, profile_id)

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())