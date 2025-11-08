import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from typing import List, Dict, Optional
import logging

from ..config import RAGConfig
from .embedder import TextEmbedder

logger = logging.getLogger(__name__)

class PineconeStore:
    def __init__(self):
        self.config = RAGConfig()
        self.embedder = TextEmbedder()
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        try:
            # Create Pinecone instance with new API
            self.pc = Pinecone(
                api_key=self.config.PINECONE_API_KEY
            )
            
            # Check if index exists, create if not
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.config.PINECONE_INDEX_NAME not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.config.PINECONE_INDEX_NAME}")
                
                # Try different regions for free tier compatibility
                regions_to_try = ['us-east-1', 'us-west-1', 'eu-west-1']
                
                for region in regions_to_try:
                    try:
                        self.pc.create_index(
                            name=self.config.PINECONE_INDEX_NAME,
                            dimension=self.config.VECTOR_DIMENSION,
                            metric=self.config.METRIC,
                            spec=ServerlessSpec(
                                cloud='aws',
                                region=region
                            )
                        )
                        logger.info(f"Successfully created index in region: {region}")
                        break
                    except Exception as region_error:
                        logger.warning(f"Failed to create index in {region}: {region_error}")
                        if region == regions_to_try[-1]:  # Last region attempt
                            raise region_error
            
            # Get the index
            self.index = self.pc.Index(self.config.PINECONE_INDEX_NAME)
            logger.info(f"Connected to Pinecone index: {self.config.PINECONE_INDEX_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def store_documents(self, documents: List[Document]) -> bool:
        """Store documents in Pinecone"""
        try:
            if not documents:
                logger.warning("No documents to store")
                return True
                
            # Create vectors to upsert
            vectors_to_upsert = []
            
            for i, doc in enumerate(documents):
                # Get embedding for the document
                embedding = self.embedder.embed_single_text(doc.page_content)
                
                # Create unique ID
                doc_id = doc.metadata.get('article_id', f"doc_{i}")
                
                # Prepare metadata
                metadata = doc.metadata.copy()
                metadata['text'] = doc.page_content[:1000]  # Limit text size for metadata
                
                vectors_to_upsert.append({
                    'id': str(doc_id),
                    'values': embedding,
                    'metadata': metadata
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1} with {len(batch)} vectors")
                
            return True
            
        except Exception as e:
            logger.error(f"Error storing documents: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            query_embedding = self.embedder.embed_single_text(query)
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            formatted_results = []
            for match in results.matches:
                if match.score >= self.config.SIMILARITY_THRESHOLD:
                    formatted_results.append({
                        'content': match.metadata.get('text', ''),
                        'metadata': match.metadata,
                        'score': match.score,
                        'id': match.id
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def store_articles(self, articles: List[Dict]) -> bool:
        """Store articles by converting them to documents first"""
        try:
            documents = self.embedder.chunk_articles(articles)
            return self.store_documents(documents)
        except Exception as e:
            logger.error(f"Error storing articles: {e}")
            return False
    
    def search_by_metadata(self, metadata_filter: Dict) -> List[Dict]:
        """Search documents by metadata filters"""
        try:
            # Create a dummy vector for metadata-only search
            dummy_vector = [0.0] * self.config.VECTOR_DIMENSION
            
            results = self.index.query(
                vector=dummy_vector,
                top_k=100,
                include_metadata=True,
                filter=metadata_filter
            )
            
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    'content': match.metadata.get('text', ''),
                    'metadata': match.metadata,
                    'score': match.score,
                    'id': match.id
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []
    
    def delete_by_metadata(self, metadata_filter: Dict) -> bool:
        """Delete documents by metadata filters"""
        try:
            # Find documents to delete
            documents_to_delete = self.search_by_metadata(metadata_filter)
            
            if not documents_to_delete:
                logger.info("No documents found to delete")
                return True
            
            # Delete by IDs
            ids_to_delete = [doc['id'] for doc in documents_to_delete if doc.get('id')]
            
            if ids_to_delete:
                self.index.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the Pinecone index"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {
                'total_vector_count': 0,
                'dimension': 0,
                'index_fullness': 0,
                'namespaces': {},
                'error': str(e)
            } 