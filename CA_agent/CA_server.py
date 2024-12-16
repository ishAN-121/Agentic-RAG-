import sys, logging
import pathway as pw
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.parsers import ParseUnstructured

logging.basicConfig(stream=sys.stderr, level=logging.WARN, force=True)

data_sources = []
data_sources.append(
    pw.io.fs.read(
        "./CA_agent/IncomeTaxDocuments",
        format="binary",
        mode="streaming",
        with_metadata=True,
    )
)

PATHWAY_PORT = 8225
PATHWAY_HOST = "127.0.0.1"

text_splitter = TokenCountSplitter(min_tokens=500, max_tokens=1000)
embedder = SentenceTransformerEmbedder(model="paraphrase-MiniLM-L6-v2")
parser = ParseUnstructured()

vector_server = VectorStoreServer(
    *data_sources,
    parser=parser,
    embedder=embedder,
    splitter=text_splitter,
)
vector_server.run_server(
    host=PATHWAY_HOST, port=PATHWAY_PORT, threaded=False, with_cache=False
)
