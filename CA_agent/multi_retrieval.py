from common.reranker import rerank_docs
from common.llm import call_llm
from CA_agent.CA_client import retrieve_documents
from common.plan_rag import plan_rag_query
from common.plan_rag import single_plan_rag_step_query
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.hyde import hyde_query
from common.metrag import metrag_filter
from common.corrective_rag import corrective_rag

def single_retriever_CA_agent(query):
    """Answer simple tax deduction related queries by running them through HyDe and then retrieve the documents"""

    modified_query = hyde_query(query)
    documents = retrieve_documents(modified_query)
    documents = metrag_filter(documents, query, "CA")
    documents = corrective_rag(query, documents)
    result = rerank_docs(modified_query, documents)
    documents = [doc.document.text for doc in result.results]
    context = "\n\n".join(documents)

    prompt = f"""You are a helpful chat assistant that helps answer a query based on the given context.
            The query is as follows:
            {query}
            The context provided to you is as follows:
            {context}
            Do not use outside knowledge to answer the query. If the answer is not contained in the provided information, just say that you don't know, don't try to make up an answer.
            You must keep in mind that you are an expert in the field of finance, and that the response you generate should be tailored accordingly.
            """
    
    response = call_llm(prompt)  
    return documents, response


def step_executor(step):
    query_ = single_plan_rag_step_query(step)
    documents, response = single_retriever_CA_agent(query_)
    return documents, response


def multi_retrieval_CA_agent(query, sections, info_dict):
    """Answer complex tax deduction queries by running them through a multi-retrieval process based on PlanRAG"""

    plan = plan_rag_query(
        query, "CA", userinfo=list(info_dict.keys()), section=sections
    )
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
    documents = metrag_filter(documents, query, "CA")
    documents = corrective_rag(query, documents)
    result = rerank_docs(modified_query, documents)

    documents = [doc.document.text for doc in result.results]

    context_response = "\n\n".join(response)
    context_documents = "\n\n".join(documents)
    temp = "\n\n".join(info_dict.values())

    prompt = f"""You are a helpful chat assistant that helps answer a query based on the given context.
            The query is as follows:
            {query}
            Currently, you had given a step-by-step plan to generate the answer which was as follows:
            {plan}
            The responses to the queries generated from the plan are as follows:
            {context_response}
            Supplementary information to the responses is as follows:
            {context_documents}
            Information provided in the documents uploaded by the user is as follows:
            {temp}
            You must keep in mind that you are an expert in the field of chartered accountancy, and that the response you generate should be tailored accordingly.
            Ensure that your output clearly mentions which sections of tax deduction are applicable to the user, and which section aren't.
            """

    response = call_llm(prompt)
    return response,context_documents