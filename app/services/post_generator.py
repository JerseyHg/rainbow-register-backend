"""
公众号文案生成服务
"""
from typing import Dict, Any


def generate_post_content(profile: Dict[str, Any]) -> Dict[str, str]:
    """
    根据用户资料生成公众号文案
    """
    # 生成标题
    title_parts = []

    # 添加地域标签
    if profile.get('work_location'):
        location = profile['work_location'].split()[0]
        title_parts.append(location)

    # 添加特征标签
    hobbies = profile.get('hobbies', [])
    if isinstance(hobbies, list):
        if '健身' in hobbies or '运动' in hobbies:
            title_parts.append('爱运动')

    # 添加外貌期待
    expectation = profile.get('expectation', {})
    if isinstance(expectation, dict):
        appearance = expectation.get('appearance', '')
        if '短发' in appearance:
            title_parts.append('喜短发')

    title = f"特伴№{profile.get('serial_number', '000')} {' '.join(title_parts)}"

    # 生成内容
    content_lines = []

    # 第一行：基本信息
    basic_info = (
        f"{profile.get('gender', '')} "
        f"{profile.get('age', '')}/{profile.get('height', '')}/{profile.get('weight', '')}kg "
        f"{profile.get('marital_status', '')} "
        f"型号{profile.get('body_type', '')}"
    )
    content_lines.append(basic_info)

    # 地域和工作
    work_info = (
        f"{profile.get('hometown', '')}人 "
        f"{profile.get('work_location', '')}工作，"
        f"{profile.get('industry', '')}"
    )
    if profile.get('health_condition'):
        work_info += f"，{profile['health_condition']}"
    content_lines.append(work_info)

    # 个性特征
    traits = []
    if profile.get('constellation'):
        traits.append(profile['constellation'])
    if profile.get('mbti'):
        traits.append(profile['mbti'])
    if profile.get('coming_out_status'):
        traits.append(profile['coming_out_status'])
    if traits:
        content_lines.append(' '.join(traits))

    # ===== 新增：交友目的 =====
    if profile.get('dating_purpose'):
        content_lines.append(f"交友目的：{profile['dating_purpose']}")

    # ===== 新增：是否需要孩子 =====
    if profile.get('want_children'):
        content_lines.append(f"孩子意愿：{profile['want_children']}")

    # 生活方式
    if profile.get('lifestyle'):
        content_lines.append(profile['lifestyle'])

    # 期待对象
    content_lines.append("\n期待交友")

    if expectation:
        if expectation.get('relationship'):
            content_lines.append(expectation['relationship'])
        if expectation.get('body_type'):
            content_lines.append(expectation['body_type'])
        if expectation.get('appearance'):
            content_lines.append(expectation['appearance'])
        if expectation.get('age_range'):
            content_lines.append(f"接受{expectation['age_range']}")
        if expectation.get('habits'):
            content_lines.append(expectation['habits'])
        if expectation.get('location'):
            content_lines.append(expectation['location'])
        if expectation.get('children'):
            content_lines.append(expectation['children'])
        if expectation.get('other'):
            content_lines.append(expectation['other'])

    # 特殊要求
    if profile.get('special_requirements'):
        content_lines.append(profile['special_requirements'])

    # 联系方式
    content_lines.append(f"\n管理员V：{profile.get('admin_contact', 'casper_gb')}")

    content = '\n'.join(content_lines)

    return {
        "title": title,
        "content": content,
        "photos": profile.get('photos', [])
    }