"""
公众号文案生成服务
"""
from typing import Dict, Any


def generate_post_content(profile: Dict[str, Any]) -> Dict[str, str]:
    """
    根据用户资料生成公众号文案
    """
    title_parts = []

    if profile.get('work_location'):
        location = profile['work_location'].split()[0]
        title_parts.append(location)

    hobbies = profile.get('hobbies', [])
    if isinstance(hobbies, list):
        if '健身' in hobbies or '运动' in hobbies:
            title_parts.append('爱运动')

    expectation = profile.get('expectation', {})
    if isinstance(expectation, dict):
        appearance = expectation.get('appearance', '')
        if '短发' in appearance:
            title_parts.append('喜短发')

    title = f"档案№{profile.get('serial_number', '000')} {' '.join(title_parts)}"

    content_lines = []

    basic_info = (
        f"{profile.get('gender', '')} "
        f"{profile.get('age', '')}/{profile.get('height', '')}/{profile.get('weight', '')}kg "
        f"{profile.get('marital_status', '')} "
        f"型号{profile.get('body_type', '')}"
    )
    content_lines.append(basic_info)

    work_info = (
        f"{profile.get('hometown', '')}人 "
        f"{profile.get('work_location', '')}工作，"
        f"{profile.get('industry', '')}"
    )
    if profile.get('health_condition'):
        work_info += f"，{profile['health_condition']}"
    content_lines.append(work_info)

    traits = []
    if profile.get('constellation'):
        traits.append(profile['constellation'])
    if profile.get('mbti'):
        traits.append(profile['mbti'])
    if traits:
        content_lines.append(' '.join(traits))

    if profile.get('dating_purpose'):
        content_lines.append(f"期望方向：{profile['dating_purpose']}")

    if profile.get('want_children'):
        content_lines.append(f"生活规划：{profile['want_children']}")

    if profile.get('lifestyle'):
        content_lines.append(profile['lifestyle'])

    content_lines.append("\n期望匹配")

    if expectation:
        if expectation.get('relationship'):
            content_lines.append(f"期望方向：{expectation['relationship']}")
        if expectation.get('body_type'):
            content_lines.append(f"体型：{expectation['body_type']}")
        if expectation.get('appearance'):
            content_lines.append(f"外貌：{expectation['appearance']}")
        if expectation.get('age_range'):
            content_lines.append(f"年龄：{expectation['age_range']}")
        if expectation.get('habits'):
            content_lines.append(f"习惯：{expectation['habits']}")
        if expectation.get('personality'):
            content_lines.append(f"性格：{expectation['personality']}")
        if expectation.get('location'):
            content_lines.append(f"地域：{expectation['location']}")

    if profile.get('special_requirements'):
        content_lines.append(f"\n备注：{profile['special_requirements']}")

    content = '\n'.join(content_lines)

    return {
        "title": title,
        "content": content,
    }
