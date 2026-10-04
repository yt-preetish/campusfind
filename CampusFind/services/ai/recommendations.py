"""
Recommendation Engine - Personalized match feed for users.

Provides:
- Personalized match recommendations based on user's lost items
- Real-time notifications for new potential matches
- Match relevance scoring
- User-specific feed generation
"""
from datetime import datetime
from typing import Dict, List, Optional
import config


class RecommendationEngine:
    """Generate personalized recommendations for users."""
    
    def __init__(self):
        self.matcher = None  # Will be initialized with MultimodalMatcher
        self.embedding_service = None
    
    def set_services(self, matcher, embedding_service):
        """Set required services for recommendations."""
        self.matcher = matcher
        self.embedding_service = embedding_service
    
    def get_personalized_matches(self, user_id: int, user_lost_items: List[Dict],
                               all_found_items: List[Dict]) -> List[Dict]:
        """
        Get personalized matches for a user's lost items.
        
        Args:
            user_id: User identifier
            user_lost_items: User's lost item reports
            all_found_items: All found items in the system
            
        Returns:
            list: Recommended matches with scores
        """
        if not self.matcher:
            return []
        
        recommendations = []
        
        for lost_item in user_lost_items:
            if lost_item.get("type") != "lost":
                continue
            
            if lost_item.get("status") != "open":
                continue
            
            # Find matching found items
            for found_item in all_found_items:
                if found_item.get("type") != "found":
                    continue
                
                if found_item.get("status") != "open":
                    continue
                
                # Calculate match
                match_result = self.matcher.match_items(
                    lost_item, found_item,
                    self.embedding_service,
                    self.embedding_service
                )
                
                # Only include high-confidence matches
                if match_result["overall_score"] >= 70:
                    recommendations.append({
                        "lost_item_id": lost_item["id"],
                        "lost_item_title": lost_item["title"],
                        "found_item_id": found_item["id"],
                        "found_item_title": found_item["title"],
                        "match_score": match_result["overall_score"],
                        "confidence": match_result["confidence"],
                        "confidence_level": match_result["confidence_level"],
                        "explanation": match_result["explanation"],
                        "breakdown": match_result["breakdown"],
                        "created_at": datetime.now().isoformat()
                    })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Limit results
        max_results = config.AIConfig.MAX_MATCH_RESULTS
        return recommendations[:max_results]
    
    def get_new_matches_for_user(self, user_id: int, user_lost_items: List[Dict],
                                new_found_item: Dict) -> List[Dict]:
        """
        Check if a new found item matches any of user's lost items.
        
        Args:
            user_id: User identifier
            user_lost_items: User's lost item reports
            new_found_item: Newly created found item
            
        Returns:
            list: New matches for this user
        """
        if not self.matcher or new_found_item.get("type") != "found":
            return []
        
        new_matches = []
        
        for lost_item in user_lost_items:
            if lost_item.get("type") != "lost":
                continue
            
            if lost_item.get("status") != "open":
                continue
            
            # Calculate match
            match_result = self.matcher.match_items(
                lost_item, new_found_item,
                self.embedding_service,
                self.embedding_service
            )
            
            # Include medium+ confidence matches for notifications
            if match_result["overall_score"] >= 60:
                new_matches.append({
                    "lost_item_id": lost_item["id"],
                    "lost_item_title": lost_item["title"],
                    "found_item_id": new_found_item["id"],
                    "found_item_title": new_found_item["title"],
                    "match_score": match_result["overall_score"],
                    "confidence": match_result["confidence"],
                    "explanation": match_result["explanation"]
                })
        
        # Sort by match score
        new_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return new_matches
    
    def get_similar_items(self, item: Dict, all_items: List[Dict],
                         limit: int = 5) -> List[Dict]:
        """
        Find items similar to a given item.
        
        Args:
            item: Reference item
            all_items: All items to search
            limit: Maximum number of results
            
        Returns:
            list: Similar items with scores
        """
        if not self.matcher:
            return []
        
        similar = []
        
        for other_item in all_items:
            if other_item["id"] == item["id"]:
                continue
            
            if other_item.get("type") == item.get("type"):
                continue  # Only match opposite types
            
            match_result = self.matcher.match_items(
                item, other_item,
                self.embedding_service,
                self.embedding_service
            )
            
            if match_result["overall_score"] >= 50:
                similar.append({
                    "item_id": other_item["id"],
                    "title": other_item["title"],
                    "type": other_item["type"],
                    "match_score": match_result["overall_score"],
                    "confidence": match_result["confidence"],
                    "explanation": match_result["explanation"]
                })
        
        similar.sort(key=lambda x: x["match_score"], reverse=True)
        return similar[:limit]
    
    def generate_feed(self, user_id: int, user_lost_items: List[Dict],
                     all_found_items: List[Dict]) -> Dict:
        """
        Generate complete personalized feed for a user.
        
        Args:
            user_id: User identifier
            user_lost_items: User's lost items
            all_found_items: All found items
            
        Returns:
            dict: Complete feed with recommendations
        """
        personalized_matches = self.get_personalized_matches(
            user_id, user_lost_items, all_found_items
        )
        
        # Categorize matches by confidence
        high_confidence = [m for m in personalized_matches if m["confidence_level"] == "HIGH"]
        medium_confidence = [m for m in personalized_matches if m["confidence_level"] == "MEDIUM"]
        
        return {
            "user_id": user_id,
            "total_matches": len(personalized_matches),
            "high_confidence_matches": high_confidence,
            "medium_confidence_matches": medium_confidence,
            "generated_at": datetime.now().isoformat()
        }
