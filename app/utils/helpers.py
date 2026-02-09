"""
辅助函数
"""
from datetime import datetime


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