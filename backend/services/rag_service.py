"""LangChain RAG Service - Query intelligence database

Replaces Pathway RAG with LangChain + Qdrant for document retrieval
and OpenRouter for LLM inference.
"""

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant, QdrantVectorStore
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = "flashpoint_events"


class RAGService:
    """LangChain-based RAG for querying intelligence database"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of RAG components"""
        if self._initialized:
            return
        
        # Initialize embeddings (same model used for indexing)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Connect to Qdrant
        client = QdrantClient(url=QDRANT_URL)
        self.vectorstore = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=self.embeddings,   # note: "embedding" not "embeddings"
        )
        
        # Initialize OpenRouter LLM - using less busy models
        self.llm = ChatOpenAI(
            model="deepseek/deepseek-chat",  # DeepSeek R1 - fast and reliable
            openai_api_base=OPENROUTER_API_BASE,
            openai_api_key=OPENROUTER_API_KEY,
            temperature=0.7,
            max_tokens=1000,
            streaming=True
        )
        
        # Create custom prompt template
        prompt_template = """You are FlashPoint, an advanced geopolitical intelligence analysis system.

Context: You have access to real-time intelligence data from multiple sources including RSS feeds, 
Telegram channels, Reddit discussions, and news agencies. The data includes events from global 
conflicts, geopolitical developments, and breaking news.

Based on the following intelligence reports, provide a comprehensive analysis:

{context}

Question: {question}

Instructions:
- Analyze the intelligence data critically
- Identify patterns, contradictions, or bias across sources
- Provide actionable insights
- Cite specific sources when possible
- If information is insufficient, state that clearly

Analysis:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={
                    "k": 10,  # Retrieve top 10 documents
                    "score_threshold": 0.5  # Minimum similarity threshold
                }
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        self._initialized = True
        print("✅ RAG Service initialized (LangChain + Qdrant)")
 # query() method simplified:
    def query(self, question: str) -> dict:
        self._initialize()
        try:
            docs = self.vectorstore.as_retriever(
                search_kwargs={"k": 10}
            ).invoke(question)
            context = "\n\n".join([d.page_content for d in docs])
            return {"success": True, "answer": context, "sources": []}
        except Exception as e:
            return {"success": False, "error": str(e), "answer": str(e)}
    
    async def query_streaming(self, question: str):
        """Query with streaming response (async generator)
        
        Yields token chunks for SSE streaming to frontend
        """
        self._initialize()
        
        try:
            # Get retriever
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 10, "score_threshold": 0.5}
            )
            
            # Retrieve documents
            docs = retriever.invoke(question)
            
            # Build context
            context = "\n\n".join([
                f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in docs
            ])
            
            # Build prompt
            prompt_template = """You are FlashPoint, an advanced geopolitical intelligence analysis system.

Context: You have access to real-time intelligence data from multiple sources including RSS feeds, 
Telegram channels, Reddit discussions, and news agencies.

Based on the following intelligence reports, provide a comprehensive analysis:

{context}

Question: {question}

Analysis:"""
            
            prompt = prompt_template.format(context=context, question=question)
            
            # Stream tokens from LLM
            async for chunk in self.llm.astream(prompt):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
                    
        except Exception as e:
            yield f"\n\n⚠️ Error: {str(e)}"


# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get singleton RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
