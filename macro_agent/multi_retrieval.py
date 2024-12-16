from common.reranker import rerank_docs
from common.llm import call_llm
from common.hyde import hyde_query
from rag.client import retrieve_documents
from common.plan_rag import plan_rag_query
from common.metrag import metrag_filter


def single_retriever_macro_agent(query):
    """For simple queries, run them through HyDe and then retrieve the documents"""

    modified_query = hyde_query(query)
    documents = retrieve_documents(modified_query)
    documents = metrag_filter(documents, query, "macro")
    documents = corrective_rag(query, documents)

    result = rerank_docs(modified_query, documents)

    documentlist = [doc.document.text for doc in result.results]
    context = "\n\n".join(documentlist)
    prompt = f"""You are a helpful chat assistant that helps create a summary of the following context: '{context}', in light of the query: '{query}'.
                You must keep in mind that you are an expert in market analysis, and that the response you generate should be tailored accordingly.
            """
    response = call_llm(prompt)
    # TODO
    documents = metrag_filter(documents, query, "macro")

    return documents, response


def multi_retrieval_macro_agent(query):
    """Answer complex queries by running them through a multi-retrieval process based on PlanRAG"""
    plan = plan_rag_query(query, "macro")
    documents = []
    response = []
    print(f"Plan:\n{plan}")
    for step in plan.split("\n"):
        if len(step) > 0:
            query_prompt = f"""You are a helpful prompt engineering assistant that must generate a query to feed to an LLM based on the given step in a multi-step plan.
                The step you must generate a query for is: {step}
                The query you generate should be clear and concise, and should be designed to retrieve the most relevant documents and information for the given step.
                It should be a query and not a statement, and must be no longer than 2 sentences.
                You must keep in mind that you are an expert in market analysis, and that the query you generate should be tailored accordingly.
                """
            query = call_llm(query_prompt)
            print(f"Step:\n{step}")
            print(f"Query:\n{query}")
            docs, resp = single_retriever_macro_agent(query)
            for i, doc in enumerate(docs):
                print(f"\nDocument {i}:")
                for key, value in doc.items():
                    print(f"{key}: {value}")
            documents.extend(docs)
            response.append(resp)

    # modified_query = hyde_query(query) # For the complex query, do we need HyDE?

    result = rerank_docs(query, documents)

    documents = [doc.document.text for doc in result.results]
    context_response = "\n\n".join(response)
    context_documents = "\n\n".join(documents)
    prompt = f"""You are a helpful chat assistant that helps answer query based on the given context.
            Currently, you had given a step-by-step plan to generate the answer and the plan is as follows:
            {plan}
            The responses to the queries generated from the plan are as follows:
            {context_response}
            Supplementary information to the responses is as follows:
            {context_documents}
            Do not use outside knowledge to answer the query. If there is missing context, don't try to make up facts and figures.
            You must keep in mind that you are an expert in market analysis, and that the response you generate should be tailored accordingly.
            """
    response = call_llm(prompt)
    return response
