# DonyanUtils/file_system/io_helpers.py
import os
import json
import requests
from pathlib import Path
from datetime import datetime

def ensure_dir_exists(dir_path):
    """确保目录存在，如有必要则创建它。"""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def read_text_file(filepath, encoding='utf-8'):
    """读取文本文件并返回其内容。"""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error reading text file {filepath}: {e}")
        return None

def write_text_file(content, filepath, encoding='utf-8'):
    """将内容写入文本文件。"""
    try:
        ensure_dir_exists(Path(filepath).parent)
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing text file {filepath}: {e}")
        return False

def read_json_file(filepath, encoding='utf-8'):
    """读取JSON文件并返回其内容。"""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {filepath}")
        return None
    except Exception as e:
        print(f"Error reading JSON file {filepath}: {e}")
        return None

def write_json_file(data, filepath, encoding='utf-8', indent=2, ensure_ascii=False):
    """将数据写入JSON文件。"""
    try:
        ensure_dir_exists(Path(filepath).parent)
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        return True
    except Exception as e:
        print(f"Error writing JSON file {filepath}: {e}")
        return False

def download_file(url, filepath, timeout=30):
    """从URL下载文件到指定的文件路径。"""
    try:
        ensure_dir_exists(Path(filepath).parent)
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {url} to {filepath}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"Error saving downloaded file to {filepath}: {e}")
        return False

def create_placeholder_image(filepath, error_message="图像生成失败", width=512, height=512, color='lightgray'):
    """创建占位符图像（需要Pillow库）。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        ensure_dir_exists(Path(filepath).parent)
        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        text_lines = [
            Path(filepath).name,
            "Placeholder Image",
            f"Error: {str(error_message)[:60]}...",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ]
        y_offset = height // 4
        for line in text_lines:
            wrapped_lines = textwrap.wrap(line, width=int(width / (font.size * 0.6 if hasattr(font, 'size') else 10))) # 粗略估计
            for wrapped_line in wrapped_lines:
                try: # PIL 10.x.x版本
                    bbox = draw.textbbox((0,0), wrapped_line, font=font)
                    text_w = bbox[2] - bbox[0]
                    # text_h = bbox[3] - bbox[1] # 这里未使用
                except AttributeError: # 较旧的PIL版本
                    text_w, text_h = draw.textsize(wrapped_line, font=font)

                x = (width - text_w) // 2
                draw.text((x, y_offset), wrapped_line, fill='black', font=font)
                y_offset += (font.size if hasattr(font, 'size') else 20) + 5
        img.save(filepath, 'JPEG')
        print(f"Placeholder image created: {filepath}")
        return True
    except ImportError:
        print("未找到Pillow库。无法创建占位符图像。改为创建文本占位符。")
        return create_placeholder_text(filepath.replace(Path(filepath).suffix, "_FAILED.txt"), error_message)
    except Exception as e:
        print(f"Error creating placeholder image {filepath}: {e}")
        return False

def create_placeholder_text(filepath, error_message="任务失败"):
    """创建占位符文本文件。"""
    content = (
        f"TASK FAILED\n"
        f"Original Filename: {Path(filepath).name}\n"
        f"Error: {error_message}\n"
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    return write_text_file(content, filepath)