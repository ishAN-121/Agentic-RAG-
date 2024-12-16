from common.llm import call_llm
from common.websearch import tavily_search
from swarm.util import debug_print
from concurrent.futures import ThreadPoolExecutor

CORRECT_THRESHOLD = 0.4
AMBIGUOUS_THRESHOLD = 0.2


def corrective_rag(query, documents):
    debug_print(True, f"Processing tool call: {corrective_rag.__name__}")
    debug_print(True, f"Processing tree call: CRAG")
    total_score = 0
    doc_length = len(documents)

    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda doc: score_document_relevance(query, doc), documents
        )
    total_score = sum(results)

    for doc in documents:
        total_score += score_document_relevance(query, doc)
    if doc_length > 0:
        total_score /= doc_length
    if total_score > CORRECT_THRESHOLD:
        return documents
    elif total_score > AMBIGUOUS_THRESHOLD:
        external_knowledge = tavily_search(query)
        return documents + external_knowledge
    else:
        return tavily_search(query)


def score_document_relevance(query, document):
    debug_print(True, f"Processing tool call: {score_document_relevance.__name__}")
    """Evaluate and return relevance of documents on a scale of 0-1 (Only output the score, up to 2 decimal places)"""

    score = call_llm(
        f"""
        For the query: '{query}'
        
        Evaluate the relevance of the following document on a scale of 0-1 for answering the above query.
        
        Document: '{document}'
        
        Only output the score, up to 2 decimal places
        """
    )

    return float(score)
