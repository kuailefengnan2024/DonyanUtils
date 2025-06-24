import os
import sys

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.ark_api_utils import ArkApiClient, download_image
from api import config

# --- 准备工作：确保环境变量 ARK_API_KEY 已设置 ---
# export ARK_API_KEY="YOUR_ACTUAL_API_KEY"
if not config.API_KEY:
    print(f"错误：请先设置环境变量 {config.API_KEY_ENV_VAR}")
    # 考虑到可能在非shell环境运行，这里不直接exit(1)，而是打印提示
    # exit(1)

# --- 1. 文本生成示例 ---
print("\n--- 文本生成示例 ---")
# 使用配置文件中预设的文本模型接入点
client_for_text = ArkApiClient(base_url=config.BASE_URL)

with client_for_text: # 使用上下文管理器确保client.close()被调用
    user_prompt = "你好，请介绍一下你自己。"
    # 可以通过 temperature, top_p 等参数控制生成效果
    generated_text = client_for_text.generate_text(
        prompt_text=user_prompt,
        model_endpoint_id=config.TEXT_MODEL_ENDPOINT_ID_SEED_1_6,
        temperature=0.7 
    )
    print(f"用户提示: {user_prompt}")
    print(f"模型回复: {generated_text}")

# --- 2. 图片生成示例 ---
print("\n--- 图片生成示例 ---")
# 图片生成通常需要指定 base_url
client_for_image = ArkApiClient(base_url=config.BASE_URL)

# 使用配置文件中的默认图片模型ID
image_model_id = config.DEFAULT_IMAGE_MODEL_ID

with client_for_image:
    image_prompt = "一只可爱的猫咪，戴着宇航员头盔，漂浮在太空中，背景是星云，动漫风格"
    image_data = client_for_image.generate_image(
        prompt_text=image_prompt,
        model_id=image_model_id,
        size="1024x1024",       # 例如 "1024x1024", "864x1152" 等
        response_format="url",  # 获取图片URL
        guidance_scale=3.5,
    )

    if image_data and image_data.url:
        print(f"图片提示: {image_prompt}")
        print(f"图片URL: {image_data.url}")
        
        # 下载图片
        # 创建一个示例输出目录
        output_dir = "ark_api_output_images"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 从提示生成一个安全的文件名
        safe_filename_base = "".join(c if c.isalnum() else "_" for c in image_prompt[:30])
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