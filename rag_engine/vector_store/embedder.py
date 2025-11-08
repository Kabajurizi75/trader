from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Dict, Optional
import logging

from ..config import RAGConfig

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or RAGConfig.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAGConfig.CHUNK_SIZE,
            chunk_overlap=RAGConfig.CHUNK_OVERLAP,
            length_function=len,
        )
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using sentence-transformers"""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            return []
    
    def embed_single_text(self, text: str) -> List[float]:
        """Embed a single text"""
        try:
            embedding = self.model.encode([text])
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Error embedding single text: {e}")
            return []
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Document]:
        """Split text into chunks using LangChain text splitter"""
        try:
            doc = Document(page_content=text, metadata=metadata or {})
            chunks = self.text_splitter.split_documents([doc])
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            return []
    
    def chunk_articles(self, articles: List[Dict]) -> List[Document]:
        """Convert articles to LangChain documents with chunking"""
        documents = []
        
        for article in articles:
            try:
                # Combine title and summary for embedding
                content = f"Title: {article['title']}\n\nSummary: {article['summary']}"
                
                # Create metadata
                metadata = {
                    'title': article['title'],
                    'source': article['source'],
                    'link': article['link'],
                    'published': article.get('published', ''),
                    'feed_title': article.get('feed_title', ''),
                    'timestamp': article.get('timestamp', ''),
                    'article_id': article.get('id', '')
                }
                
                # Create document and chunk it
                doc = Document(page_content=content, metadata=metadata)
                chunks = self.text_splitter.split_documents([doc])
                documents.extend(chunks)
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        logger.info(f"Created {len(documents)} chunks from {len(articles)} articles")
        return documents
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        return self.model.get_sentence_embedding_dimension()

def embed_texts(texts):
    """Backward compatibility function"""
    embedder = TextEmbedder()
    return embedder.embed_texts(texts)
