#!/usr/bin/env python3
"""Create a simple Markdown report from crawl + findings JSON."""

import argparse
import json
from collections import defaultdict
from datetime import date


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("crawl")
    parser.add_argument("findings")
    parser.add_argument("--output", default="SEO_AUDIT.md")
    args = parser.parse_args()

    crawl = json.load(open(args.crawl, encoding="utf-8"))
    result = json.load(open(args.findings, encoding="utf-8"))

    summary = result["summary"]
    grouped = defaultdict(list)

    for finding in result["findings"]:
        grouped[finding["severity"]].append(finding)

    lines = [
        "# SEO Audit",
        "",
        f"Website: {crawl.get('start_url')}",
        f"Audit date: {date.today().isoformat()}",
        "",
        "## Executive Summary",
        "",
        f"- Pages crawled: {summary['pages']}",
        f"- Indexable pages: {summary['indexable_pages']}",
        f"- Critical: {summary['critical']}",
        f"- High: {summary['high']}",
        f"- Medium: {summary['medium']}",
        f"- Low: {summary['low']}",
        "",
    ]

    for severity in ["critical", "high", "medium", "low"]:
        lines += [f"## {severity.title()} Findings", ""]
        items = grouped.get(severity, [])
        if not items:
            lines.append("No findings.")
            lines.append("")
            continue

        for f in items:
            lines += [
                f"### {f['finding']}",
                "",
                f"**URL:** {f.get('url', ', '.join(f.get('urls', [])))}",
                f"**Evidence:** {f.get('evidence', '')}",
                f"**Confidence:** {f.get('confidence', '')}",
                "",
            ]

    lines += [
        "## Limitations",
        "",
        "- This report is based on crawler-observable data.",
        "- Google Search Console data is not included unless separately provided.",
        "- Field performance data is not inferred from crawler timing.",
        "- Search-engine behavior should be verified against current official documentation.",
        "",
    ]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
