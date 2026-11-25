import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from analyzer.github_client import GitHubClient
from analyzer.groq_engine import GroqAnalyzerEngine

app = FastAPI(
    title="GitHub Repo Analyzer",
    description="Intelligent GitHub Repository Analyzer powered by Groq's high-speed LLMs",
    version="1.0.0"
)

# In-memory storage for analyzed repos
REPO_CACHE: Dict[str, Dict[str, Any]] = {}

api_router = APIRouter()


class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub URL or owner/repo shorthand")
    groq_api_key: Optional[str] = Field(None, description="Groq API key (optional if set in env)")
    github_token: Optional[str] = Field(None, description="GitHub token (optional, increases rate limit)")
    model: Optional[str] = Field("llama-3.3-70b-versatile", description="Groq model to use")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    repo_identifier: str = Field(..., description="owner/repo identifier")
    messages: List[ChatMessage]
    groq_api_key: Optional[str] = None
    model: Optional[str] = "llama-3.3-70b-versatile"


@api_router.get("/health")
def health_check():
    has_env_groq = bool(os.getenv("GROQ_API_KEY"))
    has_env_github = bool(os.getenv("GITHUB_TOKEN"))
    return {
        "status": "online",
        "has_groq_env_key": has_env_groq,
        "has_github_env_token": has_env_github,
        "default_model": os.getenv("GROQ_MODEL", GroqAnalyzerEngine.DEFAULT_MODEL),
        "supported_models": GroqAnalyzerEngine.SUPPORTED_MODELS
    }


@api_router.get("/sample-repos")
def get_sample_repos():
    return [
        {
            "name": "FastAPI",
            "repo": "fastapi/fastapi",
            "description": "Fast, high-performance web framework for building APIs with Python 3.8+."
        },
        {
            "name": "Flask",
            "repo": "pallets/flask",
            "description": "The Python micro framework for building web applications."
        },
        {
            "name": "Express",
            "repo": "expressjs/express",
            "description": "Fast, unopinionated, minimalist web framework for Node.js."
        },
        {
            "name": "Tailwind CSS",
            "repo": "tailwindlabs/tailwindcss",
            "description": "A utility-first CSS framework for rapid UI development."
        },
        {
            "name": "Zod",
            "repo": "colinhacks/zod",
            "description": "TypeScript-first schema validation with static type inference."
        },
        {
            "name": "SQLModel",
            "repo": "fastapi/sqlmodel",
            "description": "SQL databases in Python, designed for simplicity, compatibility, and robustness."
        }
    ]


@api_router.post("/analyze")
def analyze_repo(req: AnalyzeRequest):
    groq_key = req.groq_api_key or os.getenv("GROQ_API_KEY")
    if not groq_key or not groq_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Missing Groq API Key. Please provide your free Groq API Key from https://console.groq.com."
        )

    github_token = req.github_token or os.getenv("GITHUB_TOKEN")

    try:
        owner, repo = GitHubClient.parse_repo_identifier(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cache_key = f"{owner.lower()}/{repo.lower()}"

    # 1. Fetch GitHub data
    try:
        gh_client = GitHubClient(token=github_token)
        repo_data = gh_client.collect_repo_context(owner, repo)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub repository data: {str(e)}")

    # 2. Analyze with Groq LLM
    try:
        engine = GroqAnalyzerEngine(api_key=groq_key, model=req.model)
        analysis_result = engine.analyze_repository(repo_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq Analysis Error: {str(e)}")

    # Save to memory cache for conversational follow-ups
    REPO_CACHE[cache_key] = {
        "repo_data": repo_data,
        "analysis": analysis_result
    }

    return {
        "repo_identifier": cache_key,
        "repo_info": repo_data["repo_info"],
        "languages": repo_data["languages"],
        "ci_summary": repo_data["ci_summary"],
        "recent_commits": repo_data["recent_commits"],
        "tree_stats": {
            "total_items": repo_data["tree"]["total_items_in_repo"],
            "sampled_files": repo_data["tree"]["sampled_files_count"],
            "files": repo_data["tree"]["files"]
        },
        "manifests_detected": list(repo_data["manifests"].keys()),
        "analysis": analysis_result
    }


@api_router.post("/chat")
def chat_repo(req: ChatRequest):
    groq_key = req.groq_api_key or os.getenv("GROQ_API_KEY")
    if not groq_key or not groq_key.strip():
        raise HTTPException(status_code=400, detail="Missing Groq API Key.")

    cache_key = req.repo_identifier.lower().strip()
    cached = REPO_CACHE.get(cache_key)

    if not cached:
        try:
            owner, repo = GitHubClient.parse_repo_identifier(cache_key)
            gh_client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
            repo_data = gh_client.collect_repo_context(owner, repo)
            cached = {"repo_data": repo_data, "analysis": None}
            REPO_CACHE[cache_key] = cached
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Repository context not found. Please run analysis on '{req.repo_identifier}' first."
            )

    try:
        engine = GroqAnalyzerEngine(api_key=groq_key, model=req.model)
        reply = engine.chat_with_repo(
            repo_data=cached["repo_data"],
            messages=[m.model_dump() for m in req.messages],
            analysis_summary=cached.get("analysis")
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# Mount routes under both /api and root / for seamless server and serverless function compatibility
app.include_router(api_router, prefix="/api")
app.include_router(api_router)

# Serve static files
STATIC_DIR = PROJECT_ROOT / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
        return "<h1>GitHub Repo Analyzer</h1><p>Index file not found.</p>"


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Starting GitHub Repo Analyzer on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
