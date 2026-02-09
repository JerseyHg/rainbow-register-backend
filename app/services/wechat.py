"""
微信相关服务
"""
import httpx
from app.core.config import settings
from typing import Optional


async def get_openid_from_code(wx_code: str) -> Optional[str]:
    """
    通过微信code获取openid
    """
    # 如果没有配置微信参数，返回模拟openid（开发用）
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        # 开发模式：使用code作为openid
        return f"dev_openid_{wx_code}"

    # 生产模式：调用微信API
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "js_code": wx_code,
        "grant_type": "authorization_code"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()

            if "openid" in data:
                return data["openid"]
            else:
                print(f"微信API错误: {data}")
                return None
    except Exception as e:
        print(f"调用微信API异常: {e}")
        return None