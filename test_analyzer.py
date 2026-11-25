"""
Test and Verification script for GitHub Repo Analyzer.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from analyzer.github_client import GitHubClient
from analyzer.groq_engine import GroqAnalyzerEngine
from fastapi.testclient import TestClient
from app import app


def test_url_parser():
    print("Testing URL parsing...")
    cases = [
        ("pallets/flask", ("pallets", "flask")),
        ("https://github.com/fastapi/fastapi", ("fastapi", "fastapi")),
        ("http://github.com/expressjs/express.git", ("expressjs", "express")),
        ("github.com/tailwindlabs/tailwindcss", ("tailwindlabs", "tailwindcss")),
        ("https://github.com/facebook/react/issues/123", ("facebook", "react")),
    ]
    for inp, expected in cases:
        result = GitHubClient.parse_repo_identifier(inp)
        assert result == expected, f"Expected {expected}, got {result} for {inp}"
    print("  [PASS] URL parsing works for all formats.")


def test_github_fetch():
    print("Testing GitHub Client on real repo (pallets/click)...")
    gh = GitHubClient()
    owner, repo = "pallets", "click"
    context = gh.collect_repo_context(owner, repo)

    assert context["repo_info"]["name"].lower() == "click"
    assert context["repo_info"]["stars"] > 1000
    assert "breakdown" in context["languages"]
    assert len(context["tree"]["files"]) > 0
    print(f"  [PASS] GitHub metadata fetched successfully: {context['repo_info']['full_name']}")
    print(f"         Stars: {context['repo_info']['stars']}, Language: {context['repo_info']['language']}")
    print(f"         Files sampled: {context['tree']['sampled_files_count']}, Manifests: {list(context['manifests'].keys())}")


def test_groq_engine_validation():
    print("Testing Groq Engine validation...")
    try:
        GroqAnalyzerEngine(api_key=None)
        assert False, "Should raise ValueError when no key is provided"
    except ValueError as e:
        assert "Groq API Key is required" in str(e)
        print("  [PASS] Missing key validation caught successfully.")


def test_fastapi_endpoints():
    print("Testing FastAPI app endpoints...")
    client = TestClient(app)

    # Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    print(f"  [PASS] GET /api/health returned 200: {data}")

    # Sample repos
    res = client.get("/api/sample-repos")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) > 0
    print(f"  [PASS] GET /api/sample-repos returned {len(samples)} curated repos")

    # Missing Groq key error on analyze
    res = client.post("/api/analyze", json={"repo_url": "pallets/click"})
    assert res.status_code == 400
    assert "Missing Groq API Key" in res.json()["detail"]
    print(f"  [PASS] POST /api/analyze caught missing key with 400 status")

    # Static index page
    res = client.get("/")
    assert res.status_code == 200
    assert "RepoScope" in res.text
    print("  [PASS] GET / served index.html successfully")


if __name__ == "__main__":
    print("\n--- RUNNING REPOSCOPE TEST SUITE ---")
    test_url_parser()
    test_github_fetch()
    test_groq_engine_validation()
    test_fastapi_endpoints()
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<\n")
