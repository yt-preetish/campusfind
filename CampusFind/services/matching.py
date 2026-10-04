import re
from datetime import datetime


def token_set(text):
    """Extract tokens from text for similarity comparison."""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def text_similarity(a, b):
    """Calculate text similarity using token overlap."""
    A, B = token_set(a), token_set(b)
    if not A or not B:
        return 0
    return round(100 * len(A & B) / len(A | B), 1)


def location_similarity(a, b):
    """Calculate location similarity using text comparison."""
    return text_similarity(a, b)


def date_similarity(a, b):
    """Calculate date/time proximity similarity."""
    try:
        da = datetime.fromisoformat(a).date()
        dbb = datetime.fromisoformat(b).date()
        diff = abs((da - dbb).days)
        return 100 if diff == 0 else 70 if diff == 1 else 35 if diff <= 3 else 0
    except:
        return 0


def category_similarity(a, b):
    """Check if categories match exactly."""
    return 100 if a.lower() == b.lower() else 0


def color_similarity(a, b):
    """Calculate color similarity (basic implementation)."""
    if not a or not b:
        return 0
    a_colors = set(a.lower().split())
    b_colors = set(b.lower().split())
    if a_colors & b_colors:
        return 100
    return 0


def match_score(item, other, image_similarity_score=None):
    """
    Calculate overall match score between two items.
    
    Returns:
        tuple: (overall_score, breakdown_dict)
        breakdown_dict contains individual component scores
    """
    # Convert Row objects to dict if needed
    item_dict = dict(item) if hasattr(item, 'keys') else item
    other_dict = dict(other) if hasattr(other, 'keys') else other
    
    text = text_similarity(
        f"{item_dict['title']} {item_dict['category']} {item_dict['description']}",
        f"{other_dict['title']} {other_dict['category']} {other_dict['description']}"
    )
    loc = location_similarity(item_dict["location"], other_dict["location"])
    date = date_similarity(item_dict["date_time"], other_dict["date_time"])
    cat = category_similarity(item_dict["category"], other_dict["category"])
    
    # Color similarity if available
    color = 0
    item_color = item_dict.get("color") if isinstance(item_dict, dict) else item_dict["color"] if "color" in item_dict.keys() else None
    other_color = other_dict.get("color") if isinstance(other_dict, dict) else other_dict["color"] if "color" in other_dict.keys() else None
    if item_color and other_color:
        color = color_similarity(item_color, other_color)
    
    # Image similarity if provided
    img = image_similarity_score if image_similarity_score else 0
    
    # Weighted scoring system
    # Text similarity: 25%
    # Image similarity: 30% (if available, otherwise redistributed)
    # Location similarity: 15%
    # Date proximity: 10%
    # Category match: 10%
    # Color/brand features: 10%
    
    if img > 0:
        score = 0.25 * text + 0.30 * img + 0.15 * loc + 0.10 * date + 0.10 * cat + 0.10 * color
    else:
        # Redistribute weight if no image similarity
        score = 0.35 * text + 0.20 * loc + 0.15 * date + 0.15 * cat + 0.15 * color
    
    breakdown = {
        "text": text,
        "image": img,
        "location": loc,
        "date": date,
        "category": cat,
        "color": color
    }
    
    return round(score, 1), breakdown


def generate_match_explanation(breakdown):
    """Generate human-readable explanation of match."""
    reasons = []
    
    if breakdown["category"] == 100:
        reasons.append("Same category")
    if breakdown["color"] > 0:
        reasons.append("Similar color")
    if breakdown["text"] >= 70:
        reasons.append("Similar description")
    if breakdown["location"] >= 70:
        reasons.append("Nearby location")
    if breakdown["date"] >= 70:
        reasons.append("Close date")
    if breakdown["image"] >= 70:
        reasons.append("Similar image")
    
    if reasons:
        return "These reports may refer to the same item because: " + ", ".join(reasons) + "."
    return "These reports have some similarities but require further verification."
