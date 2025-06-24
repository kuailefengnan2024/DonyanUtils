# DonyanUtils/api_wrappers/rate_limiter.py
import time
import threading
from collections import deque

class RateLimiter:
    """
    A simple rate limiter.
    """
    def __init__(self, max_requests, per_seconds):
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.requests_timestamps = deque()
        self.lock = threading.Lock()
        self.total_calls_allowed = 0 # For tracking calls made after waiting

    def wait_if_needed(self):
        with self.lock:
            now = time.monotonic()
            # Remove timestamps older than the window
            while self.requests_timestamps and self.requests_timestamps[0] <= now - self.per_seconds:
                self.requests_timestamps.popleft()

            if len(self.requests_timestamps) >= self.max_requests:
                oldest_request_time = self.requests_timestamps[0]
                wait_time = (oldest_request_time + self.per_seconds) - now
                if wait_time > 0:
                    # print(f"RateLimiter: waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time)
            # Record current request time after potential wait
            self.requests_timestamps.append(time.monotonic())
            self.total_calls_allowed +=1

    def get_total_calls_allowed(self):
        """Returns the number of times wait_if_needed has successfully allowed a call."""
        return self.total_calls_allowed

    # Allow using as a context manager for a block of code
    def __enter__(self):
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass # Nothing to do on exit for this simple limiter