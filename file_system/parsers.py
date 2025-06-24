# DonyanUtils/file_system/parsers.py
import re

def parse_key_value_md(filepath, section_separator='||', item_separator=' - ', encoding='utf-8'):
    """
    解析带有章节和键值项的markdown文件。
    返回字典列表，每个字典代表一个章节，
    并包含(键, 值)元组的列表。
    示例MD结构：
    类别1 - 项目A1
    类别1 - 项目A2
    ||
    区域1 - 场景X
    区域1 - 场景Y
    """
    from .io_helpers import read_text_file # Local import to avoid circular dependency if called directly
    content = read_text_file(filepath, encoding)
    if content is None:
        return None

    parsed_data = []
    sections = content.strip().split(section_separator)

    for section_content in sections:
        section_data = {"name": f"section_{len(parsed_data)+1}", "items": []} # 默认名称
        lines = section_content.strip().split('\n')
        current_items = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(item_separator, 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                current_items.append((key, value))
            else:
                # 处理不符合键值结构的行，
                # 例如，作为多行值的一部分或仅单个条目
                current_items.append((None, line)) # 或 ((line, None)) 或跳过
        if current_items:
             section_data["items"] = current_items
        parsed_data.append(section_data)

    return parsed_data


def read_separated_records(filepath, separator_regex=r"\n\n==================================================\n\n", encoding='utf-8'):
    """
    从文件中读取记录，记录由给定的字符串或正则表达式分隔。
    """
    from .io_helpers import read_text_file
    content = read_text_file(filepath, encoding)
    if content is None:
        return []

    # 使用re.split处理复杂的分隔符，如果需要的话保留空字符串
    # （尽管通常我们会去除和过滤它们）
    records = re.split(separator_regex, content.strip())
    return [record.strip() for record in records if record.strip()]


def write_separated_records(records, filepath, separator="\n\n==================================================\n\n", encoding='utf-8'):
    """
    将记录列表写入文件，用分隔符连接。
    """
    from .io_helpers import write_text_file
    content = separator.join(records)
    return write_text_file(content, filepath, encoding)