import os
from PIL import Image
import re


class ImageAnalyzer:
    """AI-powered image analysis with local fallback."""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.use_api = bool(self.api_key)
    
    def analyze_image(self, image_path):
        """
        Analyze an uploaded image and extract item information.
        
        Args:
            image_path: Path to the uploaded image file
            
        Returns:
            dict: Analysis results with suggested category, color, brand, etc.
        """
        if self.use_api:
            return self._analyze_with_api(image_path)
        else:
            return self._analyze_local(image_path)
    
    def _analyze_with_api(self, image_path):
        """Analyze image using OpenAI Vision API (if API key is configured)."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            # Read and encode image
            import base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image of a lost or found item. Provide:
1. Item type (e.g., backpack, wallet, phone, keys)
2. Category (Electronics, ID Card, Wallet, Keys, Bag, Books, Clothing, Jewellery, Bottle, Other)
3. Dominant color(s)
4. Visible brand/logo if any
5. Visible characteristics (2-3 key features)

Respond in this exact format:
Item: [item type]
Category: [category]
Color: [color]
Brand: [brand or "Not visible"]
Characteristics: [comma-separated features]"""
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
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            return self._parse_api_response(content)
            
        except Exception as e:
            # Fallback to local analysis if API fails
            print(f"API analysis failed: {e}, using local fallback")
            return self._analyze_local(image_path)
    
    def _parse_api_response(self, content):
        """Parse API response into structured format."""
        result = {
            "suggested_category": "Other",
            "suggested_color": "",
            "suggested_brand": "",
            "visual_characteristics": "",
            "confidence_score": 0.8,
            "analysis_method": "api"
        }
        
        for line in content.split('\n'):
            if line.startswith("Item:"):
                result["item_type"] = line.split(":", 1)[1].strip()
            elif line.startswith("Category:"):
                result["suggested_category"] = line.split(":", 1)[1].strip()
            elif line.startswith("Color:"):
                result["suggested_color"] = line.split(":", 1)[1].strip()
            elif line.startswith("Brand:"):
                brand = line.split(":", 1)[1].strip()
                result["suggested_brand"] = brand if brand != "Not visible" else ""
            elif line.startswith("Characteristics:"):
                result["visual_characteristics"] = line.split(":", 1)[1].strip()
        
        return result
    
    def _analyze_local(self, image_path):
        """
        Local fallback analysis using basic image processing.
        This provides basic suggestions without requiring external APIs.
        """
        result = {
            "suggested_category": "Other",
            "suggested_color": "",
            "suggested_brand": "",
            "visual_characteristics": "",
            "confidence_score": 0.5,
            "analysis_method": "local"
        }
        
        try:
            img = Image.open(image_path)
            
            # Basic color detection
            colors = self._detect_dominant_colors(img)
            if colors:
                result["suggested_color"] = ", ".join(colors[:2])
            
            # Basic characteristics based on image properties
            width, height = img.size
            aspect_ratio = width / height
            
            characteristics = []
            if aspect_ratio > 1.2:
                characteristics.append("Rectangular shape")
            elif aspect_ratio < 0.8:
                characteristics.append("Portrait orientation")
            else:
                characteristics.append("Square-ish shape")
            
            if img.mode == "RGBA":
                characteristics.append("Transparent elements")
            
            result["visual_characteristics"] = ", ".join(characteristics)
            
        except Exception as e:
            print(f"Local image analysis failed: {e}")
            result["visual_characteristics"] = "Unable to analyze image"
        
        return result
    
    def _detect_dominant_colors(self, img, num_colors=3):
        """Detect dominant colors in image (basic implementation)."""
        try:
            # Resize for faster processing
            img_small = img.resize((100, 100))
            pixels = img_small.getdata()
            
            # Simple color bucketing
            color_counts = {}
            for pixel in pixels[:1000]:  # Sample pixels
                if isinstance(pixel, tuple):
                    r, g, b = pixel[:3]
                else:
                    r = g = b = pixel
                
                # Quantize colors
                r = (r // 32) * 32
                g = (g // 32) * 32
                b = (b // 32) * 32
                
                color_name = self._color_to_name(r, g, b)
                color_counts[color_name] = color_counts.get(color_name, 0) + 1
            
            # Sort by frequency
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
