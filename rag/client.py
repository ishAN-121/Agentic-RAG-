from pathway.xpacks.llm.vector_store import VectorStoreClient
from rag.rrf import rerank_results
from pymongo import MongoClient
from bson import Binary
from swarm.util import debug_print
import base64

VECTOR_PORT = 8000
BM25_PORT = 7000
SPLADE_PORT = 8500
PATHWAY_HOST = "127.0.0.1"

vector_client = VectorStoreClient(
    host=PATHWAY_HOST,
    port=VECTOR_PORT,
)
bm25_client = VectorStoreClient(
    host=PATHWAY_HOST,
    port=BM25_PORT,
)
splade_client = VectorStoreClient(
    host=PATHWAY_HOST,
    port=SPLADE_PORT,
)
from concurrent.futures import ThreadPoolExecutor

dbclient = MongoClient("mongodb://localhost:27017")
db = dbclient["interiit"]
db = db["chunks"]


def str_to_binary(id_str):
    return Binary(base64.b64decode(id_str.encode("utf-8")), 4)


def graph_lookup(docs, n=3):

    chunks = []
    for doc in docs:
        curr_id = str_to_binary(doc["metadata"]["id"])
        pipeline = [
            {"$match": {"_id": curr_id}},  # Start with the specific chunk
            {
                "$graphLookup": {
                    "from": "chunks",  # The collection to search within
                    "startWith": "$next_id",  # Start from the next chunk of the current document
                    "connectFromField": "next_id",  # Field to follow for the next chunk
                    "connectToField": "_id",  # Field to connect to (we are linking the `next_id` to `_id`)
                    "as": "next_chunks",  # Store the resulting linked chunks in `next_chunks`
                    "maxDepth": (n - 1)
                    // 2,  # Limit depth to avoid infinite loops (adjust as needed)
                    "depthField": "depth",  # Optionally, store the depth of each document in the result
                    "restrictSearchWithMatch": {
                        "next_id": {"$ne": None}
                    },  # Ensure the next_id exists
                }
            },
            {
                "$graphLookup": {
                    "from": "chunks",
                    "startWith": "$prev_id",  # Now trace the previous chunks
                    "connectFromField": "prev_id",  # Link back to the previous chunk
                    "connectToField": "_id",  # Field to connect to (link `prev_id` to `_id`)
                    "as": "prev_chunks",  # Store the linked chunks in `prev_chunks`
                    "maxDepth": (n - 1)
                    // 2,  # Limit the depth for reverse lookup as well
                    "depthField": "depth",
                    "restrictSearchWithMatch": {
                        "prev_id": {"$ne": None}
                    },  # Ensure the prev_id exists
                }
            },
        ]
        result = list(db.aggregate(pipeline))
        chunks.append(result["chunk"])
        chunks.extend(result["next_chunks"])
        chunks.extend(result["prev_chunks"])
    chunks = set(chunks)
    return list(chunks)


def retrieve_documents(query: str):
    query_prefix = "Represent this sentence for searching relevant passages: "
    debug_print(True, f"Processing tree call: RETRIEVING")
    with ThreadPoolExecutor() as executor:
        # vector_future = executor.submit(vector_client.query, query_prefix + query, 10)
        bm25_future = executor.submit(bm25_client.query, query, 10)
        splade_future = executor.submit(splade_client.query, query, 10)

        # vector_results = vector_future.result()
        bm25_results = bm25_future.result()
        splade_results = splade_future.result()

    #  make single list of results
    results = []
    # results.append(vector_results)
    results.append(bm25_results)
    results.append(splade_results)

    #  rerank results
    reranked_results = rerank_results(results)
    return reranked_results
