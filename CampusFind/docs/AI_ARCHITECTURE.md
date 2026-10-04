# CampusFind AI Architecture

## Overview

CampusFind implements a modular, explainable multimodal AI engine for lost and found item matching. The system is designed with modularity, fallback support, and explainability as core principles.

## Design Principles

1. **Modularity**: Each AI service is independent and can be replaced without affecting others
2. **Fallback Support**: Three-level fallback architecture ensures system works even when external APIs fail
3. **Explainability**: All AI decisions are accompanied by detailed explanations and uncertainty quantification
4. **Privacy First**: Sensitive data is automatically masked and never exposed publicly
5. **No Auto-Approval**: AI provides recommendations but human verification is always required
6. **Model Versioning**: All AI results track model versions for auditing and debugging

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application Layer                  │
│  (app.py - Routes, API Endpoints, Business Logic)          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Vision     │ │  Embeddings  │ │   Matching   │
│   Analyzer   │ │   Service    │ │   Engine     │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│     OCR      │ │    Search    │ │  Assistant   │
│   Service    │ │   Service    │ │   Service    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Anomaly    │ │Recommendation│ │  Confidence  │
│  Detector    │ │   Engine     │ │   Engine     │
└──────────────┘ └──────────────┘ └──────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  SQLite Database │
              │  (AI metadata)   │
              └──────────────────┘
```

## Service Modules

### 1. Vision Analyzer (`services/ai/vision.py`)

**Purpose**: Advanced image analysis for item understanding

**Features**:
- Object type detection
- Category classification
- Color detection (primary and secondary)
- Brand/logo identification
- Visual feature extraction
- Condition assessment
- Background/location clues

**Providers**:
- **OpenAI Vision API**: GPT-4 Vision for advanced analysis
- **Local Fallback**: Basic color detection and feature extraction

**Output**: Structured item fingerprint with confidence scores

```python
result = {
    "object_type": "backpack",
    "category": "Bag",
    "primary_color": "Black",
    "secondary_color": "Blue",
    "brand": "Nike",
    "features": ["front zipper pocket", "side pockets"],
    "condition": "Good",
    "confidence_score": 0.85,
    "analysis_method": "api"
}
```

### 2. Embedding Service (`services/ai/embeddings.py`)

**Purpose**: Generate and compare embeddings for semantic similarity

**Features**:
- Image embeddings using CLIP or OpenAI Vision
- Text embeddings using OpenAI or sentence-transformers
- Cosine similarity calculation
- Embedding caching for performance
- Multi-provider support

**Providers**:
- **OpenAI**: text-embedding-3-small, image-embedding-alpha
- **CLIP**: OpenAI's Contrastive Language-Image Pre-training
- **Sentence Transformers**: all-MiniLM-L6-v2 (local)
- **Local Fallback**: Basic feature vectors

**Use Cases**:
- Image similarity matching
- Semantic text search
- Multimodal similarity

### 3. Multimodal Matcher (`services/ai/matching.py`)

**Purpose**: Core matching engine combining multiple signals

**Scoring Components** (configurable weights):
- Image similarity: 30%
- Text semantics: 20%
- Visual attributes: 10%
- OCR similarity: 10%
- Category match: 10%
- Location proximity: 10%
- Date/time proximity: 5%
- Brand/features: 5%

**Features**:
- Temporal reasoning (time proximity scoring)
- Location intelligence (campus location synonyms)
- Explainable matching with evidence
- Uncertainty quantification
- Confidence scoring (separate from similarity)

**Output**:
```python
{
    "overall_score": 85.2,
    "confidence": 78.5,
    "confidence_level": "HIGH",
    "breakdown": {
        "image": 90.0,
        "text_semantics": 75.0,
        "location": 80.0,
        "date_time": 70.0,
        "category": 100.0,
        "visual_attributes": 60.0
    },
    "evidence": ["Same category", "Similar visual appearance"],
    "uncertainties": ["Brand uncertain"],
    "explanation": "These reports may refer to the same item because..."
}
```

### 4. OCR Service (`services/ai/ocr.py`)

**Purpose**: Extract text from images with privacy protection

**Features**:
- Text extraction from images
- Privacy masking for sensitive data (student IDs, phone numbers, emails)
- Sensitive pattern detection
- Verification question generation

**Providers**:
- **Tesseract**: Local OCR engine
- **EasyOCR**: Deep learning-based OCR
- **OpenAI Vision**: GPT-4 Vision OCR

**Privacy Protection**:
- Sensitive patterns: student IDs, phone numbers, emails, roll numbers
- Masking format: `23IT123456` → `23IT******`
- Public exposure: Only shows "Student ID detected" (not actual number)
- Admin-only access: Full OCR results visible only to admins

### 5. Semantic Search (`services/ai/semantic_search.py`)

**Purpose**: Natural language query processing

**Features**:
- Natural language query parsing
- Structured filter extraction (type, color, location, timeframe)
- Semantic similarity search
- Query completion suggestions

**Supported Queries**:
- "black backpack lost in library"
- "found keys near cse block yesterday"
- "blue wallet with red tag"

### 6. AI Assistant (`services/ai/assistant.py`)

**Purpose**: Conversational reporting interface

**Features**:
- Progressive form filling through conversation
- Information extraction from natural language
- Context-aware question generation
- Missing field detection

**Example Conversation**:
```
User: "I lost my black backpack in the library"
Assistant: "Can you tell me more about the backpack? Any distinctive features?"
User: "It has a Nike logo and a front zipper pocket"
Assistant: "I have all the information needed. Please review and submit."
```

### 7. Anomaly Detector (`services/ai/anomaly.py`)

**Purpose**: Detect suspicious activity and duplicates

**Features**:
- Duplicate report detection
- Claim risk analysis
- Suspicious activity detection
- Fraud flagging

**Risk Factors**:
- Short verification answers
- Generic answer patterns
- Multiple recent claims
- Rejected claims history
- New account
- Immediate claiming after report

### 8. Recommendation Engine (`services/ai/recommendations.py`)

**Purpose**: Personalized match feed for users

**Features**:
- Personalized match recommendations based on user's lost items
- Real-time notifications for new potential matches
- Match relevance scoring
- User-specific feed generation

### 9. Confidence Engine (`services/ai/confidence.py`)

**Purpose**: Calculate confidence scores with uncertainty

**Features**:
- Confidence vs similarity separation
- Evidence quality assessment
- Uncertainty quantification
- Confidence level classification (HIGH/MEDIUM/LOW/VERY LOW)

**Key Concept**: Confidence ≠ Similarity
- **Similarity**: How similar items appear based on raw scores
- **Confidence**: How certain we are that this is actually a match

## Database Schema for AI

### Items Table (AI Columns)
```sql
image_embedding BLOB,           -- Image embedding vector
text_embedding BLOB,            -- Text embedding vector
ocr_text TEXT,                  -- Raw OCR text
ocr_masked TEXT,                -- Masked OCR text
item_fingerprint TEXT,          -- JSON item fingerprint
ai_model_version TEXT           -- Model version used
```

### AI Analysis Table
```sql
item_id INTEGER UNIQUE,
suggested_category TEXT,
suggested_color TEXT,
suggested_brand TEXT,
visual_characteristics TEXT,
item_fingerprint TEXT,
confidence_score REAL,
analysis_method TEXT DEFAULT 'local',
model_version TEXT,
created_at TEXT
```

### Item Matches Table (AI Columns)
```sql
overall_score REAL NOT NULL,
confidence_score REAL,
text_similarity REAL,
image_similarity REAL,
ocr_similarity REAL,
location_similarity REAL,
date_similarity REAL,
category_match REAL,
visual_similarity REAL,
explanation TEXT,
evidence TEXT,
uncertainties TEXT,
model_version TEXT,
human_feedback TEXT DEFAULT 'pending',
human_feedback_at TEXT
```

## Configuration

All AI configuration is centralized in `config.py` and loaded from environment variables:

```python
class AIConfig:
    AI_PROVIDER = "openai"
    OPENAI_API_KEY = ""
    EMBEDDING_PROVIDER = "openai"
    OCR_PROVIDER = "tesseract"
    MATCHING_WEIGHTS = {...}
    CONFIDENCE_THRESHOLDS = {...}
    MODEL_VERSIONS = {...}
    PRIVACY_SETTINGS = {...}
```

## Fallback Architecture

### Level 1: Advanced External AI
- OpenAI Vision API for image analysis
- OpenAI embeddings for text/image similarity
- CLIP for multimodal understanding

### Level 2: Local ML Models
- sentence-transformers for text embeddings
- Basic image features for similarity
- Tesseract for OCR

### Level 3: Rule-Based
- Text similarity (token overlap)
- Exact string matching
- Basic color detection

**Automatic Fallback**: If Level 1 fails, automatically falls back to Level 2, then Level 3.

## Model Versioning

Every AI result records:
- Model name (e.g., gpt-4o-mini, CLIP)
- Model version (e.g., 1.0, 2.0)
- Analysis timestamp
- Analysis method (api/local)

**Benefits**:
- Track which models perform best
- Debug issues with specific versions
- Audit AI decisions
- Roll back to previous versions

## Human Feedback Loop

Users can confirm or reject AI matches. This feedback is stored and used to:
- Calculate AI accuracy metrics
- Improve future matching
- Provide explainable AI performance data

**Feedback States**:
- `pending`: No feedback yet
- `confirmed`: User confirmed the match
- `rejected`: User rejected the match

## Privacy & Security

### Privacy Protection
- OCR results automatically masked for sensitive data
- Public listings only show "Student ID detected" (not actual number)
- Only admins can view full OCR results
- Verification questions avoid exposing sensitive data

### Security
- No hardcoded API keys
- All sensitive data in environment variables
- No automatic claim approvals
- Human verification always required
- CSRF protection on all forms

## API Endpoints

### AI Endpoints
- `POST /api/ai/analyze-image` - Analyze uploaded image
- `POST /api/ai/semantic-search` - Semantic search
- `POST /api/ai/assistant` - Conversational assistant
- `POST /api/ai/detect-duplicate` - Duplicate detection
- `POST /api/ai/match-feedback` - Human feedback
- `POST /api/ai/claim-risk` - Claim risk analysis

### Pages
- `/ai-lab` - AI demo page
- `/ai-explanation` - AI explanation page
- `/admin/ai` - AI analytics dashboard

## Performance Optimization

- Embedding caching to reduce API calls
- Configurable max candidate retrieval
- Batch processing for embeddings
- Lazy-loading of ML models
- Image downsampling for faster processing

## Testing

Run tests with:
```bash
pytest tests/test_ai_services.py
```

## Future Enhancements

- Campus graph intelligence for location reasoning
- More advanced OCR models
- Real-time model retraining
- A/B testing for model versions
- Advanced anomaly detection patterns
