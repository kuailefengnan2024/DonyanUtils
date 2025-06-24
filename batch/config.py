from dataclasses import dataclass


@dataclass
class BatchConfig:
    """批量处理配置"""
    max_workers: int = 10  # 最大并发数
    rate_limit_per_minute: int = 60  # 每分钟最大请求数
    rate_limit_window: int = 60  # 速率限制时间窗口（秒）
    request_delay: float = 0.1  # 请求间隔（秒）
    max_retries: int = 2  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    timeout: float = 30.0  # 单个任务超时时间（秒） 