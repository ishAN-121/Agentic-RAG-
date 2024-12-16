from pymongo import MongoClient
import pathway as pw
from pathway.xpacks.llm.splitters import TokenCountSplitter
from typing import List, Dict
import uuid
from bson import Binary
import base64


def binary_to_str(binary_id):
    return base64.b64encode(binary_id).decode("utf-8")


def generate_uuid():
    id = uuid.uuid4()
    return Binary(id.bytes, subtype=4)


def linking(chunks: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    client = MongoClient("mongodb://localhost:27017")
    db = client["interiit"]
    db = db["chunks"]
    prev_id = None
    next_id = generate_uuid()
    curr_id = generate_uuid()
    for i in range(0, len(chunks) - 1):
        doc = {
            "_id": curr_id,
            "chunk": chunks[i],
            "prev_id": prev_id,
            "next_id": next_id,
        }
        prev_id = curr_id
        curr_id = next_id
        next_id = generate_uuid()
        chunks[i][1]["id"] = binary_to_str(curr_id)
        db.insert_one(doc)

    k = len(chunks) - 1
    doc = {"_id": curr_id, "chunk": chunks[k], "prev_id": prev_id, "next_id": None}
    chunks[k][1]["id"] = binary_to_str(curr_id)
    db.insert_one(doc)
    client.close()
    return chunks
