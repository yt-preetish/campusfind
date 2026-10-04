"""
Embedding Service - Image and text embeddings for semantic similarity.

Provides:
- Image embeddings using CLIP or OpenAI Vision
- Text embeddings using OpenAI or sentence-transformers
- Cosine similarity calculation
- Embedding caching
- Multi-provider support with fallback
"""
import os
import json
import numpy as np
from datetime import datetime
from typing import List, Tuple, Optional
import config


class EmbeddingService:
    """Embedding service with multi-provider support."""
    
    def __init__(self):
        self.provider = config.AIConfig.EMBEDDING_PROVIDER
        self.api_key = config.AIConfig.OPENAI_API_KEY
        self.model = config.AIConfig.EMBEDDING_MODEL
        self.model_version = config.AIConfig.EMBEDDING_MODEL_VERSION
        self.cache_enabled = config.AIConfig.ENABLE_EMBEDDING_CACHE
        self._embedding_cache = {}
        
        # Lazy-load providers
        self._openai_client = None
        self._clip_model = None
        self._clip_processor = None
    
    def get_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Generate embedding for an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            numpy array: Image embedding vector
        """
        # Check cache
        if self.cache_enabled:
            cache_key = f"img_{image_path}_{self.model_version}"
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]
        
        try:
            if self.provider == "openai" and self.api_key:
                embedding = self._get_openai_image_embedding(image_path)
            elif self.provider == "local_clip":
                embedding = self._get_clip_image_embedding(image_path)
            else:
                # Fallback to basic feature extraction
                embedding = self._get_basic_image_features(image_path)
            
            # Cache result
            if self.cache_enabled and embedding is not None:
                self._embedding_cache[cache_key] = embedding
            
            return embedding
        except Exception as e:
            print(f"Image embedding failed: {e}, using fallback")
            return self._get_basic_image_features(image_path)
    
    def get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for text.
        
        Args:
            text: Text string
            
        Returns:
            numpy array: Text embedding vector
        """
        if not text or not text.strip():
            return None
        
        # Check cache
        if self.cache_enabled:
            cache_key = f"text_{hash(text)}_{self.model_version}"
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]
        
        try:
            if self.provider == "openai" and self.api_key:
                embedding = self._get_openai_text_embedding(text)
            elif self.provider == "sentence_transformers":
                embedding = self._get_sentence_transformer_embedding(text)
            else:
                # Fallback to basic token-based embedding
                embedding = self._get_basic_text_features(text)
            
            # Cache result
            if self.cache_enabled and embedding is not None:
                self._embedding_cache[cache_key] = embedding
            
            return embedding
        except Exception as e:
            print(f"Text embedding failed: {e}, using fallback")
            return self._get_basic_text_features(text)
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(max(0, min(1, similarity)))
        except:
            return 0.0
    
    def batch_cosine_similarity(self, query_embedding: np.ndarray, 
                                candidate_embeddings: List[np.ndarray]) -> List[float]:
        """
        Calculate cosine similarity between query and multiple candidates.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            
        Returns:
            list: Similarity scores
        """
        if query_embedding is None:
            return [0.0] * len(candidate_embeddings)
        
        similarities = []
        for emb in candidate_embeddings:
            similarities.append(self.cosine_similarity(query_embedding, emb))
        return similarities
    
    def _get_openai_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Get image embedding using OpenAI Vision API."""
        try:
            from openai import OpenAI
            if self._openai_client is None:
                self._openai_client = OpenAI(api_key=self.api_key)
            
            # Read and encode image
            import base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self._openai_client.images.embed.create(
                model="image-embedding-alpha",  # Use appropriate model
                image=f"data:image/jpeg;base64,{base64_image}"
            )
            
            embedding = np.array(response.embedding)
            return embedding
        except Exception as e:
            print(f"OpenAI image embedding failed: {e}")
            return None
    
    def _get_clip_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Get image embedding using CLIP model."""
        try:
            from PIL import Image
            if self._clip_model is None:
                import clip
                device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
                self._clip_model, self._clip_processor = clip.load("ViT-B/32", device=device)
            
            image = Image.open(image_path)
            image_input = self._clip_processor(image).unsqueeze(0)
            
            with torch.no_grad():
                image_features = self._clip_model.encode_image(image_input)
            
            return image_features.cpu().numpy().flatten()
        except Exception as e:
            print(f"CLIP embedding failed: {e}")
            return None
    
    def _get_openai_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get text embedding using OpenAI API."""
        try:
            from openai import OpenAI
            if self._openai_client is None:
                self._openai_client = OpenAI(api_key=self.api_key)
            
            response = self._openai_client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = np.array(response.data[0].embedding)
            return embedding
        except Exception as e:
            print(f"OpenAI text embedding failed: {e}")
            return None
    
    def _get_sentence_transformer_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get text embedding using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            if self._clip_model is None:
                self._clip_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self._clip_model.encode(text)
            return np.array(embedding)
        except Exception as e:
            print(f"Sentence transformer embedding failed: {e}")
            return None
    
    def _get_basic_image_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Basic image feature extraction as fallback.
        Uses color histogram and basic image statistics.
        """
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(image_path)
            img = img.resize((64, 64))  # Downsample for efficiency
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Flatten and normalize
            if len(img_array.shape) == 3:
                features = img_array.flatten() / 255.0
            else:
                features = img_array.flatten() / 255.0
            
            return features
        except Exception as e:
            print(f"Basic image features failed: {e}")
            return None
    
    def _get_basic_text_features(self, text: str) -> Optional[np.ndarray]:
        """
        Basic text feature extraction as fallback.
        Uses character n-grams and word statistics.
        """
        try:
            import numpy as np
            
            # Character n-grams (2-grams)
            ngrams = []
            for i in range(len(text) - 1):
                ngrams.append(text[i:i+2])
            
            # Create feature vector from n-gram frequencies
            feature_dict = {}
            for ngram in ngrams:
                feature_dict[ngram] = feature_dict.get(ngram, 0) + 1
            
            # Convert to fixed-size vector (first 100 features)
            features = np.zeros(100)
            for i, (ngram, count) in enumerate(sorted(feature_dict.items())[:100]):
                features[i] = count
            
            # Normalize
            if np.sum(features) > 0:
                features = features / np.sum(features)
            
            return features
        except Exception as e:
            print(f"Basic text features failed: {e}")
            return None
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
