import numpy as np
import pickle
import os
from typing import List, Dict, Optional
import logging
from langchain.schema import Document
from sklearn.metrics.pairwise import cosine_similarity

from ..config import RAGConfig
from .embedder import TextEmbedder

logger = logging.getLogger(__name__)

class LocalVectorStore:
    """Local vector store implementation for development/testing without Pinecone"""
    
    def __init__(self, storage_path: str = "local_vector_store.pkl"):
        self.config = RAGConfig()
        self.embedder = TextEmbedder()
        self.storage_path = storage_path
        self.vectors = {}  # {id: {'vector': np.array, 'metadata': dict, 'content': str}}
        self._load_from_disk()
        logger.info("Local vector store initialized")
    
    def _load_from_disk(self):
        """Load vectors from disk if file exists"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    self.vectors = pickle.load(f)
                logger.info(f"Loaded {len(self.vectors)} vectors from {self.storage_path}")
            except Exception as e:
                logger.warning(f"Could not load vectors from disk: {e}")
                self.vectors = {}
    
    def _save_to_disk(self):
        """Save vectors to disk"""
        try:
            with open(self.storage_path, 'wb') as f:
                pickle.dump(self.vectors, f)
            logger.info(f"Saved {len(self.vectors)} vectors to {self.storage_path}")
        except Exception as e:
            logger.error(f"Could not save vectors to disk: {e}")
    
    def store_documents(self, documents: List[Document]) -> bool:
        """Store documents in local vector store"""
        try:
            if not documents:
                logger.warning("No documents to store")
                return True
            
            for i, doc in enumerate(documents):
                # Get embedding for the document
                embedding = self.embedder.embed_single_text(doc.page_content)
                
                # Create unique ID
                doc_id = doc.metadata.get('article_id', f"doc_{len(self.vectors)}_{i}")
                
                # Store vector with metadata
                self.vectors[str(doc_id)] = {
                    'vector': np.array(embedding),
                    'metadata': doc.metadata,
                    'content': doc.page_content
                }
            
            self._save_to_disk()
            logger.info(f"Stored {len(documents)} documents. Total vectors: {len(self.vectors)}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing documents: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        try:
            if not self.vectors:
                logger.warning("No vectors in store")
                return []
            
            # Get query embedding
            query_embedding = np.array(self.embedder.embed_single_text(query))
            
            # Calculate similarities
            similarities = []
            for doc_id, doc_data in self.vectors.items():
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    doc_data['vector'].reshape(1, -1)
                )[0][0]
                
                if similarity >= self.config.SIMILARITY_THRESHOLD:
                    similarities.append({
                        'id': doc_id,
                        'score': float(similarity),
                        'content': doc_data['content'],
                        'metadata': doc_data['metadata']
                    })
            
            # Sort by similarity score (descending)
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            return similarities[:top_k]
            
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
            results = []
            
            for doc_id, doc_data in self.vectors.items():
                # Check if all filter criteria match
                match = True
                for key, value in metadata_filter.items():
                    if key not in doc_data['metadata'] or doc_data['metadata'][key] != value:
                        match = False
                        break
                
                if match:
                    results.append({
                        'id': doc_id,
                        'content': doc_data['content'],
                        'metadata': doc_data['metadata'],
                        'score': 1.0  # Perfect match for metadata filtering
                    })
            
            return results
            
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
            
            # Delete documents
            for doc in documents_to_delete:
                if doc['id'] in self.vectors:
                    del self.vectors[doc['id']]
            
            self._save_to_disk()
            logger.info(f"Deleted {len(documents_to_delete)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the local vector store"""
        try:
            return {
                'total_vector_count': len(self.vectors),
                'dimension': self.config.VECTOR_DIMENSION,
                'index_fullness': 0.0,  # Not applicable for local store
                'namespaces': {'default': len(self.vectors)},
                'storage_path': self.storage_path,
                'storage_size_mb': os.path.getsize(self.storage_path) / (1024*1024) if os.path.exists(self.storage_path) else 0
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
    
    def clear_all(self) -> bool:
        """Clear all vectors from the store"""
        try:
            self.vectors = {}
            self._save_to_disk()
            logger.info("Cleared all vectors from local store")
            return True
        except Exception as e:
            logger.error(f"Error clearing vectors: {e}")
            return False 