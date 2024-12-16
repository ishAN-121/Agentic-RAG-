import os, cohere
from swarm.util import debug_print

co = cohere.Client(api_key=os.environ["COHERE_API_KEY"])


def rerank_docs(query, dat_arr):
    debug_print(True, f"Processing tool call: {rerank_docs.__name__}")
    debug_print(True, f"Processing tree call: Cohere Rerank")
    results = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=dat_arr,
        #rank_fields=["text"],
        top_n=4,
        return_documents=True,
    )
    return results
