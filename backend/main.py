import pathway as pw
from data_registry import get_data_stream, get_simulation_stream
import pathway as pw
from pathway.stdlib.indexing.nearest_neighbors import BruteForceKnnFactory
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm import llms

class QuerySchema(pw.Schema):
    messages: str


def build_rag_pipeline(combined_stream):
    rag_stream = combined_stream.select(
        # 1. Rename 'text' -> 'data'
        data=pw.this.text,
        
        # 2. Pack other columns into a dictionary called '_metadata'
        _metadata=pw.apply(
            lambda src, url, ts, bias: {
                "source": src,
                "url": url, 
                "timestamp": ts, 
                "bias": bias
            },
            pw.this.source,
            pw.this.url,
            pw.this.timestamp,
            pw.this.bias
        )
    )


    embedder = SentenceTransformerEmbedder(
        model="all-MiniLM-L6-v2")
    # Define the Vector Store Server
    retriever_factory = BruteForceKnnFactory(
    embedder=embedder,
    )

    document_store = DocumentStore(
    docs=rag_stream,
    retriever_factory=retriever_factory,
    parser=None,
    splitter=None,
    )

    print("✅ RAG Pipeline built successfully.")
    return document_store

def get_context(documents):
    content_list = []
    for doc in documents:
        content_list.append(str(doc["text"]))
    return " ".join(content_list)

@pw.udf
def build_prompts_udf(documents, query) -> str:
    context = get_context(documents)
    prompt = (
        f"Given the following documents : \n {context} \nanswer this query: {query}"
    )
    return prompt


def run():
    stream = get_data_stream()

    pw.io.http.write(
        table=stream,
        url='http://localhost:8000/v1/stream',
        method='POST',
        format='json'
    )

    document_store = build_rag_pipeline(stream)
   
    webserver = pw.io.http.PathwayWebserver(host="0.0.0.0", port=8011)

    queries, writer = pw.io.http.rest_connector(
        webserver=webserver,
        route='/v1/query',
        schema=QuerySchema,
        autocommit_duration_ms=50,
        delete_completed_queries=False,
    )

    queries = queries.select(
        query = pw.this.messages,
        k = 5,
        metadata_filter = None,
        filepath_globpattern = None,
    )

    retrieved_documents = document_store.retrieve_query(queries)
    retrieved_documents = retrieved_documents.select(docs=pw.this.result)
    queries_context = queries + retrieved_documents

    prompts = queries_context+queries_context.select(
    prompts=build_prompts_udf(pw.this.docs, pw.this.query)
    )

    model = llms.HFPipelineChat(
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    )

    response = prompts.select(
        *pw.this.without(pw.this.query, pw.this.prompts, pw.this.docs),
        result=model(
            llms.prompt_chat_single_qa(pw.this.prompts),
        ),
    )

    writer(response)

    pw.run()

if __name__ == "__main__":
    run()
