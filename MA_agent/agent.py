import json
import os
import uuid
from fastapi import FastAPI, File, Form, UploadFile, WebSocket
import asyncio
from typing import List
from common.plan_rag import plan_rag_query, single_plan_rag_step_query
from rag.client import retrieve_documents
from swarm.util import debug_print
from rag.rrf import rerank_results


from MA_agent.constants import (
    LIST_OF_DOCUMENTS_INPUT,
    LIST_OF_DOCUMENTS_OUTPUT,
    DOCUMENT_PROMPT_MAPPING,
)
from itertools import chain
import MA_agent.prompts as prompts
from common.llm import call_llm
import uvicorn
import pymongo
from fastapi.middleware.cors import CORSMiddleware

uri = os.getenv("MONGO_CONNECTION_STRING")
client = pymongo.MongoClient(uri)

from pathway.xpacks.llm.vector_store import VectorStoreClient

VECTOR_PORT = 8000
PATHWAY_HOST = "127.0.0.1"

vector_client = VectorStoreClient(
    host=PATHWAY_HOST,
    port=VECTOR_PORT,
)


def retrieve_docs(query: str):
    query_prefix = "Represent this sentence for searching relevant passages: "
    vector_results = vector_client.query(query_prefix + query, 10)
    results = []
    results.append(vector_results)
    return rerank_results(results)


check_event = asyncio.Event()


async def retrieve_and_process(query):
    return retrieve_docs(query)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
with open("./MA_agent/definitive_agreement_outline.txt", "r") as f:
    definitive_agreement_outline = f.read()
with open("./MA_agent/term_sheet_outline.txt", "r") as f:
    term_sheet_outline = f.read()
with open("./MA_agent/letter_of_intent_outline.txt", "r") as f:
    letter_of_intent_outline = f.read()
with open("./MA_agent/nda_outline.txt", "r") as f:
    nda_outline = f.read()
with open("./MA_agent/due_diligence_outline.txt", "r") as f:
    due_diligence_outline = f.read()


DOCUMENT_OUTLINE_MAPPING = {
    "Definitive Agreement": definitive_agreement_outline,
    "Term Sheet": term_sheet_outline,
    "Letter of Intent": letter_of_intent_outline,
    "NDA": nda_outline,
    "Due Diligence": due_diligence_outline,
}

os.makedirs("MA", exist_ok=True)


def plan_to_queries(plan):
    queries = []
    for step in plan.split("\n"):
        if len(step) > 0:
            debug_print(True, f"Step: {step}")
            query = single_plan_rag_step_query(step)
            queries.append(query)
    return queries


async def generate_agreement(company1, company2, id, instructions):
    async def create_queries(output_doc):
        plan = plan_rag_query(
            query=None,
            agent="M&A",
            companies=(company1, company2),
            input_docs=LIST_OF_DOCUMENTS_INPUT,
            output_doc=output_doc,
        )
        queries: list[str] = plan_to_queries(plan)
        return queries

    tasks = [create_queries(output_doc) for output_doc in LIST_OF_DOCUMENTS_OUTPUT]
    cache_file = f"MA_agent/{id}_queries_cache.txt"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            all_docs_queries = json.load(f)
            debug_print(True, "Loaded queries from cache")
    else:
        all_docs_queries: list[list[str]] = await asyncio.gather(*tasks)
        with open(cache_file, "w") as f:
            json.dump(all_docs_queries, f)
            debug_print(True, "Dumped queries to cache")

    #    tasks = [create_queries(output_doc) for output_doc in LIST_OF_DOCUMENTS_OUTPUT]

    # Wait for all tasks to complete in parallel and collect queries
    # all_docs_queries: list[list[str]] = await asyncio.gather(*tasks)
    #
    # Flatten the nested list of queries
    all_queries = list(chain.from_iterable(all_docs_queries))
    debug_print(True, "All queries")
    # Use asyncio.gather to await all `retrieve_docs` calls
    all_results = await asyncio.gather(
        *(retrieve_and_process(query) for query in all_queries)
    )
    debug_print(True, "All results")

    start_idx = 0
    final_results: list[list[any]] = []
    for query_group in all_docs_queries:
        count = len(query_group)
        documents = all_results[start_idx : start_idx + count]
        final_results.append(list(chain.from_iterable(documents)))
        start_idx += count
    debug_print(True, "Final results")

    async def create_summaries(documents, doc_type, company_name):
        summary = await generate_summary(documents, doc_type, company_name)
        return summary

    debug_print(True, "Summaries")
    tasks = []
    for idx, output_doc in enumerate(LIST_OF_DOCUMENTS_OUTPUT):
        for company in enumerate([company1, company2]):
            tasks.append(create_summaries(final_results[idx], output_doc, company))
    debug_print(True, "Tasks")
    summaries: list[str] = await asyncio.gather(*tasks)
    debug_print(True, "Summaries 2")
    # Generate the final documents based on the summaries parallely
    tasks = []
    for idx in range(0, len(summaries), 2):
        output_doc = LIST_OF_DOCUMENTS_OUTPUT[idx // 2]
        tasks.append(
            generate_document(
                output_doc,
                company1,
                company2,
                summaries[idx],
                summaries[idx + 1],
                instructions,
            )
        )
    debug_print(True, "Tasks 2")
    documents: list[str] = await asyncio.gather(*tasks)
    output_to_document: dict[str, str] = {
        output_doc: document
        for output_doc, document in zip(LIST_OF_DOCUMENTS_OUTPUT, documents)
    }
    debug_print(True, "Final")
    insights = await generate_insights(summaries, company1, company2, instructions)
    metrics = await generate_metrics(summaries, company1, company2, instructions)

    await send_documents(output_to_document, insights, id, metrics)


@app.post("/submit")
async def ingest(
    company1: str = Form(...),  # Extract `company1` from form data
    company2: str = Form(...),  # Extract `company2` from form data
    files: List[UploadFile] = File(...),  # Extract `files` as a list of uploaded files
    instructions: str = Form(...),
):
    # Generate a unique ID for this request
    id = str(uuid.uuid4())

    # Save each uploaded file to the server
    for file in files:
        file_location = f"./MA_agent/MA/{id}_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

    asyncio.create_task(generate_agreement(company1, company2, id, instructions))

    # Return a response with the generated conversation ID
    return {
        "message": "Files uploaded successfully, agreement generation in progress.",
        "conversation_id": id,
    }


async def generate_document(
    type, company1, company2, company1_details, company2_details, instructions
):
    prompt = DOCUMENT_PROMPT_MAPPING[type].format(
        company_a=company1,
        company_b=company2,
        company_a_details=company1_details,
        company_b_details=company2_details,
        document_outline=DOCUMENT_OUTLINE_MAPPING[type],
        instructions=instructions,
    )
    document = call_llm(prompt)
    return document


# Final_results[idx]
async def generate_summary(documents, doc_type, company_name):
    prompt = prompts.SUMMARY_PROMPT.format(
        company_name=company_name,
        document_type=doc_type,
        context=" ".join(doc["text"] for doc in documents),
    )
    summary = call_llm(prompt)
    return summary


# Function to generate insights based on document headings
async def generate_insights(summaries, company1, company2, instructions):
    company1_summary = " ".join(summary for summary in summaries[::2])
    company2_summary = " ".join(summary for summary in summaries[1::2])
    prompt = prompts.INSIGHTS_PROMPT.format(
        company_a=company1,
        company_b=company2,
        a_summary=company1_summary,
        b_summary=company2_summary,
        instructions=instructions,
    )
    debug_print(True, "before llm")
    insights = call_llm(prompt)
    debug_print(True, "after llm")
    debug_print(True, insights)
    insights = json.loads(insights)

    return insights


async def generate_metrics(summaries, company1, company2, instructions):
    company1_summary = " ".join(summary for summary in summaries[::2])
    company2_summary = " ".join(summary for summary in summaries[1::2])
    prompt = prompts.METRICS_PROMPT.format(
        company_a=company1,
        company_b=company2,
        a_summary=company1_summary,
        b_summary=company2_summary,
        instructions=instructions,
    )
    metrics = call_llm(prompt)
    metrics = json.loads(metrics)
    return metrics


async def send_documents(output_to_document, insights, conversation_id, metrics):
    # store the documents in the database using the mongo client and conversation_id
    global check_event
    db = client["sirius"]
    collection = db["MergerAcquisition"]
    output_to_document["insights"] = insights
    output_to_document["conversation_id"] = conversation_id
    output_to_document["metrics"] = metrics

    collection.insert_one(output_to_document)
    check_event.set()
    return


@app.websocket("/ws/check")
async def check(ws: WebSocket):
    await ws.accept()
    global check_event
    while True:
        await check_event.wait()
        await ws.send_json({"result": "OK"})
        check_event.clear()


# Run the FastAPI application
if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8001)
