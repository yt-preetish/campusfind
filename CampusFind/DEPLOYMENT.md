# Deployment Guide - CampusFind AI

## Quick Deploy to Render (Free Tier)

### Prerequisites
- GitHub account
- Render.com account (free)

### Step 1: Prepare for Deployment

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/campusfind.git
   git push -u origin main
   ```

2. **Ensure `.env` is NOT committed**
   - `.env` is already in `.gitignore`
   - Never commit your API keys

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: campusfind-ai
   - **Region**: Choose nearest to you
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m waitress --port=$PORT app:app`

5. **Environment Variables** (Add these in Render dashboard):
   ```
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-key-here
   AI_PROVIDER=openai
   ```

6. Click "Deploy Web Service"

### Step 3: Post-Deployment

1. **Seed the database** (first time only):
   - Access the deployed app
   - Register an admin account
   - Or use the seed_data.py script locally and upload the database

2. **Set up custom domain** (optional):
   - Buy a domain
   - Add in Render dashboard
   - Enable SSL (automatic)

---

## Alternative: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables
5. Deploy

---

## Alternative: PythonAnywhere

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Create a "Web" app
3. Upload code via git or drag-and-drop
4. Configure WSGI file
5. Set environment variables
6. Deploy

---

## Production Checklist

- [ ] Change demo passwords
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS (automatic on Render)
- [ ] Monitor OpenAI API usage
- [ ] Set up backups for database
- [ ] Configure email notifications (optional)
- [ ] Test all features after deployment

---

## Troubleshooting

**Database issues on deployment:**
- SQLite works fine for small deployments
- For larger scale, consider PostgreSQL migration

**API key issues:**
- Ensure OPENAI_API_KEY is set in environment variables
- Check API key has credits

**Rate limiting:**
- Adjust limits in app.py if needed
- Monitor logs for rate limit errors
