from typing import List, Dict, Optional
import logging
from datetime import datetime

from .config import RAGConfig
from .ingest.rss_ingest import RSSIngester
from .vector_store.embedder import TextEmbedder
from .vector_store.pinecone_store import PineconeStore
from .vector_store.local_store import LocalVectorStore
from .llm.query_llm import LLMQueryEngine

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.config = RAGConfig()
        self.ingester = RSSIngester()
        self.embedder = TextEmbedder()
        
        # Choose vector store based on configuration
        if self.config.USE_LOCAL_STORE or not self.config.PINECONE_API_KEY:
            logger.info("Using local vector store")
            self.vector_store = LocalVectorStore()
        else:
            logger.info("Using Pinecone vector store")
            try:
                self.vector_store = PineconeStore()
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone, falling back to local store: {e}")
                self.vector_store = LocalVectorStore()
        
        self.llm_engine = LLMQueryEngine()
        
        logger.info("RAG Pipeline initialized")
    
    def ingest_and_store(self) -> bool:
        """Complete pipeline: ingest RSS feeds, embed, and store"""
        try:
            # Fetch articles
            articles = self.ingester.fetch_rss_feeds()
            if not articles:
                return False
            
            # Clean articles
            cleaned_articles = self.ingester.clean_articles(articles)
            
            # Convert to documents
            documents = self.embedder.chunk_articles(cleaned_articles)
            
            # Store in Pinecone
            return self.vector_store.store_documents(documents)
            
        except Exception as e:
            logger.error(f"Error in pipeline: {e}")
            return False
    
    def query(self, question: str) -> Dict:
        """Query the RAG system"""
        try:
            # Search for relevant documents
            relevant_docs = self.vector_store.search_similar(question, 5)
            
            if not relevant_docs:
                return {
                    'question': question,
                    'answer': "No relevant information found.",
                    'sources': []
                }
            
            # Generate answer
            answer = self.llm_engine.query_llm(question, relevant_docs)
            
            # Prepare sources
            sources = []
            for doc in relevant_docs:
                metadata = doc.get('metadata', {})
                sources.append({
                    'title': metadata.get('title', 'Unknown'),
                    'source': metadata.get('source', 'Unknown'),
                    'link': metadata.get('link', '')
                })
            
            return {
                'question': question,
                'answer': answer,
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                'question': question,
                'answer': f"Error: {str(e)}",
                'sources': []
            }
    
    def analyze_market_sentiment(self) -> Dict:
        """Analyze current market sentiment from stored news"""
        try:
            logger.info("Analyzing market sentiment...")
            
            # Search for recent market news
            sentiment_query = "market sentiment analysis financial news trends"
            relevant_docs = self.vector_store.search_similar(sentiment_query, 10)
            
            if not relevant_docs:
                return {
                    'sentiment': 'neutral',
                    'analysis': 'Insufficient recent news data for sentiment analysis',
                    'confidence': 'low'
                }
            
            # Get sentiment analysis from LLM
            analysis = self.llm_engine.analyze_market_sentiment(relevant_docs)
            
            # Simple sentiment classification (could be enhanced)
            analysis_lower = analysis.lower()
            if any(word in analysis_lower for word in ['positive', 'bullish', 'optimistic', 'growth']):
                sentiment = 'positive'
            elif any(word in analysis_lower for word in ['negative', 'bearish', 'pessimistic', 'decline']):
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'analysis': analysis,
                'confidence': 'medium',
                'sources_count': len(relevant_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                'sentiment': 'unknown',
                'analysis': f"Error analyzing sentiment: {str(e)}",
                'confidence': 'error'
            }
    
    def summarize_market_news(self, hours_back: int = 24) -> Dict:
        """Summarize recent market news"""
        try:
            logger.info(f"Summarizing market news from last {hours_back} hours...")
            
            # Search for recent news
            news_query = "market news financial developments economic indicators"
            relevant_docs = self.vector_store.search_similar(news_query, 15)
            
            if not relevant_docs:
                return {
                    'summary': 'No recent market news available for summarization',
                    'key_topics': [],
                    'sources_count': 0
                }
            
            # Get summary from LLM
            summary = self.llm_engine.summarize_market_news(relevant_docs)
            
            # Extract key topics (simple approach)
            key_topics = []
            summary_lower = summary.lower()
            topics = ['bitcoin', 'ethereum', 'crypto', 'stocks', 'fed', 'inflation', 'earnings']
            for topic in topics:
                if topic in summary_lower:
                    key_topics.append(topic)
            
            return {
                'summary': summary,
                'key_topics': key_topics,
                'sources_count': len(relevant_docs),
                'timeframe': f"Last {hours_back} hours"
            }
            
        except Exception as e:
            logger.error(f"Error in news summarization: {e}")
            return {
                'summary': f"Error summarizing news: {str(e)}",
                'key_topics': [],
                'sources_count': 0
            }
    
    def get_pipeline_stats(self) -> Dict:
        """Get statistics about the RAG pipeline"""
        try:
            index_stats = self.vector_store.get_index_stats()
            
            return {
                'vector_store': index_stats,
                'embedding_model': self.config.EMBEDDING_MODEL,
                'llm_model': self.config.OPENAI_MODEL,
                'rss_feeds_count': len(self.config.RSS_FEEDS),
                'chunk_size': self.config.CHUNK_SIZE,
                'chunk_overlap': self.config.CHUNK_OVERLAP
            }
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {'error': str(e)} 