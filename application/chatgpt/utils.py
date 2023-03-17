import os
import openai
import dotenv
import json

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

dotenv.load_dotenv("../.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL_NAME = "gpt-3.5-turbo-0301"


def add_prompt(prompts: list, role: str, content: str):
    prompts.append({"role": role, "content": content})


def chat_with_gpt(prompt: str,
                  system_prompt: str = None,
                  parent_message_id: str = "",
                  temperature: float = 1.):
    messages = list()
    if system_prompt:
        add_prompt(messages, role=ROLE_SYSTEM, content=system_prompt)
    add_prompt(messages, role=ROLE_USER, content=prompt)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    data = {
        "role": completion.choices[0].message["role"],
        "id": completion.id,
        "parentMessageId": parent_message_id,
        "text": completion.choices[0].message["content"],
        "detail": completion.to_dict()
    }
    return json.dumps(data)


def stream_chat_with_gpt(prompt: str,
                         system_prompt: str = None,
                         parent_message_id: str = "",
                         temperature: float = 1.):
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
    text = ""
    for chunk in completion:
        if 'content' in chunk.choices[0].delta:
            print(chunk.choices[0].delta['content'], end="")
            sep = "" if not text else "\n"
            text += chunk.choices[0].delta['content']
            data = {
                "role": "assistant",
                "id": chunk.id,
                "parentMessageId": parent_message_id,
                "text": text,
                "delta": chunk.choices[0].delta['content'],
                "detail": chunk.to_dict()
            }
            yield f"{sep}{json.dumps(data)}"


if __name__ == "__main__":
    res = chat_with_gpt("""how to show "print logs" while running flask with gunicore""")
    print(res)
