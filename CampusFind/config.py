"""
Centralized configuration for CampusFind AI system.
Load all configuration from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class AIConfig:
    """AI configuration loaded from environment variables."""
    
    # AI Provider Selection
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")  # openai, local, hybrid
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
    
    # Embedding Configuration
    EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")  # openai, local_clip, sentence_transformers
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # OCR Configuration
    OCR_PROVIDER = os.environ.get("OCR_PROVIDER", "tesseract")  # tesseract, openai, easyocr
    OCR_ENABLED = os.environ.get("OCR_ENABLED", "true").lower() == "true"
    
    # Matching Weights (configurable)
    MATCHING_WEIGHTS = {
        "image": float(os.environ.get("WEIGHT_IMAGE", "0.30")),
        "text_semantics": float(os.environ.get("WEIGHT_TEXT_SEMANTICS", "0.20")),
        "visual_attributes": float(os.environ.get("WEIGHT_VISUAL_ATTRIBUTES", "0.10")),
        "ocr": float(os.environ.get("WEIGHT_OCR", "0.10")),
        "category": float(os.environ.get("WEIGHT_CATEGORY", "0.10")),
        "location": float(os.environ.get("WEIGHT_LOCATION", "0.10")),
        "date_time": float(os.environ.get("WEIGHT_DATE_TIME", "0.05")),
        "brand_features": float(os.environ.get("WEIGHT_BRAND_FEATURES", "0.05"))
    }
    
    # Confidence Thresholds
    CONFIDENCE_THRESHOLD_HIGH = float(os.environ.get("CONFIDENCE_THRESHOLD_HIGH", "0.85"))
    CONFIDENCE_THRESHOLD_MEDIUM = float(os.environ.get("CONFIDENCE_THRESHOLD_MEDIUM", "0.70"))
    CONFIDENCE_THRESHOLD_LOW = float(os.environ.get("CONFIDENCE_THRESHOLD_LOW", "0.50"))
    
    # Model Versioning
    VISION_MODEL_VERSION = os.environ.get("VISION_MODEL_VERSION", "1.0")
    EMBEDDING_MODEL_VERSION = os.environ.get("EMBEDDING_MODEL_VERSION", "1.0")
    MATCHING_ENGINE_VERSION = os.environ.get("MATCHING_ENGINE_VERSION", "2.0")
    
    # Privacy Settings
    PRIVACY_MASK_SENSITIVE = os.environ.get("PRIVACY_MASK_SENSITIVE", "true").lower() == "true"
    PRIVACY_EXPOSE_OCR = os.environ.get("PRIVACY_EXPOSE_OCR", "false").lower() == "true"
    
    # Performance Settings
    MAX_CANDIDATE_RETRIEVAL = int(os.environ.get("MAX_CANDIDATE_RETRIEVAL", "50"))
    MAX_MATCH_RESULTS = int(os.environ.get("MAX_MATCH_RESULTS", "10"))
    ENABLE_EMBEDDING_CACHE = os.environ.get("ENABLE_EMBEDDING_CACHE", "true").lower() == "true"
    
    # Fallback Settings
    FALLBACK_LEVEL = os.environ.get("FALLBACK_LEVEL", "auto")  # auto, level1, level2, level3
    ENABLE_LOCAL_FALLBACK = os.environ.get("ENABLE_LOCAL_FALLBACK", "true").lower() == "true"
    
    @classmethod
    def is_ai_available(cls):
        """Check if external AI services are available."""
        return bool(cls.OPENAI_API_KEY)
    
    @classmethod
    def get_matching_weights(cls):
        """Get matching weights, ensuring they sum to 1.0."""
        weights = cls.MATCHING_WEIGHTS.copy()
        total = sum(weights.values())
        if total != 1.0:
            # Normalize weights
            weights = {k: v / total for k, v in weights.items()}
        return weights


class AppConfig:
    """General application configuration."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "campusfind-dev-secret-change-me")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
