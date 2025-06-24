# ark_api_utils.py

import os
import time
import requests
import threading
import logging
from pathlib import Path
from datetime import datetime
from volcenginesdkarkruntime import Ark

from . import config

# 配置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    API请求速率限制器。
    用于控制在特定时间窗口内API的调用次数，以避免超出服务商的速率限制。
    """
    def __init__(self, max_requests: int, window_seconds: int):
        """
        初始化速率限制器。

        参数:
            max_requests (int): 时间窗口内允许的最大请求数。
            window_seconds (int): 时间窗口的长度（秒）。
        """
        if max_requests <= 0:
            raise ValueError("max_requests 必须大于 0")
        if window_seconds <= 0:
            raise ValueError("window_seconds 必须大于 0")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_times = []  # 存储每个请求的时间戳
        self.lock = threading.Lock() # 线程锁，保证多线程环境下的安全
        self.total_api_calls = 0 # 记录总的API调用次数（通过本限制器的）

        logger.info(f"速率限制器已初始化：每 {window_seconds} 秒最多 {max_requests} 次请求。")

    def wait_if_needed(self):
        """
        如果需要，则等待，以确保不超过速率限制。
        在每次API调用前调用此方法。
        """
        with self.lock:
            current_time = time.time()

            # 清理超出时间窗口的旧请求记录
            self.requests_times = [t for t in self.requests_times if current_time - t < self.window_seconds]

            # 如果当前窗口内的请求数已达到限制
            if len(self.requests_times) >= self.max_requests:
                oldest_request_time = self.requests_times[0] # 最早的请求时间
                wait_time = (oldest_request_time + self.window_seconds) - current_time + 0.01 # 额外0.01秒缓冲
                
                if wait_time > 0:
                    logger.warning(f"触发速率限制：当前窗口已有 {len(self.requests_times)} 次请求。等待 {wait_time:.2f} 秒...")
                    time.sleep(wait_time)
                    # 等待后重新检查并清理
                    current_time = time.time()
                    self.requests_times = [t for t in self.requests_times if current_time - t < self.window_seconds]


            # 记录当前请求的时间戳
            self.requests_times.append(time.time())
            self.total_api_calls += 1
            # logger.debug(f"速率限制器：当前窗口请求数 {len(self.requests_times)}/{self.max_requests}")


class ArkApiClient:
    """
    火山方舟（Ark）API客户端封装。
    提供了文本生成和图片生成等常用功能，并内置重试逻辑。
    """
    def __init__(self,
                 api_key: str = None,
                 base_url: str = None,
                 timeout: int = config.DEFAULT_TIMEOUT):
        """
        初始化Ark API客户端。

        参数:
            api_key (str, optional): API密钥。如果为None，则尝试从环境变量 ARK_API_KEY 读取。
            base_url (str, optional): API的基础URL。如果为None，则使用SDK的默认或特定于服务的URL。
                                     对于图片生成，通常需要指定如 config.BASE_URL。
            timeout (int, optional): API请求的超时时间（秒）。默认为 config.DEFAULT_TIMEOUT。
        """
        if api_key is None:
            api_key = config.API_KEY
        if not api_key:
            raise ValueError(f"API密钥未提供，且未在环境变量 {config.API_KEY_ENV_VAR} 中找到。")

        self.api_key = api_key
        self.base_url = base_url # Ark SDK的某些服务（如图片）可能需要显式设置base_url
        self.timeout = timeout
        
        # 根据是否有base_url来初始化client
        if self.base_url:
            self.client = Ark(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
            logger.info(f"ArkApiClient 已初始化，使用 Base URL: {self.base_url}, Timeout: {self.timeout}s")
        else:
            self.client = Ark(api_key=self.api_key, timeout=self.timeout)
            logger.info(f"ArkApiClient 已初始化 (无特定 Base URL), Timeout: {self.timeout}s")


    def _execute_request(self, 
                         api_call_func, 
                         params: dict, 
                         retry_count: int, 
                         rate_limiter: RateLimiter = None,
                         request_type: str = "请求"):
        """
        私有辅助方法，用于执行API请求并处理重试。

        参数:
            api_call_func (callable): 要调用的具体API方法 (例如 self.client.chat.completions.create)。
            params (dict): 传递给API方法的参数。
            retry_count (int): 最大重试次数。
            rate_limiter (RateLimiter, optional): 速率限制器实例。
            request_type (str, optional): 请求类型描述，用于日志。

        返回:
            API调用的成功响应，或在所有重试失败后返回None。
        """
        last_exception = None
        for attempt in range(retry_count):
            try:
                if rate_limiter:
                    rate_limiter.wait_if_needed()

                logger.debug(f"尝试第 {attempt + 1}/{retry_count} 次发起 {request_type}...")
                response = api_call_func(**params)
                logger.info(f"{request_type} 成功 (尝试 {attempt + 1})。")
                
                # 特别为文本生成打印模型信息
                if request_type == "文本生成" and hasattr(response, 'model'):
                    logger.info(f"  预期模型: {params.get('model')}, 实际模型: {response.model}")
                    if params.get('model') != response.model and not str(response.model).startswith(str(params.get('model'))): # 有些模型返回的是接入点ID+模型ID
                         logger.warning(f"  注意：实际模型与预期接入点不符！接入点: {params.get('model')}, API返回模型: {response.model}")
                return response
            except Exception as e:
                last_exception = e
                logger.error(f"{request_type} 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"所有 {retry_count} 次 {request_type} 尝试均失败。")
        
        # 如果所有重试都失败了，将最后一次异常信息记录下来
        if last_exception:
            logger.error(f"最终 {request_type} 错误: {last_exception}")
        return None

    def generate_text(self,
                      prompt_text: str,
                      model_endpoint_id: str,
                      system_prompt: str = "You are a helpful assistant.",
                      retry_count: int = config.DEFAULT_RETRY_COUNT,
                      rate_limiter: RateLimiter = None,
                      **kwargs) -> str:
        """
        使用指定的模型端点生成文本。

        参数:
            prompt_text (str): 用户的输入提示。
            model_endpoint_id (str): 使用的模型端点ID (例如 "ep-xxx")。
            system_prompt (str, optional): 系统提示。默认为 "You are a helpful assistant."。
            retry_count (int, optional): 失败时的重试次数。默认为 DEFAULT_RETRY_COUNT。
            rate_limiter (RateLimiter, optional): 速率限制器实例。
            **kwargs: 其他传递给 `client.chat.completions.create` 的参数。

        返回:
            str: 生成的文本内容，或在失败时返回 DEFAULT_TEXT_ERROR_RESPONSE。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ]
        params = {
            "model": model_endpoint_id,
            "messages": messages,
            **kwargs
        }

        logger.info(f"准备生成文本，模型: {model_endpoint_id}, 用户提示长度: {len(prompt_text)}")
        completion = self._execute_request(
            self.client.chat.completions.create,
            params,
            retry_count,
            rate_limiter,
            request_type="文本生成"
        )

        if completion and completion.choices:
            return completion.choices[0].message.content.strip()
        else:
            logger.warning(f"文本生成未能获取有效回复，模型: {model_endpoint_id}。")
            return config.DEFAULT_TEXT_ERROR_RESPONSE

    def generate_image(self,
                       prompt_text: str,
                       model_endpoint_id: str,
                       size: str = config.DEFAULT_IMAGE_SIZE,
                       response_format: str = config.DEFAULT_RESPONSE_FORMAT,  # "url" 或 "b64_json"
                       guidance_scale: float = 3.0,
                       add_watermark: bool = False,
                       seed: int = -1,  # -1 表示随机
                       retry_count: int = config.DEFAULT_RETRY_COUNT, # 图片生成通常重试次数少一些
                       rate_limiter: RateLimiter = None,
                       **kwargs) -> dict: # 返回原始API数据项或None
        """
        使用指定的模型端点生成图片。

        参数:
            prompt_text (str): 生成图片的文本提示。
            model_endpoint_id (str): 使用的图片模型端点ID (例如 "ep-xxx")。
            size (str, optional): 图片尺寸，默认为 "1024x1024"。
            response_format (str, optional): 返回格式 ("url" 或 "b64_json")。默认为 "url"。
            guidance_scale (float, optional): 引导强度 (1-10)。默认为 3.0。
            add_watermark (bool, optional): 是否添加水印。默认为 False。
            seed (int, optional): 随机种子，-1表示自动。默认为 -1。
            retry_count (int, optional): 失败时的重试次数。默认为 2。
            rate_limiter (RateLimiter, optional): 速率限制器实例。
            **kwargs: 其他传递给 `client.images.generate` 的参数。

        返回:
            dict: 包含图片信息（如URL或b64_json数据）的字典对象 (通常是 response.data[0])，
                  或在失败时返回 DEFAULT_IMAGE_ERROR_RESPONSE (None)。
        """
        if not self.base_url:
            logger.warning("图片生成API通常需要设置 base_url (如 'https://ark.cn-beijing.volces.com/api/v3')，当前未设置。")

        params = {
            "model": model_endpoint_id,
            "prompt": prompt_text,
            "response_format": response_format,
            "size": size,
            "guidance_scale": guidance_scale,
            "watermark": add_watermark,
            **kwargs
        }
        if seed != -1:
            params["seed"] = seed
        
        logger.info(f"准备生成图片，模型端点: {model_endpoint_id}, 尺寸: {size}, 提示长度: {len(prompt_text)}")
        response = self._execute_request(
            self.client.images.generate,
            params,
            retry_count,
            rate_limiter,
            request_type="图片生成"
        )

        if response and response.data:
            return response.data[0] # 返回第一个图片数据对象
        else:
            logger.warning(f"图片生成未能获取有效数据，模型端点: {model_endpoint_id}。")
            return config.DEFAULT_IMAGE_ERROR_RESPONSE

    def close(self):
        """
        关闭Ark客户端并释放资源。
        """
        if self.client:
            try:
                self.client.close()
                logger.info("ArkApiClient 已关闭。")
            except Exception as e:
                logger.error(f"关闭 ArkApiClient 时发生错误: {e}")
        self.client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def ensure_dir_exists(dir_path):
    """确保目录存在，如有必要则创建它。"""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

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

def download_image(url: str, filepath: str, timeout: int = 30) -> bool:
    """
    从给定的URL下载图片并保存到指定路径。

    参数:
        url (str): 图片的URL。
        filepath (str): 图片保存的完整路径（包括文件名和扩展名）。
        timeout (int, optional): 下载请求的超时时间（秒）。默认为 30。

    返回:
        bool: 如果下载并保存成功则返回True，否则返回False。
    """
    try:
        logger.info(f"开始下载图片从 {url} 到 {filepath}...")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()  # 如果HTTP请求返回了错误状态码，则抛出HTTPError异常

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): # 8KB per chunk
                f.write(chunk)
        
        logger.info(f"图片成功下载并保存到: {filepath}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"下载图片失败 (URL: {url}): {e}")
        return False
    except IOError as e:
        logger.error(f"保存图片文件失败 (路径: {filepath}): {e}")
        return False
    except Exception as e:
        logger.error(f"下载或保存图片时发生未知错误 (URL: {url}, 路径: {filepath}): {e}")
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

# --- 使用示例 ---
if __name__ == "__main__":
    # --- 准备工作：确保环境变量 ARK_API_KEY 已设置 ---
    # export ARK_API_KEY="YOUR_ACTUAL_API_KEY"
    if not config.API_KEY:
        print(f"错误：请先设置环境变量 {config.API_KEY_ENV_VAR}")
        exit(1)
    
    # --- 1. 文本生成示例 ---
    print("\n--- 文本生成示例 ---")
    # 不带 base_url 的客户端，适用于大部分文本模型接入点
    # 使用 config.py 中新定义的 Seed 1.6 模型接入点
    text_model_endpoint = config.TEXT_MODEL_ENDPOINT_ID_SEED_1_6
    
    # 如果你的接入点ID是全局唯一的，例如平台提供的标准模型ID，可以不指定base_url
    # client_for_text = ArkApiClient()

    # 如果你的接入点是区域性的，或者SDK行为不确定，指定base_url更保险
    # 对于某些文本模型接入点，可能也需要 base_url，请根据实际情况调整
    client_for_text = ArkApiClient(base_url=config.BASE_URL) # 豆包通用大模型通常用这个

    with client_for_text: # 使用上下文管理器确保client.close()被调用
        user_prompt = "你好，请介绍一下你自己。"
        # 可以通过 temperature, top_p 等参数控制生成效果
        generated_text = client_for_text.generate_text(
            prompt_text=user_prompt,
            model_endpoint_id=text_model_endpoint,
            temperature=0.7 
        )
        print(f"用户提示: {user_prompt}")
        print(f"模型回复: {generated_text}")

    # --- 2. 图片生成示例 ---
    print("\n--- 图片生成示例 ---")
    # 图片生成通常需要指定 base_url
    client_for_image = ArkApiClient(base_url=config.BASE_URL)
    
    # 使用配置的图片模型端点ID
    image_model_endpoint_id = config.IMAGE_MODEL_ENDPOINT_ID_SEED_3_T2I
    
    # 可选：创建速率限制器实例 (例如，每分钟最多10次请求)
    # rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
    rate_limiter = None # 此处禁用速率限制器以简化示例

    with client_for_image:
        image_prompt = "一只可爱的猫咪，戴着宇航员头盔，漂浮在太空中，背景是星云，动漫风格"
        image_data = client_for_image.generate_image(
            prompt_text=image_prompt,
            model_endpoint_id=image_model_endpoint_id,
            size="1024x1024",       # 例如 "1024x1024", "864x1152" 等
            response_format="url",  # 获取图片URL
            guidance_scale=3.5,
            rate_limiter=rate_limiter # 传递速率限制器
        )

        if image_data and image_data.url:
            print(f"图片提示: {image_prompt}")
            print(f"图片URL: {image_data.url}")
            
            # 下载图片
            output_dir = "ark_api_output_images"
            ensure_dir_exists(output_dir)
            
            # 从提示生成一个安全的文件名
            safe_filename_base = "".join(c if c.isalnum() else "_" for c in image_prompt[:30])
            image_filepath = os.path.join(output_dir, f"{safe_filename_base}.jpg")
            
            if download_image(image_data.url, image_filepath):
                print(f"图片已下载到: {image_filepath}")
            else:
                print(f"图片下载失败。")
        elif image_data and image_data.b64_json:
            # 如果 response_format 是 "b64_json"，可以在这里处理
            pass
        else:
            print(f"图片生成失败。")

    print("\n--- 示例运行完毕 ---")