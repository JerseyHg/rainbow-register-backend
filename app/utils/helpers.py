"""
辅助函数
"""
from datetime import datetime, date


def generate_serial_number(last_number: int) -> str:
    """
    生成编号
    """
    next_number = (last_number or 0) + 1
    return f"{next_number:03d}"


def datetime_to_str(dt: datetime) -> str:
    """datetime转字符串"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None


def calculate_age(birthday_str: str) -> int:
    """
    根据生日字符串计算年龄
    :param birthday_str: 格式 "YYYY-MM-DD"
    :return: 年龄（整数）
    """
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birthday.year
    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1
    return age


def calculate_constellation(birthday_str: str) -> str:
    """
    根据生日字符串计算星座
    :param birthday_str: 格式 "YYYY-MM-DD"
    :return: 星座名称
    """
    dt = datetime.strptime(birthday_str, "%Y-%m-%d")
    month = dt.month
    day = dt.day

    # (截止日期, 星座名称)
    # 每个月份对应的星座分界日
    constellation_dates = [
        (1, 20, "摩羯座"), (2, 19, "水瓶座"), (3, 20, "双鱼座"),
        (4, 20, "白羊座"), (5, 21, "金牛座"), (6, 21, "双子座"),
        (7, 22, "巨蟹座"), (8, 22, "狮子座"), (9, 22, "处女座"),
        (10, 23, "天秤座"), (11, 22, "天蝎座"), (12, 21, "射手座"),
    ]

    for end_month, end_day, name in constellation_dates:
        if month == end_month and day <= end_day:
            return name

    # 如果没有匹配到（说明日期在当月分界日之后），取下一个星座
    constellation_after = [
        "水瓶座", "双鱼座", "白羊座", "金牛座", "双子座", "巨蟹座",
        "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座",
    ]
    return constellation_after[month - 1]
