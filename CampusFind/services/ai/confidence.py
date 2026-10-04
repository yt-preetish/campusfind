"""
Confidence Engine - Calculate confidence scores with uncertainty quantification.

Provides:
- Confidence score calculation
- Uncertainty quantification
- Evidence quality assessment
- Confidence level classification
- Explainable confidence
"""
from typing import Dict, List, Optional
import config


class ConfidenceEngine:
    """Calculate confidence scores with uncertainty quantification."""
    
    def __init__(self):
        self.thresholds = {
            "high": config.AIConfig.CONFIDENCE_THRESHOLD_HIGH,
            "medium": config.AIConfig.CONFIDENCE_THRESHOLD_MEDIUM,
            "low": config.AIConfig.CONFIDENCE_THRESHOLD_LOW
        }
    
    def calculate_confidence(self, similarity_scores: Dict, 
                            uncertainties: List[str],
                            evidence_quality: Dict = None) -> Dict:
        """
        Calculate confidence score separate from similarity.
        
        Args:
            similarity_scores: Component similarity scores
            uncertainties: List of uncertainty factors
            evidence_quality: Quality assessment of evidence
            
        Returns:
            dict: Confidence analysis with score, level, and explanation
        """
        # Start with weighted similarity
        weights = config.AIConfig.get_matching_weights()
        weighted_similarity = sum(
            similarity_scores.get(k, 0) * weights.get(k, 0) 
            for k in weights.keys()
        )
        
        confidence = weighted_similarity
        
        # Reduce confidence based on uncertainties
        uncertainty_penalty = len(uncertainties) * 0.05
        confidence -= uncertainty_penalty
        
        # Boost confidence based on evidence quality
        if evidence_quality:
            quality_boost = self._calculate_quality_boost(evidence_quality)
            confidence += quality_boost
        
        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))
        
        # Determine confidence level
        level = self._get_confidence_level(confidence)
        
        # Generate explanation
        explanation = self._generate_confidence_explanation(
            confidence, uncertainties, evidence_quality
        )
        
        return {
            "confidence_score": round(confidence * 100, 1),
            "confidence_level": level,
            "similarity_score": round(weighted_similarity * 100, 1),
            "uncertainty_penalty": round(uncertainty_penalty * 100, 1),
            "uncertainties": uncertainties,
            "explanation": explanation
        }
    
    def _calculate_quality_boost(self, evidence_quality: Dict) -> float:
        """Calculate confidence boost based on evidence quality."""
        boost = 0.0
        
        if evidence_quality.get("image_quality", "medium") == "high":
            boost += 0.05
        
        if evidence_quality.get("text_quality", "medium") == "high":
            boost += 0.05
        
        if evidence_quality.get("multiple_strong_signals", False):
            boost += 0.1
        
        if evidence_quality.get("verified_location", False):
            boost += 0.05
        
        return boost
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label."""
        if confidence >= self.thresholds["high"]:
            return "HIGH"
        elif confidence >= self.thresholds["medium"]:
            return "MEDIUM"
        elif confidence >= self.thresholds["low"]:
            return "LOW"
        else:
            return "VERY LOW"
    
    def _generate_confidence_explanation(self, confidence: float, 
                                         uncertainties: List,
                                         evidence_quality: Dict) -> str:
        """Generate human-readable confidence explanation."""
        level = self._get_confidence_level(confidence)
        
        explanation = f"Confidence level: {level} ({round(confidence * 100)}%).\n"
        
        if level == "HIGH":
            explanation += "Strong evidence supports this match with minimal uncertainty."
        elif level == "MEDIUM":
            explanation += "Moderate evidence with some uncertainty. Manual review recommended."
        elif level == "LOW":
            explanation += "Limited evidence with significant uncertainty. Manual verification required."
        else:
            explanation += "Very weak evidence. This match requires thorough verification."
        
        if uncertainties:
            explanation += "\n\nUncertainties:\n"
            explanation += "\n".join(f"• {u}" for u in uncertainties)
        
        return explanation
    
    def assess_evidence_quality(self, item: Dict) -> Dict:
        """
        Assess the quality of evidence for an item.
        
        Args:
            item: Item dictionary
            
        Returns:
            dict: Evidence quality assessment
        """
        quality = {
            "image_quality": "medium",
            "text_quality": "medium",
            "multiple_strong_signals": False,
            "verified_location": False
        }
        
        # Assess image quality
        if item.get("image"):
            # Could add actual image quality analysis here
            quality["image_quality"] = "medium"
        else:
            quality["image_quality"] = "none"
        
        # Assess text quality
        title = item.get("title", "")
        description = item.get("description", "")
        
        if len(title) > 5 and len(description) > 20:
            quality["text_quality"] = "high"
        elif len(title) > 3 and len(description) > 10:
            quality["text_quality"] = "medium"
        else:
            quality["text_quality"] = "low"
        
        # Check for multiple strong signals
        strong_signals = 0
        if item.get("color"):
            strong_signals += 1
        if item.get("brand"):
            strong_signals += 1
        if item.get("visual_features"):
            strong_signals += 1
        if item.get("image"):
            strong_signals += 1
        
        if strong_signals >= 3:
            quality["multiple_strong_signals"] = True
        
        # Check if location is specific
        location = item.get("location", "")
        if len(location) > 10 and any(word in location.lower() for word in ["block", "building", "floor", "room"]):
            quality["verified_location"] = True
        
        return quality
    
    def compare_similarity_vs_confidence(self, similarity: float, 
                                        confidence: float) -> Dict:
        """
        Compare raw similarity with calculated confidence.
        
        This is important for explainability - they should not always be equal.
        
        Args:
            similarity: Raw similarity score (0-1)
            confidence: Calculated confidence score (0-1)
            
        Returns:
            dict: Comparison analysis
        """
        diff = abs(similarity - confidence)
        
        if diff < 0.1:
            relationship = "Consistent"
        elif diff < 0.3:
            relationship = "Moderately adjusted"
        else:
            relationship = "Significantly adjusted"
        
        return {
            "similarity": round(similarity * 100, 1),
            "confidence": round(confidence * 100, 1),
            "difference": round(diff * 100, 1),
            "relationship": relationship,
            "explanation": self._explain_difference(similarity, confidence, diff)
        }
    
    def _explain_difference(self, similarity: float, confidence: float, 
                          diff: float) -> str:
        """Explain why confidence differs from similarity."""
        if diff < 0.1:
            return "Confidence closely matches similarity. Evidence quality is good."
        elif confidence < similarity:
            return "Confidence lower than similarity due to uncertainties or weak evidence quality."
        else:
            return "Confidence higher than similarity due to strong evidence quality or multiple confirming signals."
