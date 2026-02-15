"""
AI 自动审核服务
功能：
1. 分析用户提交的资料，检测缺失的关键字段
2. 如果缺失 → 自动拒绝，生成提示文案
3. 如果用户在备注中补充了信息 → 从备注中解析出结构化数据并回填

★ 默认使用智谱 GLM-4.7-Flash（免费）
"""
import httpx
import json
import logging
from typing import Dict, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================
# 需要 AI 补全的字段定义
# ============================================================
REQUIRED_FIELDS = {
    "marital_status": "感情状态（如：单身、离异、丧偶等）",
    "health_condition": "健康状况（如：健康、HIV阴性等）",
    "housing_status": "住房情况（如：租房、自有住房、和家人同住等）",
    "dating_purpose": "交友目的（如：寻找长期伴侣、交朋友、开放关系等）",
    "want_children": "是否想要孩子（如：想要、不想要、可以考虑等）",
    "coming_out_status": "出柜状态（如：已出柜、半出柜、未出柜等）",
}

# expectation 子字段
EXPECTATION_FIELDS = {
    "relationship": "期待的关系类型",
    "age_range": "期待对方的年龄范围",
    "personality": "期待对方的性格特点",
    "location": "期待对方的所在地区",
}


def _collect_user_text(profile_data: dict) -> str:
    """
    从「自我描述」「对活动的期望」「备注」三个字段中收集用户填写的所有文本
    合并后供 AI 统一解析
    """
    parts = []

    lifestyle = profile_data.get("lifestyle") or ""
    if lifestyle.strip():
        parts.append(f"【自我描述】\n{lifestyle.strip()}")

    activity = profile_data.get("activity_expectation") or ""
    if activity.strip():
        parts.append(f"【对活动的期望】\n{activity.strip()}")

    special = profile_data.get("special_requirements") or ""
    if special.strip():
        parts.append(f"【备注】\n{special.strip()}")

    return "\n\n".join(parts)


def _get_missing_fields(profile_data: dict) -> Dict[str, str]:
    """检测资料中缺失的字段，返回 {字段名: 字段描述}"""
    missing = {}

    for field, desc in REQUIRED_FIELDS.items():
        value = profile_data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            missing[field] = desc

    # 检查 expectation 子字段
    expectation = profile_data.get("expectation") or {}
    if isinstance(expectation, str):
        try:
            expectation = json.loads(expectation)
        except (json.JSONDecodeError, TypeError):
            expectation = {}

    has_any_expectation = False
    for field, desc in EXPECTATION_FIELDS.items():
        value = expectation.get(field)
        if value and isinstance(value, str) and value.strip():
            has_any_expectation = True
            break

    if not has_any_expectation:
        missing["expectation"] = "对另一半的期待（年龄范围、性格、关系类型、地区偏好等）"

    return missing


def _build_rejection_message(missing: Dict[str, str]) -> str:
    """生成拒绝原因文案（用户可以复制）"""
    lines = [
        "您好！感谢您提交报名信息。",
        "",
        "为了更好地为您匹配，我们还需要以下信息，请将这些内容补充到「备注」栏中，然后重新提交：",
        "",
    ]

    for i, (field, desc) in enumerate(missing.items(), 1):
        lines.append(f"{i}. {desc}")

    lines.append("")
    lines.append("💡 如果某项信息您不方便透露，可以填写「未知」「不想回答」或「保密」，我们完全理解。")
    lines.append("")
    lines.append("【参考格式（可直接复制后修改）】")
    lines.append("---")

    template_parts = []
    for field, desc in missing.items():
        if field == "marital_status":
            template_parts.append("感情状态：单身")
        elif field == "health_condition":
            template_parts.append("健康状况：健康")
        elif field == "housing_status":
            template_parts.append("住房情况：租房")
        elif field == "dating_purpose":
            template_parts.append("交友目的：寻找长期伴侣")
        elif field == "want_children":
            template_parts.append("是否想要孩子：可以考虑（或填「不想回答」）")
        elif field == "coming_out_status":
            template_parts.append("出柜状态：半出柜（或填「不想回答」）")
        elif field == "expectation":
            template_parts.append("期待对象：希望对方25-35岁，性格温和，最好在同城（或填「暂无特别要求」）")

    lines.extend(template_parts)
    lines.append("---")
    lines.append("")
    lines.append("请修改信息后重新提交，感谢您的配合！")

    return "\n".join(lines)


async def _call_ai_api(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    调用 AI API
    ★ 智谱 GLM 使用 OpenAI 兼容格式
    ★ 也支持 Claude / DeepSeek / 通义千问等

    返回 AI 的文本回复，失败返回 None
    """
    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY 未配置，跳过 AI 分析")
        return None

    headers = {
        "Content-Type": "application/json",
    }

    if settings.AI_API_TYPE == "claude":
        # Anthropic Claude 格式
        headers["x-api-key"] = settings.AI_API_KEY
        headers["anthropic-version"] = "2023-06-01"
        payload = {
            "model": settings.AI_MODEL,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
    else:
        # ★ OpenAI 兼容格式（智谱 GLM / DeepSeek / 通义千问等）
        headers["Authorization"] = f"Bearer {settings.AI_API_KEY}"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": settings.AI_MODEL,
            "max_tokens": 2000,
            "messages": messages,
            "temperature": 0.1,  # 低温度，输出更稳定
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(settings.AI_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if settings.AI_API_TYPE == "claude":
            return data.get("content", [{}])[0].get("text", "")
        else:
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    except httpx.HTTPStatusError as e:
        logger.error(f"AI API HTTP错误: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"AI API 调用失败: {e}")
        return None


async def _ai_extract_fields(
    user_text: str,
    missing_fields: Dict[str, str],
    profile_context: dict,
) -> Optional[dict]:
    """让 AI 从用户填写的多个文本字段中提取结构化数据"""
    system_prompt = """你是一个数据提取助手。用户在表单的多个文本栏中填写了个人信息，请从中提取出结构化数据。
信息可能分散在「自我描述」「对活动的期望」「备注」等不同栏目中，请综合分析所有内容。
请严格按照 JSON 格式返回，不要添加任何其他文字或 markdown 标记。
如果用户明确表示「未知」「不想回答」「保密」「不方便说」等，请将该字段值设为用户的原始表述（如"不想回答"），而非 null。
只有当文本中完全没有提及某个字段时，才将该字段值设为 null。"""

    fields_desc = "\n".join([f"- {k}: {v}" for k, v in missing_fields.items()])

    prompt = f"""用户的基本资料：
姓名: {profile_context.get('name', '未知')}
性别: {profile_context.get('gender', '未知')}
年龄: {profile_context.get('age', '未知')}

用户在表单中填写的文本内容（可能分布在多个栏目）：
\"\"\"
{user_text}
\"\"\"

请从上述所有文本中综合提取以下字段：
{fields_desc}

请返回 JSON 格式，字段名使用英文 key。
对于 expectation 字段，请返回一个包含以下子字段的对象：
- relationship: 期待的关系类型
- age_range: 期待年龄范围
- personality: 期待性格
- location: 期待地区
- body_type: 期待体型
- appearance: 期待外貌
- habits: 期待生活习惯
- children: 对孩子的态度
- other: 其他期待

示例返回格式：
{{"marital_status": "单身", "health_condition": "健康", "housing_status": "租房", "dating_purpose": "寻找长期伴侣", "want_children": "可以考虑", "coming_out_status": "半出柜", "expectation": {{"relationship": "长期伴侣", "age_range": "25-35", "personality": "温和", "location": "上海", "body_type": null, "appearance": null, "habits": null, "children": null, "other": null}}}}

只返回 JSON，不要有其他任何内容。"""

    result = await _call_ai_api(prompt, system_prompt)
    if not result:
        return None

    # 清理 AI 返回（去掉 markdown 代码块标记）
    cleaned = result.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            logger.error(f"AI 返回非 dict 类型: {type(parsed)}")
            return None
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"AI 返回 JSON 解析失败: {e}\n原始内容: {result}")
        return None


# ============================================================
# 主入口函数
# ============================================================

async def auto_review_profile(profile_data: dict) -> Tuple[str, Optional[str], Optional[dict]]:
    """
    自动审核资料

    返回:
        (action, reason, extracted_data)
        - "reject": 需要自动拒绝
        - "pass": AI 审核通过，等待管理员终审
        - "error": AI 出错，跳过
    """

    # 1. 检测缺失字段
    missing = _get_missing_fields(profile_data)

    if not missing:
        logger.info(f"资料完整，AI 审核通过: {profile_data.get('name', '?')}")
        return "pass", None, None

    # 2. 有缺失 → 检查所有文本字段是否有补充信息
    user_text = _collect_user_text(profile_data)

    if not user_text.strip():
        # 所有文本字段都为空 → 直接拒绝（不调用 AI，零成本）
        reason = _build_rejection_message(missing)
        logger.info(f"缺失 {len(missing)} 个字段且无文本内容，自动拒绝: {profile_data.get('name', '?')}")
        return "reject", reason, None

    # 3. 有文本内容 → 调用 AI 从「自我描述」「对活动的期望」「备注」中综合提取
    logger.info(f"尝试从用户文本中提取 {len(missing)} 个缺失字段: {profile_data.get('name', '?')}")

    extracted = await _ai_extract_fields(user_text, missing, profile_data)

    if extracted is None:
        logger.warning("AI 提取失败，跳过自动审核")
        return "error", None, None

    # 4. 检查是否全部提取成功
    still_missing = {}
    for field, desc in missing.items():
        if field == "expectation":
            exp = extracted.get("expectation")
            if not exp or not isinstance(exp, dict):
                still_missing[field] = desc
            else:
                has_any = any(
                    v and isinstance(v, str) and v.strip()
                    for v in exp.values()
                    if v is not None
                )
                if not has_any:
                    still_missing[field] = desc
        else:
            value = extracted.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                still_missing[field] = desc

    if still_missing:
        reason = _build_rejection_message(still_missing)
        logger.info(f"AI 提取后仍缺 {len(still_missing)} 个字段，自动拒绝")
        return "reject", reason, None

    # 5. 全部成功
    logger.info(f"AI 提取成功，所有字段已补全: {profile_data.get('name', '?')}")
    return "pass", None, extracted
