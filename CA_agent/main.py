import os, uuid
from common.llm import call_llm
from pathway.xpacks.llm.parsers import ParseUnstructured
from CA_agent.multi_retrieval import multi_retrieval_CA_agent
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, WebSocket
import pymongo
import shutil
import uvicorn
import PyPDF2
import json
import re
import asyncio
from swarm.util import debug_print
from fastapi.middleware.cors import CORSMiddleware

check_event = asyncio.Event()
RELEVANT_SECTIONS = [
    ["80C", "80CC", "80CCA", "80CCB", "80CCC", "80CCD", "80CCE"],
    ["80CCF", "80CCG", "80CCH"],
    ["80D", "80DD", "80DDB"],
    ["80E", "80EE", "80EEA", "80EEB"],
    ["80G", "80GG", "80GGA", "80GGB", "80GGC"],
]

SAVE_DIR = "./uploadeddocs"
os.makedirs(SAVE_DIR, exist_ok=True)

uri = os.getenv("MONGO_CONNECTION_STRING")
client = pymongo.MongoClient(uri)
db = client["sirius"]
db = db["CA_agent"]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def parse_pdf(docpath):
    with open(docpath, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        full_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text()  # Extract text from each page
        parser = ParseUnstructured(mode="single")
        parsed = parser.__call__(full_text)
        parsed_ = str(parsed)
        parsed_ = parsed_[28:-2]
        return parsed_


async def add_user_document(documentpath):
    parsed_doc = await parse_pdf(documentpath)
    prompt = f"""
    You are a helpful AI agent.
    You are a knowledgeable agent aware of the field of chartered accountancy and finance. Particularly, you are
    aware of the income tax laws and regulations in India.
    You are tasked with adding the following document to your database: '{parsed_doc}'.
    The document is a document input by a user and is a statement of their income and expenses for the year.
    Your job is to parse the document and extract the relevant information from it, such as the income, expenses, and any other relevant information.
    You should return the extracted information in a structured format that is easy to understand and is descriptive of the document's content.
    """
    summarised_doc = call_llm(prompt)
    prompt = f"""
    You are a helpful AI agent.
    Return a small one-line descriptor of the content of this document: '{parsed_doc}'.
    You have generated a summary of the document: '{summarised_doc}'
    Now you need to return a one-line descriptor for the same document.sum
    """
    point_doc = call_llm(prompt)
    return summarised_doc, point_doc


async def add_to_info(documentpath, info_dict):
    summ_doc, point_doc = await add_user_document(documentpath)
    info_dict[point_doc] = summ_doc
    return info_dict


async def single_section_handler(info_dict, section):
    temp = "\n\n".join(info_dict.keys())
    query = f"""
    Identify and classify the sections of the income tax act that are applicable for tax deduction in context of a user who has given you documents related to the same.
    The sections that are relevant are: {", ".join(section)}
    The documents that are input by the user are as follows:{temp}
    """
    response = multi_retrieval_CA_agent(query, section, info_dict)
    prompt_new = f"""
    {query}
    You also have the following response based on a multi-retrieval RAG-based process which has been crafted to assist you in this task:
    {response}
    Output a response that clearly mentions which sections of tax deduction are applicable to the user, and which sections aren't, and those which are ambiguous.
    The response should be structured as a JSON input structured as follows:
    The JSON structure should include three keys: applicable_sections, non_applicable_sections, and probable_sections.
    Each section should be represented as an array of objects with two keys: section (the tax section code) and summary (a brief explanation of the individual's eligibility or lack thereof)
    This summary should be relevant to the user and not generic.
    """
    response = call_llm(prompt_new)
    return response


async def overall_handler(info_dict):
    responses = []
    for section in RELEVANT_SECTIONS:
        response = await single_section_handler(info_dict, section)
        responses.append(response)
    temp = "\n\n".join(responses)
    debug_print(True, "Final response consolidation")
    prompt_new = f"""
    You are a helpful AI agent.
    You were tasked with identifying which sections of the income tax act are applicable for tax deduction in context of a user who has given you documents related to the same.
    You have successfully identified the sections that are applicable and those that are not.
    You have also identified the sections that are ambiguous and require further clarification.
    You have generated the following responses for different groups of related sections:
    {temp}
    The last step is to combine all the responses into a single JSON output that clearly mentions which sections of tax deduction are applicable to the user, and which sections aren't, and those which are ambiguous.
    The response should be structured as a JSON input structured as follows:
    The JSON structure should include three keys: applicable_sections, non_applicable_sections, and probable_sections.
    Each section should be represented as an array of objects with two keys: section (the tax section code) and summary (a brief explanation of the individual's eligibility or lack thereof)
    Make sure the format of the JSON is as shown here:
    {{
        "applicable_sections": [
    {{
      "section": "80C",
      "summary": "Allows deductions for investments in specified savings instruments up to ₹1.5 lakh."
    }},
    ...
    
  ],
  "non_applicable_sections": [
    {{
      "section": "80CC",
      "summary": "Generally not utilized or referenced by individual taxpayers."
    }}
    ...
  ],
  "probable_sections": [
    {{
      "section": "80GGA",
      "summary": "Applicable if the user made donations for scientific research or rural development."
    }}
    ...
  ]
    }}
    This summary should be relevant to the user and not generic.
    Do NOT include any information other than the JSON output.
    """

    response = call_llm(prompt_new)
    debug_print(True, "generated response")
    debug_print(True, response)
    return response


async def evaluate(file_path, query, id):
    global check_event
    info_dict = {}
    info_dict = await add_to_info(file_path, info_dict)
    info_dict["The user's description of their tax situation"] = query
    response = await overall_handler(info_dict)
    debug_print(True, response)
    response = json.loads(response[7:-3])
    db.update_one({"CAID": id}, {"$set": response}, upsert=True)
    check_event.set()


@app.post("/submit")
async def upload_file(file: UploadFile = File(...), query: str = Form(...)):
    file_path = os.path.join(SAVE_DIR, file.filename)
    id = str(uuid.uuid4())
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    asyncio.create_task(evaluate(file_path, query, id))

    return {
        "message": "Files uploaded successfully, generation in progress.",
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
