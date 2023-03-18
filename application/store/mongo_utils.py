import os
from pymongo import MongoClient

mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo["chatgpt"]
chat_history_collection = db["chat_history"]


def find_chat_history_by_id(message_id):
    chat = chat_history_collection.find_one({"message_id": message_id})
    print(chat)
    return chat


def insert_chat_history(message_id: str, role: str, content: str, timestamp: float):
    res = chat_history_collection.insert_one(
        {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": timestamp
        }
    )
    return res
