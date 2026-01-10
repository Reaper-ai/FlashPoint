"""Main Pathway RAG (Retrieval-Augmented Generation) Pipeline

This module orchestrates the core intelligence processing engine:
- Collects multi-source real-time data (news, Reddit, Telegram, RSS)
- Builds a RAG pipeline for intelligent document retrieval
- Processes user queries with context-aware LLM responses
"""

import pathway as pw
from data_registry import get_data_stream, get_simulation_stream
from pathway.stdlib.indexing.nearest_neighbors import BruteForceKnnFactory
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm import llms

# Query schema for REST endpoint: receives user search queries
class QuerySchema(pw.Schema):
    """Schema for incoming user queries from HTTP endpoint"""
    messages: str


def build_rag_pipeline(combined_stream):
    """Build RAG pipeline with embedding-based document retrieval
    
    Process:
    1. Transform raw data stream into RAG-compatible format
    2. Extract 'text' field for semantic embedding
    3. Preserve metadata (source, URL, timestamp, bias) for context
    4. Initialize sentence embedder for semantic similarity search
    5. Create document store with KNN-based retrieval
    
    Args:
        combined_stream: Pathway table with columns [source, text, url, timestamp, bias]
    
    Returns:
        DocumentStore: Initialized store for document retrieval queries
    """
    # Transform input stream: rename text field and pack metadata
    rag_stream = combined_stream.select(
        # Extract main content for embedding/retrieval
        data=pw.this.text,
        
        # Bundle source provenance info into metadata dictionary
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

    # Initialize semantic embedder: converts text to 384-dim vectors
    # Model: all-MiniLM-L6-v2 (lightweight, 22M params, optimized for inference)
    embedder = SentenceTransformerEmbedder(
        model="all-MiniLM-L6-v2")
    
    # Configure brute-force KNN retriever for nearest-neighbor search
    # (Suitable for moderate datasets; scales O(n) per query)
    retriever_factory = BruteForceKnnFactory(
        embedder=embedder,
    )

    # Build document store: manages document indexing and retrieval
    document_store = DocumentStore(
        docs=rag_stream,  # Source documents to index
        retriever_factory=retriever_factory,  # Search strategy
        parser=None,  # No additional parsing (raw text)
        splitter=None,  # No chunking (treat docs as atomic units)
    )

    print("✅ RAG Pipeline built successfully.")
    return document_store

def get_context(documents):
    """Extract and concatenate text from retrieved documents
    
    Args:
        documents: List of document dicts containing 'text' field
    
    Returns:
        str: Space-separated concatenation of all document texts
    """
    content_list = []
    for doc in documents:
        content_list.append(str(doc["text"]))
    return " ".join(content_list)

@pw.udf
def build_prompts_udf(documents, query) -> str:
    """Build LLM prompt from retrieved context and user query
    
    Constructs zero-shot question-answering prompt:
    - Provides retrieved documents as context
    - Appends user query
    - LLM uses context to formulate answer
    
    Args:
        documents: Retrieved context documents
        query: User's natural language question
    
    Returns:
        str: Formatted prompt for LLM consumption
    """
    context = get_context(documents)
    prompt = (
        f"Given the following documents : \n {context} \nanswer this query: {query}"
    )
    return prompt


def run():
    """Main execution: Orchestrate data collection, RAG pipeline, and query processing
    
    Pipeline stages:
    1. Collect multi-source data stream (news, Reddit, Telegram, RSS)
    2. Push data to backend API for frontend consumption
    3. Build RAG document store with semantic indexing
    4. Start HTTP server for query intake
    5. Process queries: retrieve context → build prompts → generate responses
    """
    # ========== STAGE 1: DATA COLLECTION ==========
    # Merge all sources into unified event stream
    stream = get_data_stream()

    # Push raw events to backend API (port 8000)
    # Frontend polls this endpoint for real-time updates
    pw.io.http.write(
        table=stream,
        url='http://localhost:8000/v1/stream',
        method='POST',
        format='json'
    )

    # ========== STAGE 2: RAG PIPELINE SETUP ==========
    # Build semantic document store for retrieval-augmented generation
    document_store = build_rag_pipeline(stream)
   
    # ========== STAGE 3: QUERY SERVICE ==========
    # Initialize HTTP webserver for query intake (port 8011)
    webserver = pw.io.http.PathwayWebserver(host="0.0.0.0", port=8011)

    # REST connector: listens for POST /v1/query, outputs responses
    queries, writer = pw.io.http.rest_connector(
        webserver=webserver,
        route='/v1/query',
        schema=QuerySchema,
        autocommit_duration_ms=50,  # Batch queries every 50ms
        delete_completed_queries=False,  # Retain query history
    )

    # Normalize query format and set retrieval parameters
    queries = queries.select(
        query = pw.this.messages,  # User's question
        k = 5,  # Retrieve top-5 most relevant documents
        metadata_filter = None,  # Retrieve from all sources
        filepath_globpattern = None,  # No file filtering
    )

    # ========== STAGE 4: DOCUMENT RETRIEVAL ==========
    # Semantic search: find K most similar documents to query
    retrieved_documents = document_store.retrieve_query(queries)
    # Rename result column to 'docs' for downstream processing
    retrieved_documents = retrieved_documents.select(docs=pw.this.result)
    
    # Join queries with their retrieved context
    queries_context = queries + retrieved_documents

    # ========== STAGE 5: PROMPT CONSTRUCTION ==========
    # Build LLM prompts: context + query → formatted instruction
    prompts = queries_context + queries_context.select(
        prompts=build_prompts_udf(pw.this.docs, pw.this.query)
    )

    # ========== STAGE 6: LLM INFERENCE ==========
    # Initialize small language model (1.1B params, CPU-optimized)
    model = llms.HFPipelineChat(
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    )

    # Generate responses using LLM with built prompts
    # Format: chat-based QA with retrieved context
    response = prompts.select(
        *pw.this.without(pw.this.query, pw.this.prompts, pw.this.docs),  # Keep metadata
        result=model(
            llms.prompt_chat_single_qa(pw.this.prompts),
        ),
    )

    # Write responses back to HTTP client
    writer(response)

    # Start event loop: process stream until interrupted
    pw.run()

if __name__ == "__main__":
    """Entry point: Start the Pathway RAG engine"""
    run()
