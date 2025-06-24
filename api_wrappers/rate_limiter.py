# DonyanUtils/api_wrappers/rate_limiter.py
import time
import threading
from collections import deque

class RateLimiter:
    """
    一个简单的速率限制器。
    """
    def __init__(self, max_requests, per_seconds):
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.requests_timestamps = deque()
        self.lock = threading.Lock()
        self.total_calls_allowed = 0 # 用于跟踪等待后允许的调用次数

    def wait_if_needed(self):
        with self.lock:
            now = time.monotonic()
            # 移除窗口期之外的旧时间戳
            while self.requests_timestamps and self.requests_timestamps[0] <= now - self.per_seconds:
                self.requests_timestamps.popleft()

            if len(self.requests_timestamps) >= self.max_requests:
                oldest_request_time = self.requests_timestamps[0]
                wait_time = (oldest_request_time + self.per_seconds) - now
                if wait_time > 0:
                    # print(f"RateLimiter: 等待 {wait_time:.2f} 秒。")
                    time.sleep(wait_time)
            # 在可能的等待后记录当前请求时间
            self.requests_timestamps.append(time.monotonic())
            self.total_calls_allowed +=1

    def get_total_calls_allowed(self):
        """返回wait_if_needed成功允许调用的次数。"""
        return self.total_calls_allowed

    # 允许作为上下文管理器使用
    def __enter__(self):
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass # 对于这个简单的限制器，退出时无需执行任何操作