#!/usr/bin/env python3
"""
Command-line Interface for the GitHub Repo Analyzer powered by Groq.
Usage:
    python cli.py <owner/repo or github_url> [--groq-key KEY] [--model MODEL] [--export report.md]
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from analyzer.github_client import GitHubClient
from analyzer.groq_engine import GroqAnalyzerEngine

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""
{MAGENTA}{BOLD}====================================================================
           RepoScope: GitHub Repository Analyzer
                 Powered by Groq High-Speed LPUs
===================================================================={RESET}
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(description="Analyze any GitHub repository with Groq's high-speed AI.")
    parser.add_argument("repo", help="GitHub repo URL or 'owner/repo' shorthand (e.g. pallets/flask)")
    parser.add_argument("--groq-key", dest="groq_key", default=None, help="Groq API Key (defaults to GROQ_API_KEY in .env)")
    parser.add_argument("--github-token", dest="github_token", default=None, help="GitHub Personal Access Token (optional)")
    parser.add_argument("--model", default="llama-3.3-70b-versatile", help="Groq model (default: llama-3.3-70b-versatile)")
    parser.add_argument("--export", dest="export_path", default=None, help="Path to export markdown analysis report")

    args = parser.parse_args()
    print_banner()

    groq_key = args.groq_key or os.getenv("GROQ_API_KEY")
    if not groq_key:
        print(f"{RED}[Error]{RESET} Missing Groq API Key.")
        print(f"Please provide --groq-key, set GROQ_API_KEY in your .env, or export it in your environment.")
        print(f"You can get a free key in seconds at: {CYAN}https://console.groq.com{RESET}\n")
        sys.exit(1)

    github_token = args.github_token or os.getenv("GITHUB_TOKEN")

    try:
        owner, repo = GitHubClient.parse_repo_identifier(args.repo)
    except ValueError as e:
        print(f"{RED}[Error]{RESET} {str(e)}")
        sys.exit(1)

    print(f"{CYAN}--> Fetching GitHub context for {BOLD}{owner}/{repo}{RESET}{CYAN}...{RESET}")
    try:
        gh_client = GitHubClient(token=github_token)
        repo_data = gh_client.collect_repo_context(owner, repo)
    except Exception as e:
        print(f"{RED}[GitHub Error]{RESET} {str(e)}")
        sys.exit(1)

    info = repo_data["repo_info"]
    print(f"{GREEN}✓ Loaded repository:{RESET} {info['full_name']} ({info['stars']} stars, {info['language']})")

    print(f"{MAGENTA}--> Running architectural reasoning on Groq ({args.model})...{RESET}")
    try:
        engine = GroqAnalyzerEngine(api_key=groq_key, model=args.model)
        analysis = engine.analyze_repository(repo_data)
    except Exception as e:
        print(f"{RED}[Groq Error]{RESET} {str(e)}")
        sys.exit(1)

    # Display results
    score = analysis.get("quality_assessment", {}).get("health_score", 0)
    score_color = GREEN if score >= 80 else (YELLOW if score >= 60 else RED)

    print("\n" + "=" * 65)
    print(f"{BOLD}REPOSITORY:{RESET} {info['full_name']} ({info['html_url']})")
    print(f"{BOLD}HEALTH SCORE:{RESET} {score_color}{score}/100{RESET} - {analysis.get('quality_assessment', {}).get('health_verdict')}")
    print(f"{BOLD}PROJECT TYPE:{RESET} {analysis.get('project_type')}")
    print(f"{BOLD}PRIMARY STACK:{RESET} {', '.join(analysis.get('tech_stack', []))}")
    print("=" * 65)

    print(f"\n{BOLD}{CYAN}EXECUTIVE SUMMARY:{RESET}")
    print(analysis.get("executive_summary"))

    print(f"\n{BOLD}{CYAN}KEY FEATURES:{RESET}")
    for f in analysis.get("key_features", []):
        print(f"  • {f}")

    print(f"\n{BOLD}{CYAN}ARCHITECTURE & PATTERNS:{RESET}")
    print(analysis.get("architecture", {}).get("overview"))
    patterns = analysis.get("architecture", {}).get("design_patterns", [])
    if patterns:
        print(f"  {YELLOW}Patterns:{RESET} {', '.join(patterns)}")
    entry_points = analysis.get("architecture", {}).get("entry_points", [])
    if entry_points:
        print(f"  {YELLOW}Entry Points:{RESET} {', '.join(entry_points)}")

    print(f"\n{BOLD}{GREEN}KEY STRENGTHS:{RESET}")
    for s in analysis.get("quality_assessment", {}).get("strengths", []):
        print(f"  [+] {s}")

    print(f"\n{BOLD}{YELLOW}AREAS FOR IMPROVEMENT / RISKS:{RESET}")
    for w in analysis.get("quality_assessment", {}).get("weaknesses", []):
        print(f"  [!] {w}")

    print(f"\n{BOLD}{CYAN}QUICKSTART:{RESET}")
    setup = analysis.get("setup_and_quickstart", {})
    if setup.get("install_steps"):
        print("  Install:")
        for step in setup["install_steps"]:
            print(f"    $ {step}")
    if setup.get("run_command"):
        print(f"  Run: $ {setup['run_command']}")

    # Export if requested
    if args.export_path:
        export_file = Path(args.export_path)
        md_content = f"""# Analysis: {info['full_name']}
- URL: {info['html_url']}
- Health Score: {score}/100
- Tech Stack: {', '.join(analysis.get('tech_stack', []))}

## Summary
{analysis.get('executive_summary')}

## Architecture
{analysis.get('architecture', {}).get('overview')}

## Strengths
{chr(10).join(['- ' + s for s in analysis.get('quality_assessment', {}).get('strengths', [])])}

## Improvement Areas
{chr(10).join(['- ' + w for w in analysis.get('quality_assessment', {}).get('weaknesses', [])])}
"""
        export_file.write_text(md_content, encoding="utf-8")
        print(f"\n{GREEN}✓ Exported full report to:{RESET} {export_file.resolve()}")

    print("\n" + "=" * 65)
    print(f"{GREEN}Analysis complete! To explore with an interactive UI and AI Chat, run:{RESET}")
    print(f"  {BOLD}python app.py{RESET}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
