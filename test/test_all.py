import sys
import os
import time
import random

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batch.config import BatchConfig
from batch.batch_processor import parallel_batch_processor, simple_parallel_map
from api.ark_api_utils import ArkApiClient, download_image
from api import config as api_config

def run_batch_processor_tests():
    """运行批量处理器相关的测试"""
    print("\n" + "="*25 + " 🧪 Batch Processor Tests " + "="*25)
    
    # 示例1: 模拟API调用
    def mock_api_call(task_id):
        time.sleep(random.uniform(0.1, 0.5))  # 模拟网络延迟
        # 模拟10%的失败率
        if random.random() < 0.1:
            raise Exception(f"API调用失败 - 任务{task_id}")
        return f"任务{task_id}完成，结果: {task_id * 100}"
    
    print("\n--- 测试示例1: 模拟API批量调用 ---")
    tasks = list(range(1, 21))  # 20个任务
    config = BatchConfig(
        max_workers=5,
        rate_limit_per_minute=300,
        max_retries=3
    )
    
    result = parallel_batch_processor(tasks, mock_api_call, config)
    print(f"成功结果数量: {len(result['successful_results'])}")
    print(f"失败任务数量: {len(result['failed_tasks'])}")
    
    print("\n--- 测试示例2: 简单并行计算 ---")
    def square_number(n):
        return n ** 2
    
    numbers = list(range(10))
    squared_results = simple_parallel_map(numbers, square_number, max_workers=4)
    print(f"原始数字: {numbers}")
    print(f"平方结果: {squared_results}")

def run_ark_api_tests():
    """运行Ark API相关的测试"""
    print("\n" + "="*25 + " 🧪 Ark API Tests " + "="*25)

    # --- 准备工作：确保环境变量 ARK_API_KEY 已设置 ---
    if not api_config.API_KEY:
        print(f"警告：环境变量 {api_config.API_KEY_ENV_VAR} 未设置，将跳过API测试。")
        return

    # --- 1. 文本生成示例 ---
    print("\n--- 文本生成示例 ---")
    client_for_text = ArkApiClient(base_url=api_config.BASE_URL)
    with client_for_text:
        user_prompt = "你好，请介绍一下你自己。"
        generated_text = client_for_text.generate_text(
            prompt_text=user_prompt,
            model_endpoint_id=api_config.TEXT_MODEL_ENDPOINT_ID_SEED_1_6,
            temperature=0.7 
        )
        print(f"用户提示: {user_prompt}")
        print(f"模型回复: {generated_text}")

    # --- 2. 图片生成示例 ---
    print("\n--- 图片生成示例 ---")
    client_for_image = ArkApiClient(base_url=api_config.BASE_URL)
    image_model_id = api_config.DEFAULT_IMAGE_MODEL_ID
    with client_for_image:
        image_prompt = "一只可爱的猫咪，戴着宇航员头盔，漂浮在太空中，背景是星云，动漫风格"
        image_data = client_for_image.generate_image(
            prompt_text=image_prompt,
            model_id=image_model_id,
            size="1024x1024",
            response_format="url",
            guidance_scale=3.5,
        )

        if image_data and image_data.url:
            print(f"图片提示: {image_prompt}")
            print(f"图片URL: {image_data.url}")
            
            output_dir = "ark_api_output_images"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            safe_filename_base = "".join(c for c in image_prompt[:30] if c.isalnum() or c in " _-").rstrip()
            image_filepath = os.path.join(output_dir, f"{safe_filename_base}.jpg")
            
            if download_image(image_data.url, image_filepath):
                print(f"图片已下载到: {image_filepath}")
            else:
                print(f"图片下载失败。")
        elif image_data and image_data.b64_json:
            print(f"图片提示: {image_prompt}")
            print("图片以b64_json格式返回，内容过长，不在此处显示。")
        else:
            print("图片生成失败。")


if __name__ == "__main__":
    run_batch_processor_tests()
    run_ark_api_tests() 