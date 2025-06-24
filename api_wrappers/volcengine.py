# myutils/api_wrappers/volcengine.py
import os
import time
from volcenginesdkarkruntime import Ark # 假设已安装
# from .base_client import BaseAPIClient # 如果使用BaseAPIClient

# -----------------------------------------------
# Volcengine Ark Text Client (豆包等文本模型)
# -----------------------------------------------
class VolcengineArkTextClient:
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_TIMEOUT = 60 # seconds

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
        Calls the Ark API to get a completion for the given prompt.
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
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed for Ark API call.")
                    # raise  # Or return a default/error message
                    return "Error: API call failed after multiple retries."
        return "Error: API call failed after multiple retries." # Should be unreachable

    def close(self):
        # Ark SDK client might not have an explicit close method,
        # but if it did, it would go here.
        print("VolcengineArkTextClient closed (no explicit close needed for Ark SDK).")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# -----------------------------------------------
# Volcengine Seedream Client (文生图模型)
# -----------------------------------------------
class VolcengineSeedreamClient:
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_RETRY_COUNT = 2
    DEFAULT_TIMEOUT = 120 # seconds for image generation

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
        Generates an image using the Seedream model.
        Returns the image URL or b64_json data.
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
                    raise Exception("API response did not contain image data.")

            except Exception as e:
                print(f"Seedream API call error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    sleep_time = (2 ** attempt)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("All retries failed for Seedream API call.")
                    # raise # Or return a specific error indicator
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