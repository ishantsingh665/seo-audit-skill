#!/usr/bin/env python3
"""Deterministic analysis of crawl JSON.

Usage:
  python scripts/analyze.py crawl.json --output findings.json
"""

import argparse
import json
from collections import Counter, defaultdict
from urllib.parse import urlparse


def is_indexable(page):
    status = page.get("status")
    if status != 200:
        return False

    robots = (page.get("robots") or "").lower()
    xrobots = (page.get("x_robots_tag") or "").lower()

    return "noindex" not in robots and "noindex" not in xrobots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("crawl")
    parser.add_argument("--output", default="findings.json")
    args = parser.parse_args()

    data = json.load(open(args.crawl, encoding="utf-8"))
    pages = [p for p in data.get("pages", []) if p.get("status") is not None]

    findings = []
    title_map = defaultdict(list)
    desc_map = defaultdict(list)
    incoming = Counter()

    for p in pages:
        url = p["url"]
        title = (p.get("title") or "").strip()
        desc = (p.get("meta_description") or "").strip()

        if title:
            title_map[title].append(url)
        else:
            findings.append({
                "rule_id": "ONPAGE-001",
                "severity": "high",
                "url": url,
                "finding": "Missing title",
                "evidence": "No HTML title element was detected.",
                "confidence": "HIGH",
            })

        if desc:
            desc_map[desc].append(url)
        else:
            findings.append({
                "rule_id": "ONPAGE-003",
                "severity": "low",
                "url": url,
                "finding": "Missing meta description",
                "evidence": "No meta description was detected.",
                "confidence": "HIGH",
            })

        h1s = p.get("headings", {}).get("h1", [])
        if not h1s:
            findings.append({
                "rule_id": "ONPAGE-005",
                "severity": "medium",
                "url": url,
                "finding": "No H1 detected",
                "evidence": "The crawled HTML contains no H1 element.",
                "confidence": "HIGH",
            })

        if len(h1s) > 1:
            findings.append({
                "rule_id": "ONPAGE-006",
                "severity": "low",
                "url": url,
                "finding": "Multiple H1 elements",
                "evidence": f"{len(h1s)} H1 elements detected.",
                "confidence": "HIGH",
            })

        if p.get("status") >= 400:
            findings.append({
                "rule_id": "HTTP-001",
                "severity": "critical" if p.get("status", 0) >= 500 else "high",
                "url": url,
                "finding": f"HTTP {p.get('status')} response",
                "evidence": f"The crawler received HTTP {p.get('status')}.",
                "confidence": "HIGH",
            })

        for link in p.get("internal_links", []):
            incoming[link] += 1

    for title, urls in title_map.items():
        if len(urls) > 1:
            findings.append({
                "rule_id": "ONPAGE-002",
                "severity": "medium",
                "urls": urls,
                "finding": "Duplicate title",
                "evidence": f"{len(urls)} URLs share the same title: {title!r}",
                "confidence": "HIGH",
            })

    for desc, urls in desc_map.items():
        if len(urls) > 1:
            findings.append({
                "rule_id": "ONPAGE-004",
                "severity": "low",
                "urls": urls,
                "finding": "Duplicate meta description",
                "evidence": f"{len(urls)} URLs share the same meta description.",
                "confidence": "HIGH",
            })

    for p in pages:
        if p.get("status") == 200 and p.get("content_type", "").lower().startswith("text/html"):
            if incoming[p["url"]] == 0 and p["url"] != data.get("start_url", "").rstrip("/"):
                findings.append({
                    "rule_id": "LINKS-002",
                    "severity": "high",
                    "url": p["url"],
                    "finding": "Potential orphan page",
                    "evidence": "No incoming internal link was found within the crawl.",
                    "confidence": "MEDIUM",
                })

    summary = Counter(x["severity"] for x in findings)

    output = {
        "summary": {
            "critical": summary.get("critical", 0),
            "high": summary.get("high", 0),
            "medium": summary.get("medium", 0),
            "low": summary.get("low", 0),
            "pages": len(pages),
            "indexable_pages": sum(is_indexable(p) for p in pages),
        },
        "findings": findings,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(json.dumps(output["summary"], indent=2))


if __name__ == "__main__":
    main()
