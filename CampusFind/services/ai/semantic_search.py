"""
Semantic Search - Conversational search with natural language understanding.

Provides:
- Natural language query parsing
- Structured filter extraction
- Semantic similarity search
- Conversational search interface
- Relevance scoring with explanations
"""
import re
from typing import Dict, List, Tuple, Optional
import config


class SemanticSearch:
    """Conversational semantic search engine."""
    
    # Item type keywords
    ITEM_TYPES = {
        "wallet": "wallet",
        "phone": "phone", "mobile": "phone", "cellphone": "phone",
        "keys": "keys", "key": "keys",
        "bag": "bag", "backpack": "backpack", "rucksack": "backpack",
        "laptop": "laptop", "notebook": "laptop",
        "headphones": "headphones", "earbuds": "earbuds", "earphones": "headphones",
        "watch": "watch",
        "id card": "id card", "identity card": "id card", "student id": "id card",
        "bottle": "bottle", "water bottle": "bottle",
        "book": "book", "notebook": "book",
        "umbrella": "umbrella",
        "glasses": "glasses", "spectacles": "glasses"
    }
    
    # Color keywords
    COLORS = {
        "black": "black", "white": "white", "red": "red",
        "blue": "blue", "green": "green", "yellow": "yellow",
        "brown": "brown", "gray": "gray", "grey": "gray",
        "pink": "pink", "purple": "purple", "orange": "orange"
    }
    
    # Location keywords
    LOCATIONS = {
        "library": "library", "central library": "library",
        "cafeteria": "cafeteria", "canteen": "cafeteria", "mess": "cafeteria",
        "parking": "parking", "parking lot": "parking",
        "classroom": "classroom", "class": "classroom",
        "lab": "lab", "laboratory": "lab",
        "gym": "gym",
        "hostel": "hostel", "dorm": "hostel",
        "cse": "cse", "computer science": "cse", "cs block": "cse",
        "ece": "ece", "electronics": "ece", "ece block": "ece",
        "mech": "mech", "mechanical": "mech", "mech block": "mech",
        "block": "block", "building": "block"
    }
    
    # Timeframe keywords
    TIMEFRAMES = {
        "today": 0,
        "yesterday": 1,
        "this week": 7,
        "last week": 7,
        "this month": 30,
        "last month": 30,
        "this year": 365
    }
    
    def __init__(self):
        pass
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse natural language search query into structured filters.
        
        Args:
            query: Natural language search query
            
        Returns:
            dict: Structured search parameters
        """
        result = {
            "original_query": query,
            "filters": {},
            "intent": "search"
        }
        
        query_lower = query.lower()
        
        # Detect intent (lost vs found)
        if "lost" in query_lower:
            result["filters"]["type"] = "lost"
            result["intent"] = "search_lost"
        elif "found" in query_lower:
            result["filters"]["type"] = "found"
            result["intent"] = "search_found"
        
        # Detect item type
        for keyword, item_type in self.ITEM_TYPES.items():
            if keyword in query_lower:
                result["filters"]["type"] = item_type
                break
        
        # Detect color
        for keyword, color in self.COLORS.items():
            if keyword in query_lower:
                result["filters"]["color"] = color
                break
        
        # Detect location
        for keyword, location in self.LOCATIONS.items():
            if keyword in query_lower:
                result["filters"]["location"] = location
                break
        
        # Detect timeframe
        for keyword, days in self.TIMEFRAMES.items():
            if keyword in query_lower:
                result["filters"]["days_within"] = days
                break
        
        # Extract remaining keywords for text search
        result["keywords"] = self._extract_keywords(query_lower)
        
        return result
    
    def search_items(self, query: str, items: List[Dict], 
                    embedding_service=None) -> List[Tuple[Dict, float, Dict]]:
        """
        Perform semantic search on items with relevance scoring.
        
        Args:
            query: Search query string
            items: List of item dictionaries
            embedding_service: Optional embedding service for semantic search
            
        Returns:
            list: (item, relevance_score, explanation) tuples sorted by relevance
        """
        if not query:
            return [(item, 100.0, {"reason": "No query specified, showing all items"}) for item in items]
        
        parsed = self.parse_query(query)
        results = []
        
        for item in items:
            score, explanation = self._calculate_relevance(item, parsed, embedding_service)
            results.append((item, score, explanation))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply max results limit
        max_results = config.AIConfig.MAX_MATCH_RESULTS
        return results[:max_results]
    
    def _calculate_relevance(self, item: Dict, parsed_query: Dict,
                           embedding_service=None) -> Tuple[float, Dict]:
        """Calculate relevance score for an item."""
        score = 0.0
        reasons = []
        filters = parsed_query.get("filters", {})
        keywords = parsed_query.get("keywords", [])
        
        # Type match
        if "type" in filters:
            item_type = item.get("type", "").lower()
            if item_type == filters["type"]:
                score += 30
                reasons.append(f"Matches report type: {filters['type']}")
        
        # Category match
        if "type" in filters and filters["type"] not in ["lost", "found"]:
            category = item.get("category", "").lower()
            if filters["type"] in category:
                score += 25
                reasons.append(f"Matches category: {filters['type']}")
        
        # Color match
        if "color" in filters:
            item_color = item.get("color", "").lower()
            if filters["color"] in item_color:
                score += 20
                reasons.append(f"Matches color: {filters['color']}")
        
        # Location match
        if "location" in filters:
            item_location = item.get("location", "").lower()
            if filters["location"] in item_location:
                score += 25
                reasons.append(f"Matches location: {filters['location']}")
        
        # Timeframe match
        if "days_within" in filters:
            from datetime import datetime, timedelta
            try:
                item_date = datetime.fromisoformat(item.get("date_time", ""))
                cutoff = datetime.now() - timedelta(days=filters["days_within"])
                if item_date >= cutoff:
                    score += 15
                    reasons.append(f"Within timeframe: {filters['days_within']} days")
            except:
                pass
        
        # Keyword matching in title
        for keyword in keywords:
            if keyword in item.get("title", "").lower():
                score += 15
                reasons.append(f"Keyword in title: {keyword}")
                break
        
        # Keyword matching in description
        for keyword in keywords:
            if keyword in item.get("description", "").lower():
                score += 10
                reasons.append(f"Keyword in description: {keyword}")
                break
        
        # Semantic similarity if embedding service available
        if embedding_service and keywords:
            query_text = " ".join(keywords)
            item_text = f"{item.get('title', '')} {item.get('description', '')}"
            
            try:
                query_emb = embedding_service.get_text_embedding(query_text)
                item_emb = embedding_service.get_text_embedding(item_text)
                
                if query_emb is not None and item_emb is not None:
                    sim = embedding_service.cosine_similarity(query_emb, item_emb)
                    score += sim * 20
                    if sim > 0.7:
                        reasons.append("High semantic similarity")
            except:
                pass
        
        explanation = {
            "reason": " and ".join(reasons) if reasons else "Partial match based on keywords",
            "matched_filters": reasons
        }
        
        return min(round(score, 1), 100), explanation
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query."""
        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "shall", "can", "need", "dare",
                     "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
                     "us", "them", "my", "your", "his", "its", "our", "their", "this",
                     "that", "these", "those", "am", "in", "on", "at", "to", "for", "of",
                     "with", "by", "from", "up", "down", "over", "under", "again", "further",
                     "then", "once", "here", "there", "when", "where", "why", "how", "all",
                     "any", "both", "each", "few", "more", "most", "other", "some", "such",
                     "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
                     "just", "and", "but", "if", "or", "because", "as", "until", "while",
                     "find", "search", "look", "show", "display", "lost", "found", "near",
                     "around", "about"}
        
        words = re.findall(r"[a-z]+", query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def suggest_query_completion(self, partial_query: str) -> List[str]:
        """
        Suggest query completions based on partial input.
        
        Args:
            partial_query: Partial search query
            
        Returns:
            list: Suggested completions
        """
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Suggest item types
        for keyword, item_type in self.ITEM_TYPES.items():
            if keyword.startswith(partial_lower):
                suggestions.append(f"{keyword} lost")
                suggestions.append(f"{keyword} found")
        
        # Suggest locations
        for keyword, location in self.LOCATIONS.items():
            if keyword.startswith(partial_lower):
                suggestions.append(f"near {location}")
        
        # Suggest colors
        for keyword, color in self.COLORS.items():
            if keyword.startswith(partial_lower):
                suggestions.append(f"{color} bag")
        
        return suggestions[:10]
