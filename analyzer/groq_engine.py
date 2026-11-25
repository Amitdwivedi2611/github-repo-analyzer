import os
import json
import re
from typing import Dict, Any, List, Optional
from groq import Groq


class GroqAnalyzerEngine:
    """Orchestrates code analysis and repo intelligence using Groq's fast LLMs."""

    SUPPORTED_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL") or self.DEFAULT_MODEL
        if not self.api_key:
            raise ValueError(
                "Groq API Key is required. Please provide it via the UI, set GROQ_API_KEY in your .env file, "
                "or pass it as an argument. You can obtain a free key at https://console.groq.com."
            )
        self.client = Groq(api_key=self.api_key)

    def _prepare_context_prompt(self, repo_data: Dict[str, Any]) -> str:
        """Formats repository metadata, files, and tree into a structured LLM prompt context."""
        info = repo_data.get("repo_info", {})
        languages = repo_data.get("languages", {}).get("breakdown", [])
        readme = repo_data.get("readme")
        tree = repo_data.get("tree", {})
        manifests = repo_data.get("manifests", {})
        ci_summary = repo_data.get("ci_summary", {})
        commits = repo_data.get("recent_commits", [])

        lang_str = ", ".join([f"{l['language']} ({l['percentage']}%)" for l in languages[:6]]) or "Not detected"

        # Tree sample
        sample_files = tree.get("files", [])[:120]
        tree_str = "\n".join(sample_files) if sample_files else "No tree files available"

        # Manifest contents
        manifest_text_parts = []
        for name, content in manifests.items():
            manifest_text_parts.append(f"--- File: {name} ---\n{content[:2500]}")
        manifest_str = "\n\n".join(manifest_text_parts) if manifest_text_parts else "No key manifests found"

        # Recent commit subjects
        commit_str = "\n".join([f"- [{c.get('sha')}] {c.get('message')} (by {c.get('author')})" for c in commits[:5]]) or "None"

        readme_text = readme.get("content", "No README available") if readme else "No README available"

        return f"""
REPOSITORY METADATA:
- Full Name: {info.get('full_name')}
- Description: {info.get('description')}
- Stars: {info.get('stars')} | Forks: {info.get('forks')} | Open Issues: {info.get('open_issues')}
- Primary Language: {info.get('language')}
- Languages Breakdown: {lang_str}
- License: {info.get('license')} ({info.get('license_name')})
- Default Branch: {info.get('default_branch')}
- Topics / Tags: {', '.join(info.get('topics', []))}
- CI/CD Workflows: {'Yes (' + ', '.join(ci_summary.get('workflow_files', [])) + ')' if ci_summary.get('has_github_actions') else 'None detected'}

RECENT COMMITS:
{commit_str}

REPOSITORY FILE TREE (Sample of {len(sample_files)} files):
{tree_str}

KEY CONFIGURATION MANIFESTS:
{manifest_str}

README EXCERPT:
{readme_text}
"""

    def analyze_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs comprehensive architectural, code quality, and setup analysis using Groq.
        """
        repo_info = repo_data.get("repo_info", {})
        context_str = self._prepare_context_prompt(repo_data)

        system_prompt = (
            "You are an elite principal software architect and veteran code reviewer analyzing a GitHub repository. "
            "Your analysis must be insightful, concrete, candid, and technically precise based strictly on the provided "
            "repository metadata, file tree, manifests, and documentation.\n\n"
            "Return a strictly valid JSON object matching the requested schema without markdown backticks or extra text."
        )

        user_prompt = f"""
Analyze this GitHub repository based on the following extracted context:

{context_str}

Provide a comprehensive, senior-level analysis in JSON format with exactly the following keys:
{{
  "executive_summary": "Crisp 2-3 sentence overview describing what this project does, its target audience, and core value proposition.",
  "project_type": "Classification, e.g., 'Web Application', 'CLI Tool', 'Library / SDK', 'API Service', 'DevOps Tool', etc.",
  "tech_stack": [
    "Array of detected languages, frameworks, major libraries, databases, and tools (e.g. ['TypeScript', 'React', 'TailwindCSS', 'Vite'])"
  ],
  "key_features": [
    "Top 4-6 primary features or capabilities offered by the project"
  ],
  "architecture": {{
    "overview": "Clear explanation of how the repository is structured, core modules/packages, and data flow.",
    "entry_points": ["Key entry point files or main controllers (e.g. 'src/index.ts', 'app.py', 'cmd/main.go')"],
    "design_patterns": ["Observed patterns or structural paradigms (e.g. 'Clean Architecture', 'MVC', 'Plugin System', 'Monorepo')"]
  }},
  "quality_assessment": {{
    "health_score": 85, // Integer 0 to 100 representing overall repo health based on structure, CI/CD, tests, docs, and maintenance
    "health_verdict": "Short 3-5 word verdict (e.g. 'Production Ready & Well Maintained')",
    "strengths": [
      "3-5 specific strengths observed in the project structure, tooling, or docs"
    ],
    "weaknesses": [
      "2-4 candid areas for improvement (e.g. missing unit tests, outdated dependencies, lacking error handling, thin docs)"
    ],
    "testing_observed": "Assessment of testing practices (e.g., 'Good test suite with pytest found in tests/', 'No tests observed', etc.)",
    "documentation_quality": "Rating: 'Excellent', 'Good', 'Fair', or 'Poor', accompanied by brief explanation."
  }},
  "security_and_maintenance": {{
    "security_considerations": [
      "Potential security considerations, secrets handling, dependency risks, or safe practices to keep in mind"
    ],
    "maintenance_status": "Assessment based on recent commits, issue counts, and activity (e.g. 'Actively Maintained', 'Stable', 'Stale')"
  }},
  "setup_and_quickstart": {{
    "prerequisites": ["List of requirements (e.g. Python 3.10+, Node.js 18+, Docker)"],
    "install_steps": ["Step 1 command", "Step 2 command"],
    "run_command": "Command to run or develop locally (e.g. 'npm run dev' or 'python app.py')",
    "test_command": "Command to run tests (if applicable, e.g. 'pytest' or 'npm test')"
  }}
}}
"""

        try:
            # We attempt json_object mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            result = json.loads(raw_content)
        except Exception as e:
            # Fallback parsing in case model wrapped with backticks or json mode had issue
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                raw_content = response.choices[0].message.content.strip()
                # Clean markdown codeblocks
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
                result = json.loads(cleaned)
            except Exception as inner_e:
                raise RuntimeError(f"Groq analysis failed: {str(e)} | Secondary error: {str(inner_e)}")

        # Attach metadata to result
        result["model_used"] = self.model
        result["repo_full_name"] = repo_info.get("full_name")
        return result

    def chat_with_repo(
        self,
        repo_data: Dict[str, Any],
        messages: List[Dict[str, str]],
        analysis_summary: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Allows interactive conversation with the repository. Answers technical questions
        about implementation details, where things are located, how to extend it, etc.
        """
        context_str = self._prepare_context_prompt(repo_data)
        analysis_brief = ""
        if analysis_summary:
            analysis_brief = f"\nPRIOR ANALYSIS SUMMARY:\n- Executive Summary: {analysis_summary.get('executive_summary')}\n- Tech Stack: {', '.join(analysis_summary.get('tech_stack', []))}\n"

        system_prompt = (
            "You are an expert AI software architect and technical guide for this repository. "
            "You have deep knowledge of the repo's file structure, configuration manifests, dependencies, "
            "and architecture. Answer the user's questions clearly, accurately, with code snippets or exact file paths "
            "where helpful.\n\n"
            f"REPOSITORY CONTEXT:\n{context_str}\n{analysis_brief}"
        )

        groq_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            groq_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=groq_messages,
            temperature=0.4,
            max_tokens=2048
        )
        return response.choices[0].message.content
