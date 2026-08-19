"""
Embedding service for generating vector embeddings locally.
"""
import logging
from typing import List, Optional, Union
import numpy as np

from src.shared.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using local models.
    """
    
    _instance: Optional["EmbeddingService"] = None
    _model = None
    
    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.model_name = "all-MiniLM-L6-v2"
        self.dimension = 384
        self._load_model()
        
        self._initialized = True
        logger.info(f"Embedding service initialized with model: {self.model_name}")
    
    def _load_model(self):
        """
        Load the sentence transformer model.
        """
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback TF-IDF")
            self._model = None
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self._model = None
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self._model is not None:
            try:
                embeddings = self._model.encode(
                    texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=False,
                )
                return embeddings
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
        
        # Fallback to simple TF-IDF-like embedding
        return self._fallback_encode(texts)
    
    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """
        Fallback embedding method using character n-grams.
        """
        embeddings = np.zeros((len(texts), self.dimension))
        
        for i, text in enumerate(texts):
            # Simple hash-based embedding
            text_lower = text.lower()
            
            # Character n-grams
            for n in range(2, 5):
                for j in range(len(text_lower) - n + 1):
                    ngram = text_lower[j:j+n]
                    hash_val = hash(ngram) % self.dimension
                    embeddings[i, hash_val] += 1
            
            # Word presence
            for word in text_lower.split():
                hash_val = hash(word) % self.dimension
                embeddings[i, hash_val] += 1
            
            # Normalize
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm
        
        return embeddings
    
    def encode_single(self, text: str) -> List[float]:
        """
        Encode a single text and return as list.
        """
        embedding = self.encode(text)
        return embedding[0].tolist()
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """
        Encode a batch of texts.
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.encode(batch)
            embeddings.extend(batch_embeddings.tolist())
        
        return embeddings
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
    ) -> List[tuple[int, float]]:
        """
        Find most similar texts from candidates.
        Returns list of (index, similarity_score).
        """
        query_embedding = self.encode_single(query)
        candidate_embeddings = self.encode_batch(candidates)
        
        similarities = []
        for i, cand_emb in enumerate(candidate_embeddings):
            sim = self.compute_similarity(query_embedding, cand_emb)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model."""
        return self.model_name