"""
ChromaDB client wrapper for vector storage and retrieval.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.shared.config import settings

logger = logging.getLogger(__name__)


class ChromaClient:
    """
    ChromaDB client wrapper for managing vector embeddings.
    Used for RAG (Retrieval Augmented Generation) and semantic search.
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.VECTOR_STORE_PATH
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self._client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        self._collections: Dict[str, Any] = {}
        logger.info(f"ChromaDB initialized at {self.persist_directory}")
    
    def get_or_create_collection(self, name: str) -> Any:
        """
        Get or create a collection.
        """
        if name not in self._collections:
            try:
                self._collections[name] = self._client.get_collection(name)
            except Exception:
                self._collections[name] = self._client.create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"Created ChromaDB collection: {name}")
        
        return self._collections[name]
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """
        Add documents to a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        
        if ids is None:
            import hashlib
            ids = [
                hashlib.md5(f"{collection_name}_{i}_{doc[:50]}".encode()).hexdigest()
                for i, doc in enumerate(documents)
            ]
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
        
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
    
    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query documents from a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
        )
        
        return results
    
    def query_with_embeddings(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query using pre-computed embeddings.
        """
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
        )
        
        return results
    
    def get_by_ids(
        self,
        collection_name: str,
        ids: List[str],
    ) -> Dict[str, Any]:
        """
        Retrieve documents by IDs.
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.get(ids=ids)
    
    def update_document(
        self,
        collection_name: str,
        id: str,
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        """
        Update a document in the collection.
        """
        collection = self.get_or_create_collection(collection_name)
        
        collection.update(
            ids=[id],
            documents=[document] if document else None,
            metadatas=[metadata] if metadata else None,
            embeddings=[embedding] if embedding else None,
        )
    
    def delete_documents(
        self,
        collection_name: str,
        ids: List[str],
    ) -> None:
        """
        Delete documents from a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from collection '{collection_name}'")
    
    def delete_collection(self, name: str) -> None:
        """
        Delete an entire collection.
        """
        try:
            self._client.delete_collection(name)
            if name in self._collections:
                del self._collections[name]
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Error deleting collection '{name}': {e}")
    
    def list_collections(self) -> List[str]:
        """
        List all collections.
        """
        return [c.name for c in self._client.list_collections()]
    
    def count_documents(self, collection_name: str) -> int:
        """
        Count documents in a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.count()
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        """
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata,
        }


class ConversationMemoryStore:
    """
    Specialized vector store for conversation memory (RAG).
    """
    
    def __init__(self, chroma_client: ChromaClient, embedding_service):
        self.chroma = chroma_client
        self.embedding_service = embedding_service
        self.collection_prefix = "conversation_"
    
    def _get_collection_name(self, conversation_id: UUID) -> str:
        """Get collection name for a conversation."""
        return f"{self.collection_prefix}{conversation_id}"
    
    async def add_message_to_memory(
        self,
        conversation_id: UUID,
        message_id: UUID,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to conversation memory.
        """
        collection_name = self._get_collection_name(conversation_id)
        
        # Create metadata
        doc_metadata = {
            "message_id": str(message_id),
            "role": role,
            **(metadata or {}),
        }
        
        # Split long messages into chunks for better retrieval
        chunks = self._chunk_text(content, max_chunk_size=500, overlap=50)
        
        if len(chunks) == 1:
            self.chroma.add_documents(
                collection_name=collection_name,
                documents=[content],
                metadatas=[doc_metadata],
                ids=[str(message_id)],
            )
        else:
            # Add chunks with chunk metadata
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **doc_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "parent_message_id": str(message_id),
                }
                
                self.chroma.add_documents(
                    collection_name=collection_name,
                    documents=[chunk],
                    metadatas=[chunk_metadata],
                    ids=[f"{message_id}_chunk_{i}"],
                )
        
        logger.debug(f"Added message {message_id} to memory for conversation {conversation_id}")
    
    def _chunk_text(
        self,
        text: str,
        max_chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """
        Split text into overlapping chunks.
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word)
            
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Keep overlap words
                overlap_words = current_chunk[-overlap:] if overlap > 0 else []
                current_chunk = overlap_words.copy()
                current_size = sum(len(w) for w in current_chunk)
            
            current_chunk.append(word)
            current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def search_memory(
        self,
        conversation_id: UUID,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search conversation memory for relevant messages.
        """
        collection_name = self._get_collection_name(conversation_id)
        
        try:
            results = self.chroma.query(
                collection_name=collection_name,
                query_texts=[query],
                n_results=n_results,
            )
            
            formatted_results = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                        "id": results["ids"][0][i] if results.get("ids") else None,
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    async def delete_conversation_memory(self, conversation_id: UUID) -> None:
        """
        Delete all memory for a conversation.
        """
        collection_name = self._get_collection_name(conversation_id)
        self.chroma.delete_collection(collection_name)
        logger.info(f"Deleted memory for conversation {conversation_id}")
    
    async def get_memory_stats(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Get memory statistics for a conversation.
        """
        collection_name = self._get_collection_name(conversation_id)
        
        try:
            count = self.chroma.count_documents(collection_name)
            return {
                "conversation_id": str(conversation_id),
                "document_count": count,
                "collection_name": collection_name,
            }
        except Exception:
            return {
                "conversation_id": str(conversation_id),
                "document_count": 0,
                "collection_name": collection_name,
            }