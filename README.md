# Gemini CLI SEO Audit Skill

This package contains a reusable SEO auditing skill for Gemini CLI.

## Contents

- `SKILL.md` — main agent instructions
- `rules/rules.yaml` — deterministic audit rule definitions
- `scripts/crawl.py` — website crawler
- `scripts/robots.py` — robots.txt checker
- `scripts/sitemap.py` — sitemap discovery/parser
- `scripts/analyze.py` — deterministic crawl analysis
- `scripts/report.py` — basic Markdown report
- `references/README.md` — authoritative documentation sources
- `examples/example-request.md` — example prompts
- `requirements.txt` — Python dependencies

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python scripts/crawl.py https://example.com --output crawl.json --max-pages 200
python scripts/robots.py https://example.com --output robots.json
python scripts/sitemap.py https://example.com --output sitemap.json
python scripts/analyze.py crawl.json --output findings.json
python scripts/report.py crawl.json findings.json --output SEO_AUDIT.md
```

The Gemini agent should use `SKILL.md` as the behavioral contract and the scripts for deterministic collection/analysis.

## Important

This is intentionally not a "magic SEO score" system.

The report should prioritize evidence, impact, confidence, and actionable fixes.

Search-engine behavior changes over time. Verify current guidance from primary documentation before treating a behavior-dependent rule as a requirement.
