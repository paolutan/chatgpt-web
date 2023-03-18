import os
import openai
import dotenv
import json
import uuid
import time
from application.store import mongo_utils

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

dotenv.load_dotenv("../openai.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")

error_code_message = {
    400: '[OpenAI] 模型的最大上下文长度是4096个令牌，请减少信息的长度。| This model\'s maximum context length is 4096 tokens.',
    401: '[OpenAI] 提供错误的API密钥 | Incorrect API key provided',
    403: '[OpenAI] 服务器拒绝访问，请稍后再试 | Server refused to access, please try again later',
    429: '[OpenAI] 服务器限流，请稍后再试 | Server was limited, please try again later',
    502: '[OpenAI] 错误的网关 | Bad Gateway',
    503: '[OpenAI] 服务器繁忙，请稍后再试 | Server is busy, please try again later',
    504: '[OpenAI] 网关超时 | Gateway Time-out',
    500: '[OpenAI] 服务器繁忙，请稍后再试 | Internal Server Error',
}

if not os.getenv("OPENAI_API_KEY", None):
    raise ValueError('Missing OPENAI_API_KEY environment variable')

if not os.getenv("OPENAI_MODEL_NAME", None):
    raise ValueError('Missing OPENAI_MODEL_NAME environment variable')


def model_config():
    socks_proxy = "-"
    if os.getenv("SOCKS_PROXY_HOST", None) and os.getenv("SOCKS_PROXY_PORT", None):
        socks_proxy = f"{os.getenv('SOCKS_PROXY_HOST')}:{os.getenv('SOCKS_PROXY_PORT')}"

    api_model = "ChatGPTAPI" if os.getenv("OPENAI_API_KEY", None) else "ChatGPTUnofficialProxyAPI"
    config = {
        "apiModel": api_model,
        "reverseProxy": os.getenv("API_REVERSE_PROXY", None),
        "timeoutMs": int(os.getenv("TIMEOUT_MS", 30 * 1000)),
        "socksProxy": socks_proxy
    }
    return config


def add_prompt(prompts: list, role: str, content: str):
    prompts.append({"role": role, "content": content})


def chat_with_gpt(prompt: str,
                  system_prompt: str = None,
                  parent_message_id: str = "",
                  temperature: float = 1.,
                  need_save_db=False):
    if need_save_db:
        prompt_id = str(uuid.uuid4())
        mongo_utils.insert_chat_history(message_id=prompt_id, role=ROLE_USER, content=prompt, timestamp=time.time())

    messages = list()
    if system_prompt:
        add_prompt(messages, role=ROLE_SYSTEM, content=system_prompt)
    add_prompt(messages, role=ROLE_USER, content=prompt)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    message_id = completion.id
    data = {
        "role": completion.choices[0].message["role"],
        "id": completion.id,
        "parentMessageId": parent_message_id,
        "text": completion.choices[0].message["content"],
        "detail": completion.to_dict()
    }
    if need_save_db:
        mongo_utils.insert_chat_history(message_id=message_id, role=ROLE_ASSISTANT, content=text, timestamp=time.time())
    return json.dumps(data)


def stream_chat_with_gpt(prompt: str,
                         system_prompt: str = None,
                         parent_message_id: str = "",
                         temperature: float = 1.,
                         need_save_db=False):
    if need_save_db:
        prompt_id = str(uuid.uuid4())
        mongo_utils.insert_chat_history(message_id=prompt_id, role=ROLE_USER, content=prompt, timestamp=time.time())

    messages = list()
    if system_prompt:
        add_prompt(messages, role=ROLE_SYSTEM, content=system_prompt)
    add_prompt(messages, role=ROLE_USER, content=prompt)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=messages,
        temperature=temperature,
        stream=True
    )
    text, message_id = "", ""
    for chunk in completion:
        if 'content' in chunk.choices[0].delta:
            print(chunk.choices[0].delta['content'], end="")
            sep = "" if not text else "\n"
            text += chunk.choices[0].delta['content']
            message_id = chunk.id
            data = {
                "role": "assistant",
                "id": chunk.id,
                "parentMessageId": parent_message_id,
                "text": text,
                "delta": chunk.choices[0].delta['content'],
                "detail": chunk.to_dict()
            }
            yield f"{sep}{json.dumps(data)}"
    if need_save_db:
        mongo_utils.insert_chat_history(message_id=message_id, role=ROLE_ASSISTANT, content=text, timestamp=time.time())


if __name__ == "__main__":
    res = chat_with_gpt("""how to show "print logs" while running flask with gunicore""")
    print(res)
