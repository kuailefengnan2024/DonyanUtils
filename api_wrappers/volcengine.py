# DonyanUtils/api_wrappers/volcengine.py
import os
import time
from volcenginesdkarkruntime import Ark # 假设已安装
# from .base_client import BaseAPIClient # 如果使用BaseAPIClient

# -----------------------------------------------
# 火山引擎Ark文本客户端 (豆包等文本模型)
# -----------------------------------------------
class VolcengineArkTextClient:
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_TIMEOUT = 60 # 秒

    def __init__(self, api_key=None, endpoint_id=None, timeout=None, retry_count=None):
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("ARK_API_KEY not found in environment or provided.")
        self.endpoint_id = endpoint_id
        if not self.endpoint_id:
            raise ValueError("Endpoint ID must be provided for ArkTextClient.")

        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.retry_count = retry_count if retry_count is not None else self.DEFAULT_RETRY_COUNT

        self.client = Ark(api_key=self.api_key, timeout=self.timeout)
        print(f"VolcengineArkTextClient initialized for endpoint: {self.endpoint_id}")

    def generate(self, prompt_text, system_prompt="You are a helpful assistant."):
        """
        调用Ark API获取给定提示的完成结果。
        """
        for attempt in range(self.retry_count):
            try:
                print(f"Calling Ark API (attempt {attempt + 1}/{self.retry_count})...")
                completion = self.client.chat.completions.create(
                    model=self.endpoint_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_text}
                    ]
                )
                print(f"Ark API call successful. Model used: {completion.model}")
                return completion.choices[0].message.content
            except Exception as e:
                print(f"Ark API call error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    sleep_time = (2 ** attempt)
                    print(f"将在 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                else:
                    print("Ark API调用的所有重试均失败。")
                    # raise  # 或返回默认/错误消息
                    return "错误：API调用在多次重试后失败。"
        return "错误：API调用在多次重试后失败。" # 理论上不应该到达这里

    def close(self):
        # Ark SDK客户端可能没有显式的关闭方法，
        # 但如果有的话，会在这里调用。
        print("VolcengineArkTextClient已关闭（Ark SDK不需要显式关闭）。")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# -----------------------------------------------
# 火山引擎Seedream客户端 (文生图模型)
# -----------------------------------------------
class VolcengineSeedreamClient:
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_RETRY_COUNT = 2
    DEFAULT_TIMEOUT = 120 # 图像生成的超时时间（秒）

    def __init__(self, api_key=None, model_id=None, base_url=None, timeout=None, retry_count=None):
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("ARK_API_KEY not found in environment or provided.")
        self.model_id = model_id
        if not self.model_id:
            raise ValueError("Model ID must be provided for SeedreamClient.")

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.retry_count = retry_count if retry_count is not None else self.DEFAULT_RETRY_COUNT

        self.client = Ark(base_url=self.base_url, api_key=self.api_key, timeout=self.timeout)
        print(f"VolcengineSeedreamClient initialized for model: {self.model_id}")

    def generate_image(self, prompt, size="1024x1024", response_format="url", guidance_scale=3.0, seed=-1, add_watermark=False):
        """
        使用Seedream模型生成图像。
        返回图像URL或b64_json数据。
        """
        params = {
            "model": self.model_id,
            "prompt": prompt,
            "size": size,
            "response_format": response_format,
            "guidance_scale": guidance_scale,
            "watermark": add_watermark,
        }
        if seed != -1:
            params["seed"] = seed

        for attempt in range(self.retry_count):
            try:
                print(f"Calling Seedream API (attempt {attempt + 1}/{self.retry_count})...")
                response = self.client.images.generate(**params)

                if response.data and len(response.data) > 0:
                    if response_format == "url":
                        print("Seedream API call successful (URL).")
                        return response.data[0].url
                    elif response_format == "b64_json":
                        print("Seedream API call successful (b64_json).")
                        return response.data[0].b64_json
                else:
                    raise Exception("API响应不包含图像数据。")

            except Exception as e:
                print(f"Seedream API call error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    sleep_time = (2 ** attempt)
                    print(f"将在 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                else:
                    print("Seedream API调用的所有重试均失败。")
                    # raise # 或返回特定的错误指示器
                    return None
        return None

    def close(self):
        try:
            if hasattr(self.client, 'close') and callable(self.client.close):
                self.client.close()
            print("VolcengineSeedreamClient closed.")
        except Exception as e:
            print(f"Error closing SeedreamClient: {e}")


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()