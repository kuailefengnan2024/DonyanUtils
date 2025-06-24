# DonyanUtils/file_system/parsers.py
import re

def parse_key_value_md(filepath, section_separator='||', item_separator=' - ', encoding='utf-8'):
    """
    Parses a markdown file with sections and key-value items.
    Returns a list of dictionaries, where each dictionary represents a section,
    and contains a list of (key, value) tuples.
    Example MD structure:
    Category1 - ItemA1
    Category1 - ItemA2
    ||
    Region1 - SceneX
    Region1 - SceneY
    """
    from .io_helpers import read_text_file # Local import to avoid circular dependency if called directly
    content = read_text_file(filepath, encoding)
    if content is None:
        return None

    parsed_data = []
    sections = content.strip().split(section_separator)

    for section_content in sections:
        section_data = {"name": f"section_{len(parsed_data)+1}", "items": []} # Default name
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
                # Handle lines that don't match the key-value structure,
                # e.g., as part of a multi-line value or just single entries
                current_items.append((None, line)) # Or ((line, None)) or skip
        if current_items:
             section_data["items"] = current_items
        parsed_data.append(section_data)

    return parsed_data


def read_separated_records(filepath, separator_regex=r"\n\n==================================================\n\n", encoding='utf-8'):
    """
    Reads records from a file, where records are separated by a given string or regex.
    """
    from .io_helpers import read_text_file
    content = read_text_file(filepath, encoding)
    if content is None:
        return []

    # Using re.split to handle complex separators and keep empty strings if needed
    # (though usually we strip and filter them)
    records = re.split(separator_regex, content.strip())
    return [record.strip() for record in records if record.strip()]


def write_separated_records(records, filepath, separator="\n\n==================================================\n\n", encoding='utf-8'):
    """
    Writes a list of records to a file, joined by a separator.
    """
    from .io_helpers import write_text_file
    content = separator.join(records)
    return write_text_file(content, filepath, encoding)