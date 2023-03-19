import os
import openai
import dotenv
import json
import uuid
import time
from datetime import datetime
import tiktoken
from application.store import mongo_utils

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
FORGET_ABOVE_FLAG = "[FA]"

dotenv.load_dotenv("../openai.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
MAX_CONTEXT_NUM = int(os.getenv("MAX_CONTEXT_NUM", 100))
MAX_MODEL_TOKENS = 4000
MAX_RESPONSE_TOKENS = 1000
MAX_NUM_TOKENS = MAX_MODEL_TOKENS - MAX_RESPONSE_TOKENS  # 3000


def estimate_token_size(text, model_name=OPENAI_MODEL_NAME):
    tokenizer = tiktoken.get_encoding("cl100k_base" if model_name == "gpt-3.5-turbo-0301" else "p50k_base")
    tokens = tokenizer.encode(text)
    return len(tokens)


def default_system_prompt():
    system_prompt = (
        "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible.\n"
        "Knowledge cutoff: 2021-09-01\n"
        "Current date: {current_date}\n".format(current_date=datetime.now().strftime("%Y-%m-%d"))
    )
    return system_prompt


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


def construct_chat_context(prompt: str, parent_message_id: str = "", system_prompt: str = ""):
    chat_context = list()
    system_prompt = system_prompt if system_prompt else default_system_prompt()
    total_tokens_num = estimate_token_size(system_prompt) + estimate_token_size(prompt) + 8

    if not prompt.startswith(FORGET_ABOVE_FLAG):
        for i in range(MAX_CONTEXT_NUM):
            if parent_message_id:
                parent_message = mongo_utils.find_chat_history_by_message_id(parent_message_id)
                if parent_message:
                    parent_message_id = parent_message.get("parent_message_id", "")
                    parent_role = parent_message.get("role", ROLE_USER)
                    parent_content = parent_message.get("content", "")
                    if parent_content and parent_content.startswith(FORGET_ABOVE_FLAG):
                        break
                    total_tokens_num += estimate_token_size(parent_content) + 4
                    if total_tokens_num > MAX_NUM_TOKENS:
                        break
                    add_prompt(chat_context, parent_role, parent_content)
                else:
                    print(f"Can not find message: {parent_message_id}")
                    break

    add_prompt(chat_context, ROLE_SYSTEM, system_prompt)
    chat_context.reverse()
    add_prompt(chat_context, ROLE_USER, prompt)

    return chat_context


def save_chat_history(prompt, parent_message_id, system_prompt, response_message_id, response_text, model):
    prompt_id = str(uuid.uuid4())
    mongo_utils.insert_chat_history(
        message_id=prompt_id,
        role=ROLE_USER,
        content=prompt,
        parent_message_id=parent_message_id,
        timestamp=time.time(),
        system_prompt=system_prompt,
        max_context_num=MAX_CONTEXT_NUM
    )
    mongo_utils.insert_chat_history(
        message_id=response_message_id,
        role=ROLE_ASSISTANT,
        content=response_text,
        parent_message_id=prompt_id,
        timestamp=time.time(),
        model=model
    )


def chat_with_openai(prompt: str,
                     system_prompt: str = None,
                     parent_message_id: str = "",
                     temperature: float = 1.,
                     need_save_db=False,
                     stream=False):
    chat_context = construct_chat_context(prompt, parent_message_id, system_prompt)
    model, response_text, response_message_id = "", "", uuid.uuid4()
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=chat_context,
        temperature=temperature,
        stream=stream
    )
    if stream:
        for chunk in completion:
            if 'content' in chunk.choices[0].delta:
                sep = "" if not response_text else "\n"
                if chunk.id:
                    response_message_id = chunk.id
                model = chunk.model
                response_text += chunk.choices[0].delta['content']
                data = {
                    "role": "assistant",
                    "id": chunk.id,
                    "parentMessageId": parent_message_id,
                    "text": response_text,
                    "delta": chunk.choices[0].delta['content'],
                    "detail": chunk.to_dict()
                }
                yield f"{sep}{json.dumps(data)}"
        if need_save_db:
            save_chat_history(prompt, parent_message_id, system_prompt, response_message_id, response_text, model)
    else:
        if completion.id:
            response_message_id = completion.id
        model = completion.model
        response_text = completion.choices[0].message["content"]
        data = {
            "role": completion.choices[0].message["role"],
            "id": completion.id,
            "parentMessageId": parent_message_id,
            "text": response_text,
            "detail": completion.to_dict()
        }
        if need_save_db:
            save_chat_history(prompt, parent_message_id, system_prompt, response_message_id, response_text, model)
        return json.dumps(data)


if __name__ == "__main__":
    # res = chat_with_openai("""how to show "print logs" while running flask with gunicore""")
    # print(res)
    print(default_system_prompt())
