"""
OCR Service - Text extraction from images with privacy protection.

Provides:
- OCR text extraction from images
- Privacy masking for sensitive information
- Support for multiple OCR providers (Tesseract, EasyOCR, OpenAI)
- Sensitive data detection (ID numbers, phone numbers, etc.)
- Configurable privacy settings
"""
import os
import re
from typing import Dict, List, Optional
import config


class OCRService:
    """OCR service with privacy masking."""
    
    # Patterns for sensitive information
    SENSITIVE_PATTERNS = {
        "student_id": r"\b\d{2}[A-Z]{2}\d{6}\b",  # e.g., 23IT123456
        "phone": r"\b\d{10}\b",  # 10-digit phone
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "roll_number": r"\b\d{8,12}\b",  # 8-12 digit roll numbers
        "serial": r"\b[A-Z0-9]{8,}\b",  # Serial numbers
    }
    
    def __init__(self):
        self.provider = config.AIConfig.OCR_PROVIDER
        self.enabled = config.AIConfig.OCR_ENABLED
        self.privacy_mask = config.AIConfig.PRIVACY_MASK_SENSITIVE
        self.api_key = config.AIConfig.OPENAI_API_KEY
        
        # Lazy-load OCR engines
        self._tesseract = None
        self._easyocr = None
    
    def extract_text(self, image_path: str, mask_sensitive: bool = None) -> Dict:
        """
        Extract text from image with optional privacy masking.
        
        Args:
            image_path: Path to image file
            mask_sensitive: Override privacy setting (default: use config)
            
        Returns:
            dict: OCR results with raw and masked text
        """
        if not self.enabled:
            return {
                "raw_text": "",
                "masked_text": "",
                "detected_fields": {},
                "sensitive_detected": False,
                "provider": "disabled"
            }
        
        if mask_sensitive is None:
            mask_sensitive = self.privacy_mask
        
        try:
            # Extract text using configured provider
            raw_text = self._extract_with_provider(image_path)
            
            # Detect sensitive information
            detected_fields = self._detect_sensitive_fields(raw_text)
            sensitive_detected = bool(detected_fields)
            
            # Mask sensitive information if required
            if mask_sensitive and sensitive_detected:
                masked_text = self._mask_sensitive_text(raw_text, detected_fields)
            else:
                masked_text = raw_text
            
            return {
                "raw_text": raw_text,
                "masked_text": masked_text,
                "detected_fields": detected_fields,
                "sensitive_detected": sensitive_detected,
                "provider": self.provider
            }
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return {
                "raw_text": "",
                "masked_text": "",
                "detected_fields": {},
                "sensitive_detected": False,
                "provider": self.provider,
                "error": str(e)
            }
    
    def _extract_with_provider(self, image_path: str) -> str:
        """Extract text using configured OCR provider."""
        if self.provider == "tesseract":
            return self._extract_tesseract(image_path)
        elif self.provider == "easyocr":
            return self._extract_easyocr(image_path)
        elif self.provider == "openai" and self.api_key:
            return self._extract_openai(image_path)
        else:
            # Default to Tesseract
            return self._extract_tesseract(image_path)
    
    def _extract_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except ImportError:
            print("Tesseract not available, install pytesseract and tesseract-ocr")
            return ""
        except Exception as e:
            print(f"Tesseract OCR failed: {e}")
            return ""
    
    def _extract_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR."""
        try:
            import easyocr
            if self._easyocr is None:
                self._easyocr = easyocr.Reader(['en'])
            
            result = self._easyocr.readtext(image_path)
            text = " ".join([detection[1] for detection in result])
            return text.strip()
        except ImportError:
            print("EasyOCR not available, install with: pip install easyocr")
            return ""
        except Exception as e:
            print(f"EasyOCR failed: {e}")
            return ""
    
    def _extract_openai(self, image_path: str) -> str:
        """Extract text using OpenAI Vision API."""
        try:
            from openai import OpenAI
            import base64
            
            client = OpenAI(api_key=self.api_key)
            
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = client.chat.completions.create(
                model=config.AIConfig.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all visible text from this image. Return only the text, no explanations."
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
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI OCR failed: {e}")
            return ""
    
    def _detect_sensitive_fields(self, text: str) -> Dict[str, List[str]]:
        """Detect sensitive information patterns in text."""
        detected = {}
        
        for field_name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected[field_name] = matches
        
        return detected
    
    def _mask_sensitive_text(self, text: str, detected_fields: Dict) -> str:
        """
        Mask sensitive information in text.
        
        Preserves format but replaces sensitive data with asterisks.
        """
        masked_text = text
        
        for field_name, matches in detected_fields.items():
            for match in matches:
                # Preserve first and last characters, mask middle
                if len(match) > 4:
                    masked = match[:2] + "*" * (len(match) - 4) + match[-2:]
                else:
                    masked = "*" * len(match)
                
                masked_text = masked_text.replace(match, masked)
        
        return masked_text
    
    def generate_verification_questions(self, ocr_result: Dict, 
                                       item_context: Dict) -> List[str]:
        """
        Generate private verification questions based on OCR results.
        
        These questions help verify ownership without exposing sensitive data.
        """
        questions = []
        detected = ocr_result.get("detected_fields", {})
        
        # If student ID detected
        if "student_id" in detected:
            questions.append("What are the first two characters of your student ID?")
        
        # If phone detected
        if "phone" in detected:
            questions.append("What are the last 4 digits of the phone number on the item?")
        
        # If specific text detected
        raw_text = ocr_result.get("raw_text", "")
        if raw_text and len(raw_text) > 10:
            # Extract a distinctive word or phrase
            words = re.findall(r"[A-Za-z]{4,}", raw_text)
            if words:
                distinctive_word = words[0]
                questions.append(f"What word starting with '{distinctive_word[0]}' appears on the item?")
        
        # Add context-based questions
        if item_context.get("brand"):
            questions.append(f"What brand is visible on the item?")
        
        if item_context.get("color"):
            questions.append(f"What is the primary color of the item?")
        
        return questions[:5]  # Limit to 5 questions
    
    def is_sensitive_content(self, text: str) -> bool:
        """Check if text contains sensitive information."""
        detected = self._detect_sensitive_fields(text)
        return bool(detected)
