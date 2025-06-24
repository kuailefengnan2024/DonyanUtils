# d:\DonyanUtils\api\config.py
import os

# --- API Configuration ---
# The environment variable name for the API key
API_KEY_ENV_VAR = "ARK_API_KEY"
# Get API key from environment variable
API_KEY = os.environ.get(API_KEY_ENV_VAR)
# Default base URL for the Ark API
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# --- Model Endpoints ---
# Text Model Endpoints
TEXT_MODEL_ENDPOINT_ID_SEED_1_6 = "ep-20250618135311-j28zf"

# Image Model Endpoints  
IMAGE_MODEL_ENDPOINT_ID_SEED_3_T2I = "ep-20250610170258-wcq9p"

# --- Request Parameters ---
# Default image size
# Available options include:
# "1024x1024" (1:1), "864x1152" (3:4), "1152x864" (4:3),
# "1280x720" (16:9), "720x1280" (9:16), "832x1248" (2:3),
# "1248x832" (3:2), "1512x648" (21:9)
DEFAULT_IMAGE_SIZE = "2048x1200"
# Default response format: "url" or "b64_json"
DEFAULT_RESPONSE_FORMAT = "url"
# Default timeout for API requests in seconds
DEFAULT_TIMEOUT = 60
# Default number of retries for failed requests
DEFAULT_RETRY_COUNT = 3

# --- Default Error Responses ---
# Default error message for text generation failure
DEFAULT_TEXT_ERROR_RESPONSE = "文本生成失败，请稍后重试。"
# Default error response for image generation failure (None, handled by caller)
DEFAULT_IMAGE_ERROR_RESPONSE = None