"""
ChromaDB implementation of conversation memory repository for RAG.
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.domain.repositories.base_repository import BaseRepository
from src.infrastructure.database.vector_store.chroma_client import ChromaClient, ConversationMemoryStore
from src.infrastructure.database.vector_store.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ChromaMemoryRepository:
    """
    Repository for managing conversation memory using ChromaDB.
    Implements RAG (Retrieval Augmented Generation) storage and retrieval.
    """
    
    def __init__(
        self,
        chroma_client: Optional[ChromaClient] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.chroma = chroma_client or ChromaClient()
        self.embedding_service = embedding_service or EmbeddingService()
        self.memory_store = ConversationMemoryStore(self.chroma, self.embedding_service)
        self.collection_prefix = "conversation_"
    
    async def add_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to conversation memory for future retrieval.
        """
        await self.memory_store.add_message_to_memory(
            conversation_id=conversation_id,
            message_id=message_id,
            content=content,
            role=role,
            metadata=metadata,
        )
    
    async def add_document(
        self,
        conversation_id: UUID,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an external document to conversation memory (for document Q&A).
        """
        collection_name = f"{self.collection_prefix}{conversation_id}"
        
        # Chunk large documents
        chunks = self._chunk_document(content, max_chunk_size=1000, overlap=100)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                **(metadata or {}),
                "document_id": document_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_type": "document",
            })
            ids.append(f"{document_id}_chunk_{i}")
        
        self.chroma.add_documents(
            collection_name=collection_name,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        
        logger.info(f"Added document {document_id} ({len(chunks)} chunks) to conversation {conversation_id}")
    
    async def search(
        self,
        conversation_id: UUID,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search conversation memory for relevant content.
        Returns list of results with content, metadata, and relevance score.
        """
        collection_name = f"{self.collection_prefix}{conversation_id}"
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_single(query)
            
            # Build where clause for metadata filtering
            where = None
            if filter_metadata:
                where = {k: {"$eq": v} for k, v in filter_metadata.items()}
            
            # Query ChromaDB
            results = self.chroma.query_with_embeddings(
                collection_name=collection_name,
                query_embeddings=[query_embedding],
                n_results=limit * 2,  # Get more to filter by relevance
                where=where,
            )
            
            # Process and filter results
            processed_results = []
            
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    relevance = 1 - (distance / 2)  # Convert cosine distance to similarity
                    
                    if relevance >= min_relevance:
                        metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                        
                        processed_results.append({
                            "id": results["ids"][0][i],
                            "content": doc,
                            "metadata": metadata,
                            "relevance": relevance,
                            "distance": distance,
                        })
            
            # Sort by relevance
            processed_results.sort(key=lambda x: x["relevance"], reverse=True)
            
            # Merge chunks from same document
            merged_results = self._merge_document_chunks(processed_results[:limit])
            
            return merged_results
            
        except Exception as e:
            logger.error(f"Error searching memory for conversation {conversation_id}: {e}")
            return []
    
    async def search_semantic(
        self,
        conversation_id: UUID,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Search and return only the content strings (for LLM context).
        """
        results = await self.search(conversation_id, query, limit)
        return [r["content"] for r in results]
    
    async def get_relevant_context(
        self,
        conversation_id: UUID,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Get relevant context formatted for LLM consumption.
        """
        results = await self.search(conversation_id, query, limit=10, min_relevance=0.3)
        
        if not results:
            return ""
        
        context_parts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough estimate: 4 chars per token
        
        for result in results:
            content = result["content"]
            if total_chars + len(content) > char_limit:
                # Truncate last item to fit
                remaining = char_limit - total_chars
                if remaining > 100:
                    context_parts.append(content[:remaining] + "...")
                break
            
            context_parts.append(content)
            total_chars += len(content)
        
        return "\n\n---\n\n".join(context_parts)
    
    async def delete_conversation_memory(self, conversation_id: UUID) -> None:
        """
        Delete all memory for a conversation.
        """
        await self.memory_store.delete_conversation_memory(conversation_id)
    
    async def delete_document(
        self,
        conversation_id: UUID,
        document_id: str,
    ) -> None:
        """
        Delete a specific document from conversation memory.
        """
        collection_name = f"{self.collection_prefix}{conversation_id}"
        
        try:
            # Find all chunks for this document
            results = self.chroma.query(
                collection_name=collection_name,
                query_texts=[""],
                n_results=1000,
                where={"document_id": {"$eq": document_id}},
            )
            
            if results and results.get("ids"):
                ids_to_delete = results["ids"][0]
                self.chroma.delete_documents(collection_name, ids_to_delete)
                logger.info(f"Deleted document {document_id} ({len(ids_to_delete)} chunks)")
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
    
    async def get_memory_stats(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Get memory statistics for a conversation.
        """
        return await self.memory_store.get_memory_stats(conversation_id)
    
    async def list_documents(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        """
        List all documents in conversation memory.
        """
        collection_name = f"{self.collection_prefix}{conversation_id}"
        
        try:
            # Get all items
            results = self.chroma.get_by_ids(collection_name, [])
            
            if not results:
                return []
            
            # Extract unique documents
            documents = {}
            if results.get("metadatas"):
                for metadata in results["metadatas"]:
                    doc_id = metadata.get("document_id")
                    if doc_id and doc_id not in documents:
                        documents[doc_id] = {
                            "document_id": doc_id,
                            "source_type": metadata.get("source_type", "message"),
                            "total_chunks": metadata.get("total_chunks", 1),
                        }
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def _chunk_document(
        self,
        content: str,
        max_chunk_size: int = 1000,
        overlap: int = 100,
    ) -> List[str]:
        """
        Split document into overlapping chunks.
        """
        if len(content) <= max_chunk_size:
            return [content]
        
        chunks = []
        
        # Try to split on paragraph boundaries first
        paragraphs = content.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If paragraph itself is too long, split on sentences
                if len(para) > max_chunk_size:
                    sub_chunks = self._chunk_by_sentences(para, max_chunk_size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_sentences(
        self,
        text: str,
        max_size: int,
        overlap: int,
    ) -> List[str]:
        """
        Split text by sentences with overlap.
        """
        import re
        sentences = re.split(r"(?<=[.!?])\s+", text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Start new chunk with overlap from previous
                words = current_chunk.split()
                overlap_words = words[-overlap:] if overlap > 0 and len(words) > overlap else []
                current_chunk = " ".join(overlap_words) + " " + sentence if overlap_words else sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _merge_document_chunks(
        self,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge chunks from the same document into single results.
        """
        merged = {}
        
        for result in results:
            metadata = result.get("metadata", {})
            doc_id = metadata.get("document_id") or metadata.get("parent_message_id") or result["id"]
            
            if doc_id not in merged:
                merged[doc_id] = {
                    "id": doc_id,
                    "content": result["content"],
                    "metadata": metadata,
                    "relevance": result["relevance"],
                    "chunk_count": 1,
                }
            else:
                # Keep highest relevance score
                if result["relevance"] > merged[doc_id]["relevance"]:
                    merged[doc_id]["relevance"] = result["relevance"]
                    merged[doc_id]["content"] = result["content"]
                merged[doc_id]["chunk_count"] += 1
        
        return list(merged.values())
    
    async def clear_all_memory(self) -> None:
        """
        Clear all memory across all conversations (admin only).
        """
        collections = self.chroma.list_collections()
        for collection in collections:
            if collection.startswith(self.collection_prefix):
                self.chroma.delete_collection(collection)
        
        logger.info(f"Cleared {len(collections)} conversation memory collections")