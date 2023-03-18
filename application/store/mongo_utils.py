import os
from pymongo import MongoClient

mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo["chatgpt"]
chat_history_collection = db["chat_history"]

chat_history_collection.create_index("message_id")
chat_history_collection.create_index("parent_message_id")


def find_chat_history_by_message_id(message_id):
    chat = chat_history_collection.find_one({"message_id": message_id})
    return chat


def insert_chat_history(message_id: str, role: str, content: str, parent_message_id: str, timestamp: float, **kwargs):
    data = {
        "message_id": message_id,
        "role": role,
        "content": content,
        "parent_message_id": parent_message_id,
        "timestamp": timestamp
    }
    data.update(kwargs)
    res = chat_history_collection.insert_one(data)
    return res
