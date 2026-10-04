"""
Anomaly Detector - Duplicate detection and claim risk analysis.

Provides:
- Duplicate report detection
- Claim risk analysis
- Suspicious activity detection
- Fraud flagging
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import config


class AnomalyDetector:
    """Detect anomalies and potential issues in reports and claims."""
    
    def __init__(self):
        self.duplicate_threshold = 0.85
        self.risk_threshold_high = 0.8
        self.risk_threshold_medium = 0.5
    
    def detect_duplicate_report(self, new_report: Dict, existing_reports: List[Dict],
                              embedding_service=None) -> List[Dict]:
        """
        Detect potential duplicate reports.
        
        Args:
            new_report: New report to check
            existing_reports: List of existing reports
            embedding_service: Optional embedding service for similarity
            
        Returns:
            list: Potential duplicates with similarity scores
        """
        duplicates = []
        
        for existing in existing_reports:
            # Skip if same user (could be update, not duplicate)
            if existing.get("user_id") == new_report.get("user_id"):
                continue
            
            # Skip if different type (lost vs found)
            if existing.get("type") != new_report.get("type"):
                continue
            
            similarity = self._calculate_report_similarity(new_report, existing, embedding_service)
            
            if similarity >= self.duplicate_threshold:
                duplicates.append({
                    "existing_report": existing,
                    "similarity": round(similarity * 100, 1),
                    "reason": self._generate_duplicate_reason(new_report, existing)
                })
        
        # Sort by similarity
        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates
    
    def _calculate_report_similarity(self, report_a: Dict, report_b: Dict,
                                   embedding_service=None) -> float:
        """Calculate similarity between two reports."""
        score = 0.0
        
        # Title similarity
        title_a = report_a.get("title", "").lower()
        title_b = report_b.get("title", "").lower()
        title_sim = self._text_similarity(title_a, title_b)
        score += title_sim * 0.3
        
        # Description similarity
        desc_a = report_a.get("description", "").lower()
        desc_b = report_b.get("description", "").lower()
        desc_sim = self._text_similarity(desc_a, desc_b)
        score += desc_sim * 0.3
        
        # Location match
        loc_a = report_a.get("location", "").lower()
        loc_b = report_b.get("location", "").lower()
        if loc_a == loc_b:
            score += 0.2
        elif loc_a in loc_b or loc_b in loc_a:
            score += 0.1
        
        # Category match
        cat_a = report_a.get("category", "").lower()
        cat_b = report_b.get("category", "").lower()
        if cat_a == cat_b:
            score += 0.1
        
        # Time proximity
        try:
            dt_a = datetime.fromisoformat(report_a.get("date_time", ""))
            dt_b = datetime.fromisoformat(report_b.get("date_time", ""))
            diff = abs((dt_a - dt_b).total_seconds())
            if diff <= 3600:  # Within 1 hour
                score += 0.1
        except:
            pass
        
        # Semantic similarity if embedding service available
        if embedding_service:
            try:
                text_a = f"{title_a} {desc_a}"
                text_b = f"{title_b} {desc_b}"
                emb_a = embedding_service.get_text_embedding(text_a)
                emb_b = embedding_service.get_text_embedding(text_b)
                if emb_a is not None and emb_b is not None:
                    sem_sim = embedding_service.cosine_similarity(emb_a, emb_b)
                    score += sem_sim * 0.2
            except:
                pass
        
        return score
    
    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate text similarity using token overlap."""
        tokens_a = set(re.findall(r"[a-z0-9]+", text_a))
        tokens_b = set(re.findall(r"[a-z0-9]+", text_b))
        
        if not tokens_a or not tokens_b:
            return 0.0
        
        overlap = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        
        return overlap / union if union > 0 else 0.0
    
    def _generate_duplicate_reason(self, new_report: Dict, existing: Dict) -> str:
        """Generate explanation for why reports might be duplicates."""
        reasons = []
        
        if new_report.get("title", "").lower() == existing.get("title", "").lower():
            reasons.append("Same title")
        
        if new_report.get("location", "").lower() == existing.get("location", "").lower():
            reasons.append("Same location")
        
        if new_report.get("category", "").lower() == existing.get("category", "").lower():
            reasons.append("Same category")
        
        return " and ".join(reasons) if reasons else "Similar content"
    
    def analyze_claim_risk(self, claim: Dict, item: Dict, user_history: List[Dict]) -> Dict:
        """
        Analyze claim for potential fraud or suspicious activity.
        
        Args:
            claim: Claim information
            item: Item being claimed
            user_history: User's previous claims history
            
        Returns:
            dict: Risk analysis with score and reasons
        """
        risk_factors = []
        risk_score = 0.0
        
        # Check answer quality
        answer = claim.get("answer", "")
        if len(answer) < 10:
            risk_score += 0.3
            risk_factors.append("Very short answer")
        
        # Check for generic answers
        generic_phrases = ["it is", "the item", "my", "i lost", "i found"]
        if any(phrase in answer.lower() for phrase in generic_phrases):
            risk_score += 0.2
            risk_factors.append("Generic answer pattern")
        
        # Check claim history
        if user_history:
            recent_claims = [c for c in user_history 
                           if (datetime.now() - datetime.fromisoformat(c.get("created_at", ""))).days <= 7]
            
            if len(recent_claims) > 3:
                risk_score += 0.3
                risk_factors.append("Many recent claims")
            
            # Check rejected claims
            rejected = [c for c in user_history if c.get("status") == "rejected"]
            if len(rejected) > 2:
                risk_score += 0.4
                risk_factors.append("Multiple rejected claims")
        
        # Check account age
        user_created = claim.get("user_created_at")
        if user_created:
            try:
                account_age = (datetime.now() - datetime.fromisoformat(user_created)).days
                if account_age < 7:
                    risk_score += 0.2
                    risk_factors.append("New account")
            except:
                pass
        
        # Check timing (claim submitted shortly after item creation)
        try:
            item_created = datetime.fromisoformat(item.get("created_at", ""))
            claim_created = datetime.fromisoformat(claim.get("created_at", ""))
            time_diff = (claim_created - item_created).total_seconds()
            
            if time_diff < 60:  # Claimed within 1 minute of item creation
                risk_score += 0.3
                risk_factors.append("Claimed immediately after report")
        except:
            pass
        
        # Determine risk level
        if risk_score >= self.risk_threshold_high:
            risk_level = "HIGH"
        elif risk_score >= self.risk_threshold_medium:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_score": round(risk_score * 100, 1),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level, risk_factors)
        }
    
    def _get_risk_recommendation(self, risk_level: str, factors: List) -> str:
        """Get recommendation based on risk level."""
        if risk_level == "HIGH":
            return "Manual review required. Do not auto-approve."
        elif risk_level == "MEDIUM":
            return "Review recommended. Verify claimant identity."
        else:
            return "Normal claim. Standard verification process."
    
    def detect_suspicious_activity(self, user_id: int, user_reports: List[Dict],
                                   user_claims: List[Dict]) -> List[Dict]:
        """
        Detect suspicious user activity patterns.
        
        Args:
            user_id: User identifier
            user_reports: User's report history
            user_claims: User's claim history
            
        Returns:
            list: Suspicious activities detected
        """
        suspicious = []
        
        # Check for rapid reporting
        recent_reports = [r for r in user_reports 
                        if (datetime.now() - datetime.fromisoformat(r.get("created_at", ""))).days <= 1]
        
        if len(recent_reports) > 5:
            suspicious.append({
                "type": "rapid_reporting",
                "severity": "medium",
                "description": f"User reported {len(recent_reports)} items in 24 hours"
            })
        
        # Check for claiming own items
        for claim in user_claims:
            for report in user_reports:
                if report.get("id") == claim.get("item_id"):
                    suspicious.append({
                        "type": "self_claim",
                        "severity": "high",
                        "description": "User attempted to claim their own reported item"
                    })
                    break
        
        # Check for pattern of claiming without verification
        approved_claims = [c for c in user_claims if c.get("status") == "approved"]
        if len(approved_claims) > 10:
            suspicious.append({
                "type": "excessive_claims",
                "severity": "medium",
                "description": f"User has {len(approved_claims)} approved claims"
            })
        
        return suspicious
