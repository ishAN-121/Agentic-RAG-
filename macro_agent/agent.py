from fastapi import FastAPI, WebSocket, Form
import uvicorn
import pymongo
import uuid
from common.reranker import rerank_docs
from langchain_openai import ChatOpenAI
from common.hyde import hyde_query
from rag.client import retrieve_documents
from common.plan_rag import plan_rag_query
from common.metrag import metrag_filter
from common.corrective_rag import corrective_rag
from common.llm import call_llm
from common.plan_rag import single_plan_rag_step_query
from concurrent.futures import ThreadPoolExecutor, as_completed
from swarm.util import debug_print
import asyncio
import os
from fastapi.middleware.cors import CORSMiddleware

check_event = asyncio.Event()
uri = os.getenv("MONGO_CONNECTION_STRING")
client = pymongo.MongoClient(uri)
db = client["sirius"]
db = db["MacroAgent"]
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def single_retriever_macro_agent(query):
    """For simple macro analysis queries, run them through HyDe and then retrieve the documents"""
    mod_query = hyde_query(query)

    documents = retrieve_documents(mod_query)
    debug_print(True, f"documents: {len(documents)}")
    documents = metrag_filter(documents, query, "macro")
    documents = corrective_rag(query, documents)
    result = rerank_docs(mod_query, documents)

    documentlist = [doc.document.text for doc in result.results]
    context = "\n\n".join(documentlist)

    prompt = f"""You are a helpful chat assistant that helps create a summary of the following context: '{context}', in light of the query: '{query}'.
                You must keep in mind that you are an expert in the field of macro analysis, and that the response you generate should be tailored accordingly.
            """

    response = call_llm(prompt)

    return documents, response


def step_executor(step):
    query_ = single_plan_rag_step_query(step)
    documents, response = single_retriever_macro_agent(query_)
    return documents, response


async def multi_retrieval_macro_agent(query, id):
    """Answer complex macro analysis related queries by running them through a multi-retrieval process based on PlanRAG"""

    plan = plan_rag_query(query, "macro")
    dict_store = {}
    resp_dict = {}
    documents = []
    response = []

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(step_executor, step): i
            for i, step in enumerate(plan.split("\n"))
            if step
        }
        for future in as_completed(futures):
            i = futures[future]
            docs, resp = future.result()
            dict_store[i] = docs
            resp_dict[i] = resp
    for i in sorted(dict_store.keys()):
        documents.extend(dict_store[i])
        response.extend(resp_dict[i])

    modified_query = hyde_query(query)
    documents = metrag_filter(documents, query, "macro")
    documents = corrective_rag(query, documents)
    result = rerank_docs(modified_query, documents)

    documents = [doc.document.text for doc in result.results]

    context_response = "\n\n".join(response)
    context_documents = "\n\n".join(documents)

    prompt = f"""You are a helpful chat assistant that helps answer a query based on the given context.
            The query is as follows:
            {query}
            Currently, you had given a step-by-step plan to generate the answer and the plan is as follows:
            {plan}
            The responses to the queries generated from the plan are as follows:
            {context_response}
            Supplementary information to the responses is as follows:
            {context_documents}
            Do not use outside knowledge to answer the query. If there is missing context, don't try to make up facts and figures.
            You must keep in mind that you are an expert in the field of macro analysis, and that the response you generate should be tailored accordingly.
            """

    response = call_llm(prompt)
    db.update_one({"MacroID": id}, {"$set": {"response": response}}, upsert=True)
    check_event.set()


@app.post("/submit")
async def submit(query: str = Form(...)):
    id = str(uuid.uuid4())
    asyncio.create_task(multi_retrieval_macro_agent(query, id))
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
