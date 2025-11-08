import os
from dotenv import load_dotenv

load_dotenv()

class RAGConfig:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    # Vector Store Configuration
    USE_LOCAL_STORE = os.getenv("USE_LOCAL_STORE", "false").lower() == "true"
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "financial-news")
    
    # Embedding Configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # sentence-transformers model
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RSS Feed Configuration
    RSS_FEEDS = [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.investing.com/rss/news_301.rss",
        "https://www.marketwatch.com/rss/topstories",
        "https://feeds.reuters.com/reuters/businessNews"
    ]
    
    # Vector Store Configuration
    VECTOR_DIMENSION = 384  # for all-MiniLM-L6-v2
    METRIC = "cosine"
    
    # Retrieval Configuration
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.7 