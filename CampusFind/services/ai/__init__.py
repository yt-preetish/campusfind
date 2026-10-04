"""
CampusFind AI Services - Multimodal AI Engine

This package provides modular AI services for:
- Vision (image analysis)
- Embeddings (image and text)
- Matching (multimodal matching)
- OCR (text extraction with privacy)
- Semantic Search (conversational search)
- Assistant (AI recovery assistant)
- Anomaly (duplicate detection, risk analysis)
- Recommendations (personalized feed)
- Confidence (confidence engine)

All services support fallback to local implementations when external APIs are unavailable.
"""

from .vision import VisionAnalyzer
from .embeddings import EmbeddingService
from .matching import MultimodalMatcher
from .ocr import OCRService
from .semantic_search import SemanticSearch
from .assistant import AIAssistant
from .anomaly import AnomalyDetector
from .recommendations import RecommendationEngine
from .confidence import ConfidenceEngine

__all__ = [
    'VisionAnalyzer',
    'EmbeddingService',
    'MultimodalMatcher',
    'OCRService',
    'SemanticSearch',
    'AIAssistant',
    'AnomalyDetector',
    'RecommendationEngine',
    'ConfidenceEngine'
]
