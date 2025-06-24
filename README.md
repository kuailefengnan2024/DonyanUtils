
# DonyanUtils: 个人Python实用工具库

`DonyanUtils` 是一个轻量级的个人Python工具库，封装常用功能，提升开发效率。

##核心模块

*   **`DonyanUtils.api_wrappers`**:
    *   `VolcengineArkTextClient` & `VolcengineSeedreamClient`: 火山引擎方舟平台文本与图像API客户端。
    *   `RateLimiter`: API请求速率控制器。
*   **`DonyanUtils.file_system`**:
    *   `io_helpers`: 文件读写（文本、JSON）、目录创建、文件下载、占位符生成（图片/文本）。
    *   `parsers`: 解析特定格式的MD文件和记录分隔的文本文件。
*   **`DonyanUtils.task_runner`**:
    *   `run_concurrently`: 并发执行任务（线程/进程池），带进度跟踪。
    *   `ProgressTracker`: 任务进度统计。

## 安装

1.  **直接复制代码**: 将 `DonyanUtils` 文件夹置于项目可访问路径。
2.  **本地安装 (推荐)**:
    ```bash
    pip install -e .  # 在DonyanUtils_project根目录执行
    ```

## 主要依赖

*   `requests`
*   `Pillow` (占位图功能可选)
*   `volcenginesdkarkruntime` (火山引擎客户端功能)

安装依赖:
```bash
pip install requests Pillow volcenginesdkarkruntime
```

## 快速上手

```python
from DonyanUtils.file_system import read_json_file, ensure_dir_exists
from DonyanUtils.api_wrappers import RateLimiter
from DonyanUtils.task_runner import run_concurrently

# 创建目录
ensure_dir_exists("data/output")

# 定义一个受速率限制的任务
limiter = RateLimiter(max_requests=2, per_seconds=1)
def process_item(item_id):
    with limiter:
        print(f"Processing: {item_id}")
        # ... 模拟一些工作 ...
        return f"Done: {item_id}"

# 并发执行任务
items_to_process = list(range(10))
results = run_concurrently(items_to_process, process_item, max_workers=3)
print("\nResults:", results)
```
