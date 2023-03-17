import os
import dotenv

dotenv.load_dotenv()

error_code_message = {
    400: '[OpenAI] 模型的最大上下文长度是4096个令牌，请减少信息的长度。| This model\'s maximum context length is 4096 tokens.',
    401: '[OpenAI] 提供错误的API密钥 | Incorrect API key provided',
    403: '[OpenAI] 服务器拒绝访问，请稍后再试 | Server refused to access, please try again later',
    429: '[OpenAI] 服务器限流，请稍后再试 | Server was limited, please try again later',
    502: '[OpenAI] 错误的网关 |  Bad Gateway',
    503: '[OpenAI] 服务器繁忙，请稍后再试 | Server is busy, please try again later',
    504: '[OpenAI] 网关超时 | Gateway Time-out',
    500: '[OpenAI] 服务器繁忙，请稍后再试 | Internal Server Error',
}

if (not os.getenv("OPENAI_API_KEY", None)) and (not os.getenv("OPENAI_ACCESS_TOKEN", None)):
    raise ValueError('Missing OPENAI_API_KEY or OPENAI_ACCESS_TOKEN environment variable')

# let api: ChatGPTAPI | ChatGPTUnofficialProxyAPI

if os.getenv("OPENAI_API_KEY", None):
    options = {"apiKey": os.getenv("OPENAI_API_KEY"), "completionParams": {"model": "gpt-3.5-turbo"}, "debug": False}

    if os.getenv("OPENAI_API_BASE_URL", None) and len(os.getenv("OPENAI_API_BASE_URL").strip()) > 0:
        options["apiBaseUrl"] = os.getenv("OPENAI_API_BASE_URL")

    # TODO: handle process.env.SOCKS_PROXY_HOST && process.env.SOCKS_PROXY_PORT
    api = None
    apiModel = 'ChatGPTAPI'
else:
    options = {
        "accessToken": os.getenv("OPENAI_ACCESS_TOKEN"),
        "debug": False
    }
    # TODO: handle process.env.SOCKS_PROXY_HOST && process.env.SOCKS_PROXY_PORT
    if os.getenv("API_REVERSE_PROXY", None):
        options["apiReverseProxyUrl"] = os.getenv("API_REVERSE_PROXY")

    apiModel = 'ChatGPTUnofficialProxyAPI'


def model_config():
    socks_proxy = "-"
    if os.getenv("SOCKS_PROXY_HOST", None) and os.getenv("SOCKS_PROXY_PORT", None):
        socks_proxy = f"{os.getenv('SOCKS_PROXY_HOST')}:{os.getenv('SOCKS_PROXY_PORT')}"

    config = {
        "apiModel": apiModel,
        "reverseProxy": os.getenv("API_REVERSE_PROXY", None),
        "timeoutMs": int(os.getenv("TIMEOUT_MS", 30 * 1000)),
        "socksProxy": socks_proxy
    }
    return config
