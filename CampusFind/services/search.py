import re
from services.matching import text_similarity


def semantic_search(query, items):
    """
    Perform semantic search on items with relevance scoring.
    
    Args:
        query: Search query string
        items: List of item dictionaries
        
    Returns:
        List of (item, relevance_score) tuples sorted by relevance
    """
    if not query:
        return [(item, 100) for item in items]
    
    query_lower = query.lower()
    results = []
    
    for item in items:
        score = 0
        
        # Keyword matching in title
        if query_lower in item["title"].lower():
            score += 40
        
        # Keyword matching in description
        if query_lower in item["description"].lower():
            score += 30
        
        # Keyword matching in location
        if query_lower in item["location"].lower():
            score += 20
        
        # Category match
        if query_lower in item["category"].lower():
            score += 25
        
        # Text similarity for partial matches
        combined_text = f"{item['title']} {item['description']} {item['location']} {item['category']}"
        sim_score = text_similarity(query, combined_text)
        score += sim_score * 0.3
        
        # Bonus for exact word matches
        query_words = set(query_lower.split())
        item_words = set(combined_text.lower().split())
        word_matches = len(query_words & item_words)
        if word_matches > 0:
            score += word_matches * 10
        
        results.append((item, min(round(score, 1), 100)))
    
    # Sort by relevance score
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def parse_search_query(query):
    """
    Parse natural language search query for structured filters.
    
    Examples:
        "black bag found near library" -> {"color": "black", "type": "bag", "location": "library"}
        "wallet lost yesterday" -> {"type": "wallet", "timeframe": "yesterday"}
    """
    result = {"query": query}
    query_lower = query.lower()
    
    # Detect item type
    item_types = ["wallet", "phone", "keys", "bag", "backpack", "laptop", "headphones", "earbuds", 
                  "watch", "id card", "bottle", "book", "umbrella", "glasses"]
    for item_type in item_types:
        if item_type in query_lower:
            result["type"] = item_type
            break
    
    # Detect color
    colors = ["black", "white", "red", "blue", "green", "yellow", "brown", "gray", "grey", "pink", "purple"]
    for color in colors:
        if color in query_lower:
            result["color"] = color
            break
    
    # Detect location keywords
    locations = ["library", "cafeteria", "canteen", "parking", "classroom", "lab", "gym", "hostel", 
                 "cse", "ece", "mech", "block", "building", "floor"]
    for loc in locations:
        if loc in query_lower:
            result["location"] = loc
            break
    
    # Detect lost/found
    if "lost" in query_lower:
        result["report_type"] = "lost"
    elif "found" in query_lower:
        result["report_type"] = "found"
    
    # Detect timeframes
    timeframes = {
        "today": 0,
        "yesterday": 1,
        "this week": 7,
        "last week": 7,
        "this month": 30,
        "last month": 30
    }
    for timeframe, days in timeframes.items():
        if timeframe in query_lower:
            result["days_within"] = days
            break
    
    return result
