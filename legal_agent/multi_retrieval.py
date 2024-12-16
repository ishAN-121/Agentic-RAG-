from common.reranker import rerank_docs
from common.llm import call_llm
from common.hyde import hyde_query
from rag.client import retrieve_documents
from common.plan_rag import plan_rag_query
from common.plan_rag import single_plan_rag_step_query
from common.metrag import metrag_filter
from common.corrective_rag import corrective_rag
from concurrent.futures import ThreadPoolExecutor, as_completed
from swarm.util import debug_print


def single_retriever_legal_agent(query):
    """For simple legal related queries, run them through HyDe and then retrieve the documents"""
    mod_query = hyde_query(query)

    documents = retrieve_documents(mod_query)
    documents = metrag_filter(documents, query, "legal")
    documents = corrective_rag(query, documents)
    result = rerank_docs(mod_query, documents)

    documentlist = [doc.document.text for doc in result.results]
    context = "\n\n".join(documentlist)

    prompt = f"""You are a helpful chat assistant that helps create a summary of the following context: '{context}', in light of the query: '{query}'.
                You must keep in mind that you are a legal expert, and that the response you generate should be tailored accordingly.
            """

    response = call_llm(prompt)

    return documents, response


def step_executor(step):
    query_ = single_plan_rag_step_query(step)
    documents, response = single_retriever_legal_agent(query_)
    return documents, response


def multi_retrieval_legal_agent(query):
    """Answer complex legal related queries by running them through a multi-retrieval process based on PlanRAG"""
    debug_print(True, f"Processing tree call: MULTI_RETRIEVAL")
    plan = plan_rag_query(query, "legal")
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
    documents = metrag_filter(documents, query, "legal")
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
            You must keep in mind that you are a legal expert, and that the response you generate should be tailored accordingly.
            """

    response = call_llm(prompt)
    return response,context_documents
