"""
Vision Analyzer - Advanced image analysis for CampusFind.

Provides:
- Object type detection
- Category classification
- Color detection
- Brand/logo identification
- Visual feature extraction
- Condition assessment
- Background/location clues

Supports OpenAI Vision API with local fallback.
"""
import os
import base64
from datetime import datetime
from PIL import Image
import config


class VisionAnalyzer:
    """Advanced vision analysis with multi-level fallback."""
    
    def __init__(self):
        self.api_key = config.AIConfig.OPENAI_API_KEY
        self.model = config.AIConfig.OPENAI_VISION_MODEL
        self.use_api = bool(self.api_key)
        self.model_version = config.AIConfig.VISION_MODEL_VERSION
    
    def analyze_image(self, image_path, item_context=None):
        """
        Analyze an uploaded image and extract comprehensive item information.
        
        Args:
            image_path: Path to the uploaded image file
            item_context: Optional context (type, location) to guide analysis
            
        Returns:
            dict: Analysis results with structured item fingerprint
        """
        if self.use_api and config.AIConfig.AI_PROVIDER in ["openai", "hybrid"]:
            try:
                result = self._analyze_with_api(image_path, item_context)
                result["model_version"] = self.model_version
                result["analysis_timestamp"] = datetime.now().isoformat()
                return result
            except Exception as e:
                print(f"API analysis failed: {e}, falling back to local")
                if config.AIConfig.FALLBACK_LEVEL in ["auto", "level2", "level3"]:
                    return self._analyze_local(image_path, item_context)
        
        # Local fallback
        result = self._analyze_local(image_path, item_context)
        result["model_version"] = f"local-{self.model_version}"
        result["analysis_timestamp"] = datetime.now().isoformat()
        return result
    
    def _analyze_with_api(self, image_path, item_context):
        """Analyze image using OpenAI Vision API."""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Build context-aware prompt
        context_hint = ""
        if item_context:
            if item_context.get("type"):
                context_hint = f"This is a {item_context['type']} report. "
            if item_context.get("location"):
                context_hint += f"Location: {item_context['location']}. "
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""{context_hint}Analyze this image of a lost or found item. Provide detailed analysis:

1. OBJECT TYPE: What is the main object? (e.g., backpack, wallet, phone, keys, laptop, water bottle)

2. CATEGORY: Electronics, ID Card, Wallet, Keys, Bag, Books, Clothing, Jewellery, Bottle, Other

3. PRIMARY COLOR: Dominant color

4. SECONDARY COLOR: Any secondary colors

5. VISIBLE BRAND/LOGO: Is there a visible brand or logo? If yes, specify.

6. DISTINCTIVE FEATURES: List 3-5 key visual features (e.g., front zipper pocket, side pockets, white logo, red tag, handle design)

7. ACCESSORIES/COMPONENTS: Any visible accessories (e.g., keychain, strap, case)

8. APPROXIMATE CONDITION: New, Good, Used, Damaged

9. VISIBLE TEXT: Any visible text, numbers, or writing (be specific)

10. BACKGROUND CLUES: Any location context from background (e.g., library shelves, classroom desk, grass)

Respond in this exact format:
OBJECT: [object type]
CATEGORY: [category]
PRIMARY_COLOR: [color]
SECONDARY_COLOR: [color or "None"]
BRAND: [brand or "Not visible"]
FEATURES: [comma-separated features]
ACCESSORIES: [comma-separated or "None"]
CONDITION: [condition]
VISIBLE_TEXT: [text or "None"]
BACKGROUND: [clues or "None"]
CONFIDENCE: [0-100]"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        return self._parse_api_response(content)
    
    def _parse_api_response(self, content):
        """Parse API response into structured format."""
        result = {
            "object_type": "",
            "category": "Other",
            "primary_color": "",
            "secondary_color": "",
            "brand": "",
            "features": [],
            "accessories": [],
            "condition": "",
            "visible_text": "",
            "background_clues": "",
            "confidence_score": 0.8,
            "analysis_method": "api"
        }
        
        for line in content.split('\n'):
            if line.startswith("OBJECT:"):
                result["object_type"] = line.split(":", 1)[1].strip()
            elif line.startswith("CATEGORY:"):
                result["category"] = line.split(":", 1)[1].strip()
            elif line.startswith("PRIMARY_COLOR:"):
                result["primary_color"] = line.split(":", 1)[1].strip()
            elif line.startswith("SECONDARY_COLOR:"):
                sec = line.split(":", 1)[1].strip()
                result["secondary_color"] = sec if sec != "None" else ""
            elif line.startswith("BRAND:"):
                brand = line.split(":", 1)[1].strip()
                result["brand"] = brand if brand != "Not visible" else ""
            elif line.startswith("FEATURES:"):
                features = line.split(":", 1)[1].strip()
                result["features"] = [f.strip() for f in features.split(",") if f.strip()]
            elif line.startswith("ACCESSORIES:"):
                acc = line.split(":", 1)[1].strip()
                result["accessories"] = [a.strip() for a in acc.split(",") if a.strip() and a != "None"]
            elif line.startswith("CONDITION:"):
                result["condition"] = line.split(":", 1)[1].strip()
            elif line.startswith("VISIBLE_TEXT:"):
                text = line.split(":", 1)[1].strip()
                result["visible_text"] = text if text != "None" else ""
            elif line.startswith("BACKGROUND:"):
                bg = line.split(":", 1)[1].strip()
                result["background_clues"] = bg if bg != "None" else ""
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence_score"] = float(line.split(":", 1)[1].strip()) / 100
                except:
                    result["confidence_score"] = 0.8
        
        return result
    
    def _analyze_local(self, image_path, item_context):
        """
        Local fallback analysis using basic image processing.
        Provides basic suggestions without requiring external APIs.
        """
        result = {
            "object_type": "",
            "category": "Other",
            "primary_color": "",
            "secondary_color": "",
            "brand": "",
            "features": [],
            "accessories": [],
            "condition": "",
            "visible_text": "",
            "background_clues": "",
            "confidence_score": 0.5,
            "analysis_method": "local"
        }
        
        try:
            img = Image.open(image_path)
            
            # Color detection
            colors = self._detect_dominant_colors(img)
            if colors:
                result["primary_color"] = colors[0]
                if len(colors) > 1:
                    result["secondary_color"] = colors[1]
            
            # Basic characteristics
            width, height = img.size
            aspect_ratio = width / height
            
            features = []
            if aspect_ratio > 1.2:
                features.append("Rectangular shape")
            elif aspect_ratio < 0.8:
                features.append("Portrait orientation")
            else:
                features.append("Square-ish shape")
            
            if img.mode == "RGBA":
                features.append("Transparent elements")
            
            # Estimate size category
            if width > 1000 or height > 1000:
                features.append("Large image (high resolution)")
            elif width < 300 or height < 300:
                features.append("Small image (low resolution)")
            
            result["features"] = features
            
            # Infer category from context if available
            if item_context and item_context.get("type"):
                result["object_type"] = item_context["type"]
                # Simple category mapping
                category_map = {
                    "wallet": "Wallet",
                    "phone": "Electronics",
                    "keys": "Keys",
                    "bag": "Bag",
                    "backpack": "Bag",
                    "laptop": "Electronics",
                    "id card": "ID Card",
                    "bottle": "Bottle",
                    "book": "Books"
                }
                result["category"] = category_map.get(item_context["type"].lower(), "Other")
            
        except Exception as e:
            print(f"Local image analysis failed: {e}")
            result["features"] = ["Unable to analyze image"]
        
        return result
    
    def _detect_dominant_colors(self, img, num_colors=3):
        """Detect dominant colors in image."""
        try:
            img_small = img.resize((100, 100))
            pixels = img_small.getdata()
            
            color_counts = {}
            for pixel in pixels[:1000]:
                if isinstance(pixel, tuple):
                    r, g, b = pixel[:3]
                else:
                    r = g = b = pixel
                
                r = (r // 32) * 32
                g = (g // 32) * 32
                b = (b // 32) * 32
                
                color_name = self._color_to_name(r, g, b)
                color_counts[color_name] = color_counts.get(color_name, 0) + 1
            
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
            return [c[0] for c in sorted_colors[:num_colors]]
        except:
            return []
    
    def _color_to_name(self, r, g, b):
        """Convert RGB to basic color name."""
        if r > 200 and g > 200 and b > 200:
            return "White"
        elif r < 50 and g < 50 and b < 50:
            return "Black"
        elif r > 200 and g < 100 and b < 100:
            return "Red"
        elif r < 100 and g > 200 and b < 100:
            return "Green"
        elif r < 100 and g < 100 and b > 200:
            return "Blue"
        elif r > 200 and g > 200 and b < 100:
            return "Yellow"
        elif r > 200 and g < 100 and b > 200:
            return "Purple"
        elif r < 100 and g > 200 and b > 200:
            return "Cyan"
        elif r > 150 and g > 100 and b < 50:
            return "Brown"
        elif r > 100 and g > 100 and b > 100:
            return "Gray"
        else:
            return "Multi-colored"
    
    def generate_item_fingerprint(self, analysis_result):
        """
        Generate a structured item fingerprint from analysis results.
        
        Args:
            analysis_result: Result from analyze_image()
            
        Returns:
            dict: Structured item fingerprint for matching
        """
        return {
            "category": analysis_result.get("category", "Other"),
            "primary_color": analysis_result.get("primary_color", ""),
            "secondary_color": analysis_result.get("secondary_color", ""),
            "brand": analysis_result.get("brand", ""),
            "features": analysis_result.get("features", []),
            "accessories": analysis_result.get("accessories", []),
            "condition": analysis_result.get("condition", ""),
            "visible_text": analysis_result.get("visible_text", ""),
            "background_clues": analysis_result.get("background_clues", ""),
            "confidence": analysis_result.get("confidence_score", 0.5),
            "analysis_method": analysis_result.get("analysis_method", "local"),
            "model_version": analysis_result.get("model_version", "unknown")
        }
