from common.hyde import hyde_query
from rag.client import retrieve_documents
from common.reranker import rerank_docs
from common.metrag import metrag_filter
from common.corrective_rag import corrective_rag
from common.llm import call_llm
from swarm.util import debug_print


def single_retrieval_agent(query):
    """Answer simple queries by running them through HyDe and then retrieve the documents"""
    debug_print(True, f"Processing tree call: SINGLE_RETRIEVAL")
    modified_query = hyde_query(query)
    documents = retrieve_documents(modified_query)
    documents = metrag_filter(documents, query, "general")
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
            """

    response = call_llm(prompt) 
    return response,context
