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
MAX_CONTEXT_NUM = os.getenv("MAX_CONTEXT_NUM", 10)

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
    if (not role) or (not content):
        return
    prompts.append({"role": role, "content": content})


def construct_chat_context(prompt: str, parent_message_id: str = "", max_context_num: int = 0, system_prompt: str = ""):
    chat_context = list()

    for i in range(max_context_num):
        if parent_message_id:
            parent_message = mongo_utils.find_chat_history_by_message_id(parent_message_id)
            if parent_message:
                parent_message_id = parent_message.get("parent_message_id", "")
                add_prompt(chat_context, parent_message.get("role", ""), parent_message.get("content", ""))
            else:
                print(f"Can not find message: {parent_message_id}")
                break

    if system_prompt:
        add_prompt(chat_context, ROLE_SYSTEM, system_prompt)

    chat_context.reverse()
    add_prompt(chat_context, ROLE_USER, prompt)

    return chat_context


def chat_with_gpt(prompt: str,
                  system_prompt: str = None,
                  parent_message_id: str = "",
                  temperature: float = 1.,
                  need_save_db=False):
    prompt_id = str(uuid.uuid4())
    if need_save_db:
        mongo_utils.insert_chat_history(
            message_id=prompt_id,
            role=ROLE_USER,
            content=prompt,
            parent_message_id=parent_message_id,
            timestamp=time.time(),
            system_prompt=system_prompt
        )

    chat_context = construct_chat_context(prompt, parent_message_id, MAX_CONTEXT_NUM, system_prompt)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=chat_context,
        temperature=temperature,
    )
    message_id = completion.id
    model = completion.model
    content = completion.choices[0].message["content"]
    data = {
        "role": completion.choices[0].message["role"],
        "id": completion.id,
        "parentMessageId": parent_message_id,
        "text": content,
        "detail": completion.to_dict()
    }
    if need_save_db:
        mongo_utils.insert_chat_history(
            message_id=message_id,
            role=ROLE_ASSISTANT,
            content=content,
            parent_message_id=prompt_id,
            timestamp=time.time(),
            model=model
        )
    return json.dumps(data)


def stream_chat_with_gpt(prompt: str,
                         system_prompt: str = None,
                         parent_message_id: str = "",
                         temperature: float = 1.,
                         need_save_db=False):
    prompt_id = str(uuid.uuid4())
    if need_save_db:
        mongo_utils.insert_chat_history(
            message_id=prompt_id,
            role=ROLE_USER,
            content=prompt,
            parent_message_id=parent_message_id,
            timestamp=time.time(),
            system_prompt=system_prompt
        )

    chat_context = construct_chat_context(prompt, parent_message_id, MAX_CONTEXT_NUM, system_prompt)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=chat_context,
        temperature=temperature,
        stream=True
    )
    model, text, message_id = "", "", ""
    for chunk in completion:
        if 'content' in chunk.choices[0].delta:
            print(chunk.choices[0].delta['content'], end="")
            sep = "" if not text else "\n"
            text += chunk.choices[0].delta['content']
            message_id = chunk.id
            model = chunk.model
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
        mongo_utils.insert_chat_history(
            message_id=message_id,
            role=ROLE_ASSISTANT,
            content=text,
            parent_message_id=prompt_id,
            timestamp=time.time(),
            model=model
        )


if __name__ == "__main__":
    # res = chat_with_gpt("""how to show "print logs" while running flask with gunicore""")
    # print(res)
    context = construct_chat_context("hello", "chapl-6vK8GUbmm2ZCEyNlY8PQZhrOeOEOo", 2, "you are simpleton")
    print(context)

    context = construct_chat_context("hello", "chatcmpl-6vK8GUbmm2ZCEyNlY8PQZhrOeOEOo", 2, "you are simpleton")
    print(context)
