"""
Multimodal Matcher - Advanced matching engine with explainable AI.

Provides:
- Multimodal scoring (image, text, location, date, category, OCR)
- Configurable weights
- Explainable matching with evidence
- Temporal reasoning
- Location intelligence
- Model versioning
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np
import config


class MultimodalMatcher:
    """Advanced multimodal matching engine."""
    
    def __init__(self):
        self.weights = config.AIConfig.get_matching_weights()
        self.model_version = config.AIConfig.MATCHING_ENGINE_VERSION
        self.confidence_thresholds = {
            "high": config.AIConfig.CONFIDENCE_THRESHOLD_HIGH,
            "medium": config.AIConfig.CONFIDENCE_THRESHOLD_MEDIUM,
            "low": config.AIConfig.CONFIDENCE_THRESHOLD_LOW
        }
    
    def match_items(self, item_a: Dict, item_b: Dict, 
                   image_embedding_service=None,
                   text_embedding_service=None) -> Dict:
        """
        Calculate multimodal match score between two items.
        
        Args:
            item_a: First item dictionary
            item_b: Second item dictionary
            image_embedding_service: Optional embedding service for image similarity
            text_embedding_service: Optional embedding service for text similarity
            
        Returns:
            dict: Match result with scores, breakdown, and explanation
        """
        # Calculate individual component scores
        scores = {}
        evidence = []
        uncertainties = []
        
        # Image similarity
        scores["image"] = self._calculate_image_similarity(
            item_a, item_b, image_embedding_service
        )
        if scores["image"] > 0.7:
            evidence.append("Similar visual appearance")
        elif scores["image"] > 0:
            uncertainties.append("Image similarity moderate")
        
        # Text semantic similarity
        scores["text_semantics"] = self._calculate_text_semantic_similarity(
            item_a, item_b, text_embedding_service
        )
        if scores["text_semantics"] > 0.7:
            evidence.append("Semantic text similarity")
        
        # Visual attributes (color, brand, features)
        scores["visual_attributes"] = self._calculate_visual_attribute_similarity(item_a, item_b)
        if scores["visual_attributes"] > 0.7:
            evidence.append("Similar visual attributes")
        
        # OCR similarity
        scores["ocr"] = self._calculate_ocr_similarity(item_a, item_b)
        if scores["ocr"] > 0.7:
            evidence.append("Similar visible text")
        
        # Category match
        scores["category"] = self._calculate_category_similarity(item_a, item_b)
        if scores["category"] == 100:
            evidence.append("Same item category")
        
        # Location similarity with intelligence
        scores["location"] = self._calculate_location_similarity(item_a, item_b)
        if scores["location"] > 0.7:
            evidence.append("Nearby location")
        elif scores["location"] > 0:
            uncertainties.append("Location approximate")
        
        # Date/time similarity with temporal reasoning
        scores["date_time"] = self._calculate_temporal_similarity(item_a, item_b)
        if scores["date_time"] > 0.7:
            evidence.append("Reports close in time")
        elif scores["date_time"] > 0:
            uncertainties.append("Time difference notable")
        
        # Brand/features similarity
        scores["brand_features"] = self._calculate_brand_feature_similarity(item_a, item_b)
        if scores["brand_features"] > 0.7:
            evidence.append("Similar brand or features")
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(scores)
        
        # Calculate confidence (separate from similarity)
        confidence = self._calculate_confidence(scores, overall_score, uncertainties)
        
        # Generate explanation
        explanation = self._generate_explanation(scores, evidence, uncertainties)
        
        return {
            "overall_score": round(overall_score * 100, 1),
            "confidence": round(confidence * 100, 1),
            "confidence_level": self._get_confidence_level(confidence),
            "breakdown": {k: round(v * 100, 1) for k, v in scores.items()},
            "evidence": evidence,
            "uncertainties": uncertainties,
            "explanation": explanation,
            "model_version": self.model_version,
            "weights_used": self.weights
        }
    
    def _calculate_image_similarity(self, item_a: Dict, item_b: Dict, 
                                   embedding_service=None) -> float:
        """Calculate image similarity using embeddings."""
        if not embedding_service:
            return 0.0
        
        try:
            img_a = item_a.get("image")
            img_b = item_b.get("image")
            
            if not img_a or not img_b:
                return 0.0
            
            # Get embeddings
            emb_a = embedding_service.get_image_embedding(img_a)
            emb_b = embedding_service.get_image_embedding(img_b)
            
            if emb_a is None or emb_b is None:
                return 0.0
            
            # Calculate cosine similarity
            similarity = embedding_service.cosine_similarity(emb_a, emb_b)
            return similarity
        except Exception as e:
            print(f"Image similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_text_semantic_similarity(self, item_a: Dict, item_b: Dict,
                                          embedding_service=None) -> float:
        """Calculate semantic text similarity using embeddings."""
        if not embedding_service:
            # Fallback to basic text similarity
            return self._basic_text_similarity(item_a, item_b) / 100.0
        
        try:
            # Combine text fields
            text_a = f"{item_a.get('title', '')} {item_a.get('description', '')} {item_a.get('category', '')}"
            text_b = f"{item_b.get('title', '')} {item_b.get('description', '')} {item_b.get('category', '')}"
            
            if not text_a.strip() or not text_b.strip():
                return 0.0
            
            # Get embeddings
            emb_a = embedding_service.get_text_embedding(text_a)
            emb_b = embedding_service.get_text_embedding(text_b)
            
            if emb_a is None or emb_b is None:
                return self._basic_text_similarity(item_a, item_b) / 100.0
            
            # Calculate cosine similarity
            similarity = embedding_service.cosine_similarity(emb_a, emb_b)
            return similarity
        except Exception as e:
            print(f"Text semantic similarity failed: {e}")
            return self._basic_text_similarity(item_a, item_b) / 100.0
    
    def _basic_text_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """Basic token-based text similarity as fallback."""
        def token_set(text):
            return set(re.findall(r"[a-z0-9]+", (text or "").lower()))
        
        text_a = f"{item_a.get('title', '')} {item_a.get('description', '')} {item_a.get('category', '')}"
        text_b = f"{item_b.get('title', '')} {item_b.get('description', '')} {item_b.get('category', '')}"
        
        A, B = token_set(text_a), token_set(text_b)
        if not A or not B:
            return 0.0
        
        similarity = len(A & B) / len(A | B)
        return similarity * 100
    
    def _calculate_visual_attribute_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """Calculate similarity of visual attributes (color, brand, features)."""
        score = 0.0
        components = 0
        
        # Color similarity
        color_a = item_a.get("color", "").lower()
        color_b = item_b.get("color", "").lower()
        if color_a and color_b:
            colors_a = set(color_a.split())
            colors_b = set(color_b.split())
            if colors_a & colors_b:
                score += 0.4
            components += 1
        
        # Brand similarity
        brand_a = item_a.get("brand", "").lower()
        brand_b = item_b.get("brand", "").lower()
        if brand_a and brand_b:
            if brand_a == brand_b:
                score += 0.4
            components += 1
        
        # Features similarity
        features_a = item_a.get("visual_features", "").lower()
        features_b = item_b.get("visual_features", "").lower()
        if features_a and features_b:
            feat_a = set(features_a.split(","))
            feat_b = set(features_b.split(","))
            if feat_a & feat_b:
                score += 0.2 * (len(feat_a & feat_b) / max(len(feat_a), len(feat_b)))
            components += 1
        
        return score if components > 0 else 0.0
    
    def _calculate_ocr_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """Calculate similarity of OCR-detected text."""
        ocr_a = item_a.get("ocr_text", "").lower()
        ocr_b = item_b.get("ocr_text", "").lower()
        
        if not ocr_a or not ocr_b:
            return 0.0
        
        # Token overlap
        tokens_a = set(re.findall(r"[a-z0-9]+", ocr_a))
        tokens_b = set(re.findall(r"[a-z0-9]+", ocr_b))
        
        if not tokens_a or not tokens_b:
            return 0.0
        
        similarity = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        return similarity
    
    def _calculate_category_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """Calculate category similarity (exact match only)."""
        cat_a = item_a.get("category", "").lower()
        cat_b = item_b.get("category", "").lower()
        
        return 1.0 if cat_a == cat_b else 0.0
    
    def _calculate_location_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """
        Calculate location similarity with intelligence.
        Understands campus location synonyms and proximity.
        """
        loc_a = item_a.get("location", "").lower()
        loc_b = item_b.get("location", "").lower()
        
        if not loc_a or not loc_b:
            return 0.0
        
        # Exact match
        if loc_a == loc_b:
            return 1.0
        
        # Check for location synonyms
        synonyms = {
            "cse": ["computer science", "cse block", "cse building", "cs block"],
            "library": ["central library", "library building", "main library"],
            "cafeteria": ["canteen", "food court", "mess"],
            "ece": ["electronics", "ece block", "ece building"],
            "mech": ["mechanical", "mech block", "mech building"]
        }
        
        # Check if locations are synonyms
        for key, values in synonyms.items():
            if key in loc_a and any(v in loc_b for v in values):
                return 0.9
            if key in loc_b and any(v in loc_a for v in values):
                return 0.9
        
        # Partial match
        words_a = set(loc_a.split())
        words_b = set(loc_b.split())
        overlap = len(words_a & words_b)
        
        if overlap > 0:
            return 0.6
        
        return 0.0
    
    def _calculate_temporal_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """
        Calculate temporal similarity with reasoning.
        Considers time proximity and plausibility.
        """
        try:
            dt_a = datetime.fromisoformat(item_a.get("date_time", ""))
            dt_b = datetime.fromisoformat(item_b.get("date_time", ""))
            
            diff = abs((dt_a - dt_b).total_seconds())
            
            # Same day (within 24 hours)
            if diff <= 86400:
                # Same day is highly plausible
                if diff <= 3600:  # Within 1 hour
                    return 1.0
                elif diff <= 14400:  # Within 4 hours
                    return 0.9
                else:
                    return 0.8
            # Within 2 days
            elif diff <= 172800:
                return 0.6
            # Within 1 week
            elif diff <= 604800:
                return 0.3
            # More than 1 week - less plausible
            else:
                return 0.1
        except:
            return 0.0
    
    def _calculate_brand_feature_similarity(self, item_a: Dict, item_b: Dict) -> float:
        """Calculate similarity based on brand and distinctive features."""
        score = 0.0
        
        # Brand match
        brand_a = item_a.get("brand", "").lower()
        brand_b = item_b.get("brand", "").lower()
        if brand_a and brand_b and brand_a == brand_b:
            score += 0.6
        
        # Distinctive features
        features_a = item_a.get("visual_features", "").lower()
        features_b = item_b.get("visual_features", "").lower()
        if features_a and features_b:
            feat_a = set(features_a.split(","))
            feat_b = set(features_b.split(","))
            overlap = len(feat_a & feat_b)
            if overlap > 0:
                score += 0.4 * (overlap / max(len(feat_a), len(feat_b)))
        
        return score
    
    def _calculate_weighted_score(self, scores: Dict) -> float:
        """Calculate weighted overall score from component scores."""
        weighted_sum = 0.0
        for component, weight in self.weights.items():
            weighted_sum += scores.get(component, 0.0) * weight
        return weighted_sum
    
    def _calculate_confidence(self, scores: Dict, overall_score: float, 
                             uncertainties: List) -> float:
        """
        Calculate confidence score (separate from similarity).
        Considers evidence quality and uncertainties.
        """
        confidence = overall_score
        
        # Reduce confidence based on uncertainties
        for uncertainty in uncertainties:
            confidence -= 0.05
        
        # Boost confidence if multiple strong signals
        strong_signals = sum(1 for v in scores.values() if v > 0.7)
        if strong_signals >= 3:
            confidence += 0.1
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label."""
        if confidence >= self.confidence_thresholds["high"]:
            return "HIGH"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "MEDIUM"
        elif confidence >= self.confidence_thresholds["low"]:
            return "LOW"
        else:
            return "VERY LOW"
    
    def _generate_explanation(self, scores: Dict, evidence: List, 
                              uncertainties: List) -> str:
        """Generate human-readable explanation."""
        if not evidence:
            return "These reports have limited similarities and require manual verification."
        
        explanation = "These reports may refer to the same item because:\n"
        explanation += "\n".join(f"✓ {e}" for e in evidence)
        
        if uncertainties:
            explanation += "\n\nHowever:\n"
            explanation += "\n".join(f"⚠ {u}" for u in uncertainties)
        
        return explanation
