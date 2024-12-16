import os
from common.llm import call_llm
from PyPDF2 import PdfReader
import tiktoken
from pydantic import BaseModel
from typing import Optional
import json
from flags_agent.contracts import contract_checklist
import uvicorn
import pymongo
from fastapi import FastAPI, File, UploadFile, WebSocket
import asyncio
import uuid
import io
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
check_event = asyncio.Event()
uri = os.getenv("MONGO_CONNECTION_STRING")
client = pymongo.MongoClient(uri)
db = client["sirius"]
db = db["FlagAgent"]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Eval(BaseModel):
    item: str
    is_met: int
    explaination: str
    reference: Optional[str]


class Evals(BaseModel):
    evals: list[Eval]
    checklist_relevance: float


def transform_to_prisma_schema(id, evals):

    for category, evals in evals.items():
        result = {
            "group_id": id,
            "category": category,
            "checklistRelevance": evals.checklist_relevance,
            "evaluations": [],
        }

        # Create the Evaluation entries
        for eval_item in evals.evals:
            evaluation = {
                "id": str(uuid.uuid4()),
                "resultId": id,
                "item": eval_item.item,
                "isMet": eval_item.is_met,
                "explanation": eval_item.explaination,
                "reference": eval_item.reference,
            }
            result["evaluations"].append(evaluation)
        db.update_one({"flagID": id}, {"$set": result}, upsert=True)


async def extract_pdf_text(content: bytes) -> str:
    try:
        # reader = PyPDF2.PdfFileReader
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


async def evaluate(text: str, id: str) -> Evals:
    global check_event
    lines = text.splitlines()
    numbered_contract = "\n".join([f"{i+1}. {line}" for i, line in enumerate(lines)])
    evaluations = {}
    for title, checklist in contract_checklist.items():
        prompt = f"""
        Check the legal contract to ensure that the following checklist is met:
        {checklist}

        The legal contract:
        {numbered_contract}

        Also find out the relevance of checklist which checks for correctness in {title}.

        Evaluation of a checklist item must follow this pydantic model:
        class Eval(BaseModel):
            item: str
            is_met: int | [0, 5] with 0 being not met and 5 being met
            explaination: str
            reference : Optional[str] | Lines (start)-(end) provide the reference of line numbers is is_met is less than 4.

        The output should be json dump of:
        class Evals(BaseModel):
            evals: list[Eval]
            checklist_relevance: float | between 0 to 1 with 1 being relevant

        Do not output any additional text.
        """
        output = call_llm(prompt)
        try:
            evals = Evals(**json.loads(output[7:-3]))
            evaluations[title] = evals
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    transform_to_prisma_schema(id, evaluations)
    check_event.set()


@app.post("/submit")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    id = str(uuid.uuid4())
    text = await extract_pdf_text(content)
    print(text)
    db.update_one({"flagID": id}, {"$set": {"file": text}}, upsert=True)
    asyncio.create_task(evaluate(text, id))

    return {
        "message": "Files uploaded successfully, agreement generation in progress.",
        "conversation_id": id,
    }


@app.websocket("/ws/check")
async def check(ws: WebSocket):
    await ws.accept()
    global check_event
    while True:
        await check_event.wait()
        await ws.send_json({"result": "OK"})
        check_event.clear()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8230)
