# CampusFind — Smart Lost & Found Management System

An AI-powered campus lost and found platform built with Python Flask + SQLite.

## Features

### Core Functionality
- Student registration/login with role-based access (admin/student)
- Lost and found item reports with image uploads and enhanced fields
- Search and filters for browsing items with sorting options
- Claim and ownership-verification workflow
- Notifications system with type categorization
- Recovery status tracking
- Interactive campus map with Leaflet (no API key required)
- AI-powered chat assistant for natural language queries
- Personal dashboard with analytics charts
- Profile page with quick stats and actions
- My Reports page with filtering
- Matches page for viewing potential matches
- Beautiful error pages (404, 403, 500)

### Multimodal AI Engine
- **Vision AI**: Advanced image analysis with OpenAI Vision API and local fallback
  - Object type detection
  - Category classification
  - Color detection
  - Brand/logo identification
  - Visual feature extraction
  - Condition assessment
- **Embeddings**: Image and text embeddings for semantic similarity
  - CLIP-compatible models
  - OpenAI text embeddings
  - Local fallback features
  - Cosine similarity calculation
- **Multimodal Matching**: Advanced matching engine with configurable weights
  - Image similarity (30%)
  - Text semantics (20%)
  - Visual attributes (10%)
  - OCR similarity (10%)
  - Category match (10%)
  - Location proximity (10%)
  - Date/time proximity (5%)
  - Brand/features (5%)
- **Explainable AI**: Detailed match breakdown with evidence and uncertainties
- **OCR with Privacy**: Text extraction with automatic sensitive data masking
- **Conversational Search**: Natural language query processing
- **AI Assistant**: Conversational reporting assistant
- **Duplicate Detection**: AI-powered duplicate report detection
- **Claim Risk Analysis**: Fraud detection and suspicious activity flagging
- **Personalized Feed**: AI-powered match recommendations
- **Confidence Engine**: Separate confidence scoring from similarity

### Security & Handover
- **QR Code Handover System**: Secure handover confirmation with unique handover IDs and QR codes for both finder and claimant
- **CSRF Protection**: Cross-site request forgery protection using Flask-WTF
- **Environment Configuration**: Secure handling of sensitive data via environment variables

### Admin Dashboard 2.0
- **Analytics Charts**: Visual analytics with Chart.js including:
  - Lost vs Found distribution (doughnut chart)
  - Reports by category (bar chart)
  - Top locations (horizontal bar chart)
  - Recovery trend over 7 days (line chart)
- **AI Analytics Dashboard**: AI performance metrics
  - Total AI analyses
  - API vs local fallback usage
  - Match accuracy with human feedback
  - Average confidence scores
  - Recent matches with feedback
- Enhanced statistics with pending claims tracking
- Claim approval/rejection with automatic handover record generation

### AI Demo & Explanation
- **AI Lab**: Interactive demo page for testing image similarity
- **AI Explanation Page**: Comprehensive explanation of how the AI works (perfect for project vivas)

### Modern UI/UX
- Responsive dark theme design with glassmorphism effects
- Smooth animations and transitions
- Progress bars for match confidence visualization
- Status badges and visual indicators
- Mobile-friendly layout
- Premium error pages (404, 403, 500)
- Interactive charts with Chart.js
- Filterable report lists
- Real-time AI suggestions in report form

## Demo accounts

After running `seed_data.py`, the following demo accounts are available:

**Admin**
- Email: admin@campusfind.local
- Password: admin123

**Student**
- Email: student@campusfind.local
- Password: student123

**Additional Demo Users**
- Email: john@campus.edu / Password: john123
- Email: jane@campus.edu / Password: jane123
- Email: mike@campus.edu / Password: mike123

**Important**: Change these credentials before real deployment.

## Setup

### Prerequisites
- Python 3.8 or higher
- pip

### Installation

1. Clone or download the project
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Configure environment variables (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
6. Initialize the database:
   ```bash
   python app.py
   ```
7. (Optional) Seed demo data:
   ```bash
   python seed_data.py
   ```
8. Start the application:
   ```bash
   python app.py
   ```
9. Open in browser:
   ```
   http://127.0.0.1:5000
   ```

The SQLite database is automatically created on first run with demo accounts. Use `seed_data.py` to populate with sample items for testing.

## Project Structure

```
CampusFind/
├── app.py                      # Main Flask application
├── config.py                   # Centralized AI configuration
├── seed_data.py               # Demo data seeding script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── campusfind.db              # SQLite database (created automatically)
├── models/                    # Database models
│   ├── __init__.py
│   └── database.py           # Database connection and initialization
├── services/                  # Business logic services
│   ├── __init__.py
│   ├── matching.py           # Legacy matching (backward compatibility)
│   ├── image_analyzer.py     # Legacy image analyzer (backward compatibility)
│   └── search.py             # Legacy search (backward compatibility)
├── services/ai/               # Multimodal AI engine
│   ├── __init__.py
│   ├── vision.py             # Image analysis with OpenAI Vision API
│   ├── embeddings.py         # Image and text embeddings
│   ├── matching.py           # Multimodal matching engine
│   ├── ocr.py                # OCR with privacy masking
│   ├── assistant.py          # AI recovery assistant
│   ├── anomaly.py            # Duplicate detection & risk analysis
│   ├── recommendations.py    # Personalized match feed
│   └── confidence.py         # Confidence engine
├── templates/                 # Jinja2 templates
│   ├── base.html             # Base template with navigation
│   ├── index.html            # Homepage
│   ├── dashboard.html        # User dashboard with charts
│   ├── profile.html          # User profile page
│   ├── my_reports.html       # My reports with filtering
│   ├── matches.html          # Potential matches page
│   ├── chat.html             # AI chat assistant
│   ├── map.html              # Interactive campus map
│   ├── admin.html            # Admin dashboard with charts
│   ├── admin_ai.html         # AI analytics dashboard
│   ├── report.html           # Enhanced report form with AI analysis
│   ├── item_detail.html      # Item details with match breakdown
│   ├── handover.html         # QR handover confirmation
│   ├── items.html            # Browse items with sorting
│   ├── login.html            # Login form
│   ├── register.html         # Registration form
│   ├── notifications.html    # Notifications list
│   ├── ai_lab.html           # AI demo page
│   ├── ai_explanation.html   # AI explanation page
│   ├── 404.html             # Custom 404 error page
│   ├── 403.html             # Custom 403 error page
│   └── 500.html             # Custom 500 error page
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Main stylesheet with glassmorphism
│   ├── js/
│   │   └── app.js            # Client-side JavaScript
│   └── uploads/              # Uploaded images
└── docs/                      # Documentation
    └── AI_ARCHITECTURE.md     # Detailed AI architecture documentation
```

## AI Architecture

### Modular Design
The AI system is designed with modularity in mind. Each service can be replaced independently:

- **Vision Analyzer**: Handles image analysis with OpenAI Vision API or local fallback
- **Embedding Service**: Manages image and text embeddings with multiple provider support
- **Multimodal Matcher**: Core matching engine with configurable weights
- **OCR Service**: Text extraction with privacy masking
- **Semantic Search**: Natural language query processing
- **AI Assistant**: Conversational reporting interface
- **Anomaly Detector**: Duplicate detection and risk analysis
- **Recommendation Engine**: Personalized match feeds
- **Confidence Engine**: Confidence scoring with uncertainty quantification

### Fallback Architecture
The system supports three levels of fallback:

1. **Level 1**: Advanced external AI (OpenAI Vision, CLIP)
2. **Level 2**: Local ML models (sentence-transformers, basic features)
3. **Level 3**: Rule-based matching (text similarity, exact matches)

If an API call fails, the system automatically falls back to the next level.

### Configuration
All AI configuration is managed through environment variables in `.env`:

```bash
# AI Provider Selection
AI_PROVIDER=openai  # openai, local, hybrid

# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini

# Embedding Configuration
EMBEDDING_PROVIDER=openai  # openai, local_clip, sentence_transformers
EMBEDDING_MODEL=text-embedding-3-small

# OCR Configuration
OCR_PROVIDER=tesseract  # tesseract, openai, easyocr
OCR_ENABLED=true

# Matching Weights (configurable)
WEIGHT_IMAGE=0.30
WEIGHT_TEXT_SEMANTICS=0.20
WEIGHT_VISUAL_ATTRIBUTES=0.10
WEIGHT_OCR=0.10
WEIGHT_CATEGORY=0.10
WEIGHT_LOCATION=0.10
WEIGHT_DATE_TIME=0.05
WEIGHT_BRAND_FEATURES=0.05

# Confidence Thresholds
CONFIDENCE_THRESHOLD_HIGH=0.85
CONFIDENCE_THRESHOLD_MEDIUM=0.70
CONFIDENCE_THRESHOLD_LOW=0.50

# Model Versioning
VISION_MODEL_VERSION=1.0
EMBEDDING_MODEL_VERSION=1.0
MATCHING_ENGINE_VERSION=2.0

# Privacy Settings
PRIVACY_MASK_SENSITIVE=true
PRIVACY_EXPOSE_OCR=false

# Performance Settings
MAX_CANDIDATE_RETRIEVAL=50
MAX_MATCH_RESULTS=10
ENABLE_EMBEDDING_CACHE=true

# Fallback Settings
FALLBACK_LEVEL=auto  # auto, level1, level2, level3
ENABLE_LOCAL_FALLBACK=true
```

### OpenAI Vision API (Optional)
To enable AI image analysis with OpenAI Vision API:
1. Get an API key from https://platform.openai.com/
2. Add to your `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```
3. The system will automatically use the API when available, falling back to local analysis if the key is not configured.

### Local Fallback
Without an API key, the system uses local image processing for basic color detection and feature extraction.

## Smart Matching Algorithm

The matching engine uses a weighted scoring system:
- **Image similarity**: 30%
- **Text semantics**: 20%
- **Visual attributes**: 10%
- **OCR similarity**: 10%
- **Category match**: 10%
- **Location proximity**: 10%
- **Date/time proximity**: 5%
- **Brand/features**: 5%

The system automatically redistributes weights when certain signals are unavailable.

## Security Features

- **CSRF Protection**: All forms protected with CSRF tokens via Flask-WTF
- **Password Hashing**: User passwords hashed using Werkzeug security
- **Session Management**: Secure session handling with Flask
- **Environment Variables**: Sensitive data stored in environment variables, never committed to code
- **SQL Injection Prevention**: Parameterized queries throughout
- **Privacy Masking**: OCR results automatically masked for sensitive data
- **No Auto-Approval**: AI never automatically approves claims; human verification always required

## API Endpoints

### AI Endpoints
- `POST /api/ai/analyze-image` - Analyze uploaded image with AI
- `POST /api/ai/semantic-search` - Perform semantic search
- `POST /api/ai/assistant` - AI conversational assistant
- `POST /api/ai/detect-duplicate` - Detect duplicate reports
- `POST /api/ai/match-feedback` - Submit human feedback on matches
- `POST /api/ai/claim-risk` - Analyze claim risk

### Pages
- `/` - Homepage
- `/login` - Login form
- `/register` - Registration form
- `/dashboard` - User dashboard with charts and stats
- `/profile` - User profile with quick actions
- `/my-reports` - User's reports with filtering
- `/matches` - Potential matches for user's lost items
- `/chat` - AI chat assistant
- `/map` - Interactive campus map with Leaflet
- `/items` - Browse all items with search and filters
- `/report/lost` - Report lost item form
- `/report/found` - Report found item form
- `/item/<id>` - Item details with match breakdown
- `/notifications` - User notifications
- `/handover/<id>` - QR handover confirmation
- `/admin` - Admin dashboard (admin only)
- `/admin/ai` - AI analytics dashboard (admin only)
- `/ai-lab` - AI demo page for testing image similarity
- `/ai-explanation` - Comprehensive AI explanation

### Legacy Endpoints
- `GET /api/match/<item_id>` - Get potential matches for an item
- `GET /handover/<handover_id>/qr` - Download QR code for handover

## Model Versioning

Every AI result records:
- Model name (e.g., gpt-4o-mini, CLIP)
- Model version (e.g., 1.0, 2.0)
- Analysis timestamp

This enables:
- Tracking which models perform best
- Debugging issues with specific versions
- Auditing AI decisions
- Rolling back to previous versions if needed

## Human Feedback Loop

Users can confirm or reject AI matches. This feedback is stored and used to:
- Calculate AI accuracy metrics
- Improve future matching
- Provide explainable AI performance data

## License

This project is provided as-is for educational purposes.

## Contributing

This is a demonstration project. Feel free to fork and modify for your campus needs.
