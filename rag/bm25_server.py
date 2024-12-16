import pathway as pw
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.servers import DocumentStoreServer
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.xpacks.llm.splitters import TokenCountSplitter

bm25 = pw.indexing.TantivyBM25Factory()

data_sources = []

data_sources.append(
    pw.io.fs.read(
        "./documents",
        format="binary",
        mode="streaming",
        with_metadata=True,
    )
)
data_sources.append(
    pw.io.fs.read(
        "../MA_agent/MA",
        format="binary",
        mode="streaming",
        with_metadata=True,
    )
)

splitter = TokenCountSplitter(min_tokens=1000, max_tokens=1500)
parser = ParseUnstructured()
bm25_store = DocumentStore(
    data_sources, retriever_factory=bm25, splitter=splitter, parser=parser
)

bm25_server = DocumentStoreServer(
    port=7000, host="127.0.0.1", document_store=bm25_store
)
bm25_server.run()
