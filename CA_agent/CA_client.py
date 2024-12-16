from pathway.xpacks.llm.vector_store import VectorStoreClient

VECTOR_PORT = 8225
PATHWAY_HOST = "127.0.0.1"

vector_client = VectorStoreClient(
    host=PATHWAY_HOST,
    port=VECTOR_PORT,
)


def retrieve_documents(query: str):
    return vector_client.query(query, 10)
