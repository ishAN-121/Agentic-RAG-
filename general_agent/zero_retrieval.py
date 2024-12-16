from common.hyde import hyde_query
from rag.client import retrieve_documents
from common.reranker import rerank_docs
from common.metrag import metrag_filter
from common.llm import call_llm


def zero_retrieval_agent(query):
    """Answer extremely simple queries without any RAG-retrieval"""

    response = call_llm(query)
    return response,None
