"""
AI Assistant - Conversational AI for lost item recovery.

Provides:
- Natural language conversation for reporting lost items
- Structured information extraction from conversation
- Context-aware question generation
- Progressive form filling through conversation
"""
import re
from typing import Dict, List, Optional
import config


class AIAssistant:
    """AI-powered recovery assistant for conversational reporting."""
    
    # Required fields for a complete report
    REQUIRED_FIELDS = ["type", "category", "title", "description", "location", "date_time"]
    
    # Optional fields that enhance matching
    OPTIONAL_FIELDS = ["color", "brand", "visual_features"]
    
    def __init__(self):
        self.api_key = config.AIConfig.OPENAI_API_KEY
        self.use_api = bool(self.api_key)
        self.conversation_state = {}
    
    def process_message(self, user_message: str, user_id: str, 
                       current_state: Dict = None) -> Dict:
        """
        Process user message and extract structured information.
        
        Args:
            user_message: User's natural language message
            user_id: User identifier for conversation state
            current_state: Current form state (if any)
            
        Returns:
            dict: Response with extracted info and next question
        """
        if current_state is None:
            current_state = {}
        
        # Extract information from message
        extracted = self._extract_information(user_message)
        
        # Update state with extracted info
        updated_state = {**current_state, **extracted}
        
        # Determine what information is still needed
        missing_fields = self._get_missing_fields(updated_state)
        
        # Generate response
        if not missing_fields:
            # All required fields collected
            return {
                "status": "complete",
                "state": updated_state,
                "message": "I have all the information needed. Please review your report and submit.",
                "can_submit": True
            }
        else:
            # Ask for missing information
            next_field = missing_fields[0]
            question = self._generate_question(next_field, updated_state)
            
            return {
                "status": "incomplete",
                "state": updated_state,
                "message": question,
                "missing_fields": missing_fields,
                "can_submit": False
            }
    
    def _extract_information(self, message: str) -> Dict:
        """Extract structured information from natural language message."""
        extracted = {}
        message_lower = message.lower()
        
        # Extract item type (lost/found)
        if "lost" in message_lower:
            extracted["type"] = "lost"
        elif "found" in message_lower:
            extracted["type"] = "found"
        
        # Extract item category/type
        item_types = {
            "wallet": "Wallet",
            "phone": "Electronics",
            "mobile": "Enhancements",
            "keys": "Keys",
            "bag": "Bag",
            "backpack": "Bag",
            "laptop": "Electronics",
            "headphones": "Electronics",
            "earbuds": "Electronics",
            "watch": "Electronics",
            "id card": "ID Card",
            "bottle": "Bottle",
            "book": "Books",
            "umbrella": "Other",
            "glasses": "Other"
        }
        
        for keyword, category in item_types.items():
            if keyword in message_lower:
                if not extracted.get("title"):
                    extracted["title"] = keyword.capitalize()
                extracted["category"] = category
                break
        
        # Extract color
        colors = ["black", "white", "red", "blue", "green", "yellow", 
                 "brown", "gray", "grey", "pink", "purple"]
        for color in colors:
            if color in message_lower:
                extracted["color"] = color.capitalize()
                break
        
        # Extract location
        locations = ["library", "cafeteria", "canteen", "parking", "classroom", 
                    "lab", "gym", "hostel", "cse", "ece", "mech", "block"]
        for loc in locations:
            if loc in message_lower:
                extracted["location"] = loc.capitalize()
                break
        
        # Extract date/time references
        if "yesterday" in message_lower:
            from datetime import datetime, timedelta
            extracted["date_time"] = (datetime.now() - timedelta(days=1)).isoformat()
        elif "today" in message_lower:
            from datetime import datetime
            extracted["date_time"] = datetime.now().isoformat()
        elif "morning" in message_lower:
            from datetime import datetime, timedelta
            extracted["date_time"] = (datetime.now().replace(hour=9, minute=0)).isoformat()
        elif "afternoon" in message_lower:
            from datetime import datetime
            extracted["date_time"] = (datetime.now().replace(hour=14, minute=0)).isoformat()
        
        # Extract description (use the message itself if not already set)
        if not extracted.get("description") and len(message) > 20:
            # Use the message as description, but remove common phrases
            desc = message
            desc = re.sub(r"(i lost|i found|my|a|an|the)", "", desc, flags=re.IGNORECASE)
            desc = desc.strip()
            if desc:
                extracted["description"] = desc
        
        return extracted
    
    def _get_missing_fields(self, state: Dict) -> List[str]:
        """Determine which required fields are still missing."""
        missing = []
        
        for field in self.REQUIRED_FIELDS:
            if not state.get(field):
                missing.append(field)
        
        return missing
    
    def _generate_question(self, field: str, current_state: Dict) -> str:
        """Generate a natural language question for a missing field."""
        questions = {
            "type": "Did you lose an item or find something?",
            "category": "What category does this item belong to? (e.g., Electronics, Bag, Wallet, Keys, ID Card)",
            "title": "What is the item? (e.g., Black backpack, iPhone 13, Blue wallet)",
            "description": "Can you describe the item in more detail? (e.g., color, brand, distinctive features)",
            "location": "Where did you lose/find this item? (e.g., Library, CSE block, Cafeteria)",
            "date_time": "When did you lose/find this item? (e.g., yesterday, today morning, 2 days ago)"
        }
        
        # Context-aware questions
        if field == "description" and current_state.get("title"):
            return f"Can you tell me more about the {current_state['title']}? Any distinctive features, brand, or color?"
        
        if field == "location" and current_state.get("date_time"):
            time_ref = current_state["date_time"]
            return f"Where were you when this happened {time_ref}?"
        
        return questions.get(field, f"Please provide the {field}.")
    
    def suggest_improvements(self, current_state: Dict) -> List[str]:
        """Suggest optional fields to improve matching accuracy."""
        suggestions = []
        
        if not current_state.get("color"):
            suggestions.append("Adding the color can significantly improve matching.")
        
        if not current_state.get("brand"):
            suggestions.append("If there's a visible brand, mentioning it helps with identification.")
        
        if not current_state.get("visual_features"):
            suggestions.append("Describe any distinctive features like logos, pockets, or accessories.")
        
        return suggestions
    
    def generate_summary(self, state: Dict) -> str:
        """Generate a natural language summary of the collected information."""
        item_type = state.get("type", "item").upper()
        title = state.get("title", "item")
        location = state.get("location", "unknown location")
        description = state.get("description", "")
        
        summary = f"You reported a {item_type}: {title}. "
        summary += f"Location: {location}. "
        
        if description:
            summary += f"Description: {description}"
        
        return summary
    
    def clarify_ambiguity(self, message: str, ambiguous_field: str) -> str:
        """Ask clarification question for ambiguous information."""
        clarifications = {
            "location": "Could you be more specific about the location? (e.g., which floor, which room, near what landmark?)",
            "date_time": "Could you provide a more specific time? (e.g., around 2 PM, yesterday morning)",
            "description": "What makes this item distinctive? (e.g., brand, color, unique features, accessories)",
            "title": "What type of item is it exactly? (e.g., is it a backpack, handbag, or shoulder bag?)"
        }
        
        return clarifications.get(ambiguous_field, "Could you provide more details?")
