# 🔍 RepoScope: GitHub Repo Analyzer (Powered by Groq)

A high-performance GitHub Repository Analyzer powered by **Groq's Free LPU API**. RepoScope delivers comprehensive architectural blueprints, code quality and security audits, technology stack mapping, and interactive "Chat with the Repo" in seconds.

---

## ✨ Features

- **⚡ Blazing Fast Analysis via Groq LPUs**: Leverages Groq's high-speed inference on `llama-3.3-70b-versatile` (or `llama-3.1-8b-instant`), delivering full senior-level architectural reports in 1–3 seconds.
- **📊 Code Quality & Health Score (0-100)**: Evaluates repository organization, testing presence, documentation quality, and maintenance status.
- **🏛️ Architectural & Structural Mapping**: Detects software design patterns, key entry points, component structures, and indexes the repository file tree.
- **🛡️ Candid Strengths & Security Risks**: Highlights what the repository does well and identifies missing tests, outdated practices, or configuration risks.
- **💬 "Ask the Repo" (Interactive Groq Chat)**: Ask arbitrary technical questions about the repository (e.g., *"Where is authentication handled?"*, *"How does routing work?"*, *"How do I contribute?"*) with full repository context.
- **🚀 Synthesized Quickstart**: Step-by-step installation, dependency configuration, and run/test commands.
- **📥 One-Click Export**: Download reports directly as Markdown (`.md`) or structured JSON (`.json`).
- **🖥️ Dual Mode**: Run as a modern web dashboard with dark-mode UI or as a standalone terminal CLI.

---

## 🚀 Quickstart

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Groq API Key**: Get a free API key at [console.groq.com/keys](https://console.groq.com/keys). Free tier provides generous rate limits and ultra-fast inference.

### 2. Installation

Clone or navigate to the project directory:
```bash
cd C:\Users\amitd\.gemini\antigravity\scratch\github-repo-analyzer
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Edit `.env` and set your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(Note: You can also enter your Groq API key directly in the Web UI, which stores it securely in your browser's localStorage!)*

---

## 🌐 Running the Web Dashboard

Start the local server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:8000
```

Paste any public GitHub repository link (e.g. `fastapi/fastapi`, `pallets/flask`, `expressjs/express`, `tailwindlabs/tailwindcss`) or click one of the quick sample chips.

---

## 💻 Running the CLI Analyzer

Analyze any repository directly from your terminal:

```bash
# Basic analysis
python cli.py pallets/flask

# Analyze with custom model & export markdown report
python cli.py fastapi/fastapi --model llama-3.3-70b-versatile --export fastapi-audit.md

# Provide Groq API key via command flag
python cli.py expressjs/express --groq-key gsk_your_key_here
```

---

## 🛠️ Project Architecture

```
github-repo-analyzer/
├── analyzer/
│   ├── __init__.py
│   ├── github_client.py    # GitHub REST API client (metadata, tree, manifests, commits)
│   └── groq_engine.py      # Groq LLM integration (JSON structured output, Q&A chat)
├── static/
│   └── index.html          # Modern Single Page Application (Tailwind CSS, Chart.js, Marked)
├── app.py                  # FastAPI backend server & REST API
├── cli.py                  # Terminal CLI tool with colored outputs
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
└── README.md               # Documentation
```

---

## 🔑 Groq Models Supported

| Model Name | Parameter Size | Speed | Ideal For |
|------------|----------------|-------|-----------|
| `llama-3.3-70b-versatile` *(Default)* | 70B | ~250-300 t/s | Deep architectural reasoning & code quality audits |
| `llama-3.1-8b-instant` | 8B | ~800+ t/s | Near-instant queries and lower token usage |
| `mixtral-8x7b-32768` | 8x7B | ~400 t/s | Large context repositories |

---

## 📄 License
MIT License.
