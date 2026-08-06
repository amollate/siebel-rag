# Deployment Guide — Siebel 6 RAG Solution

## Deploying to Streamlit Cloud (Free Hosting)

Streamlit Cloud offers a free tier for hosting Streamlit apps. Follow these steps to deploy:

### Prerequisites
- A GitHub account
- Git installed on your machine
- The `siebel-rag` project directory ready

### Step 1: Push Code to GitHub

```bash
cd /Users/richalate/Documents/UIPath/Kilo/siebel-rag

# Initialize git repo (if not already)
git init
git add .
git commit -m "Initial commit: Siebel 6 RAG solution"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/siebel-rag.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Sign in with your GitHub account
3. Click "New app" or "Create app"
4. Select the repository: `YOUR_USERNAME/siebel-rag`
5. Set the main file path to: `streamlit_app.py`
6. Click "Deploy"

Streamlit Cloud will automatically:
- Detect `requirements.txt` and install dependencies
- Run `streamlit run streamlit_app.py`
- Provide a public URL (e.g., `https://siebel-rag-yourusername.streamlit.app`)

### Step 3: Run Ingestion

After the app is deployed, you need to run ingestion first:

1. Open the deployed app in your browser
2. The sidebar will show "Pipeline initialized"
3. Click "Reset Knowledge Base" if needed
4. The app will use pre-seeded data (see below)

### Alternative: Deploy on Hugging Face Spaces (Free)

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose "Streamlit" as the SDK
4. Upload all project files
5. Hugging Face will auto-build and deploy

### Alternative: Deploy on Render (Free Tier)

1. Go to https://render.com
2. Connect your GitHub repo
3. Create a new Web Service
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `streamlit run streamlit_app.py --server.port $PORT`
6. Deploy

## Environment Variables for Production

Set these in your hosting platform's environment settings:

| Variable | Value | Description |
|----------|-------|-------------|
| `USE_OLLAMA` | `false` | Use OpenAI for embeddings/generation |
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `LOG_LEVEL` | `WARNING` | Reduce log noise in production |

## Notes

- The first deployment will take 2-5 minutes to install dependencies
- ChromaDB persists data between restarts on Streamlit Cloud
- Free tiers have limited compute — ingestion may be slow
- For production use, consider using OpenAI embeddings for better quality