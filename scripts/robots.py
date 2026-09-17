#!/usr/bin/env python3
"""Fetch and summarize robots.txt."""

import argparse
import json
from urllib.parse import urlparse

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", default="robots.json")
    args = parser.parse_args()

    parsed = urlparse(args.url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    response = requests.get(
        robots_url,
        timeout=20,
        headers={"User-Agent": "GeminiCLI-SEO-Audit/1.0"}
    )

    lines = response.text.splitlines() if response.ok else []

    data = {
        "url": robots_url,
        "status": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "sitemaps": [
            line.split(":", 1)[1].strip()
            for line in lines
            if line.lower().startswith("sitemap:")
        ],
        "lines": lines,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"robots.txt status: {response.status_code}")
    print(f"Sitemaps declared: {len(data['sitemaps'])}")


if __name__ == "__main__":
    main()
