# myutils/api_wrappers/base_client.py
import time
import requests # 假设使用requests库

class BaseAPIClient:
    """
    一个非常基础的API客户端基类，可以包含通用逻辑。
    """
    def __init__(self, api_key=None, base_url=None, timeout=30, max_retries=3, retry_delay=1):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay # seconds
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update(self._get_auth_headers())

    def _get_auth_headers(self):
        """子类应实现此方法以提供认证头部"""
        raise NotImplementedError

    def _request(self, method, endpoint, params=None, data=None, json=None, headers=None):
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        merged_headers = self.session.headers.copy()
        if headers:
            merged_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method, url,
                    params=params, data=data, json=json,
                    headers=merged_headers, timeout=self.timeout
                )
                response.raise_for_status()  # 如果状态码是4xx或5xx，则抛出HTTPError
                return response.json() # 假设API总是返回JSON
            except requests.exceptions.RequestException as e:
                print(f"API request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt)) # Exponential backoff
                else:
                    raise  # Re-raise the last exception if all retries fail
        return None # Should not be reached if an exception is raised

    def get(self, endpoint, params=None, headers=None):
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(self, endpoint, data=None, json=None, params=None, headers=None):
        return self._request("POST", endpoint, params=params, data=data, json=json, headers=headers)

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()