#!/usr/bin/env python3
"""Discover and inspect common XML sitemaps."""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import requests


UA = "GeminiCLI-SEO-Audit/1.0"


def get(url):
    return requests.get(url, timeout=20, headers={"User-Agent": UA})


def parse_xml_urls(text):
    root = ET.fromstring(text)
    tag = root.tag.lower()
    urls = []
    locs = [x.text.strip() for x in root.iter() if x.tag.lower().endswith("loc") and x.text]
    return "sitemapindex" in tag, locs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", default="sitemap.json")
    args = parser.parse_args()

    parsed = urlparse(args.url)
    candidates = [
        urljoin(f"{parsed.scheme}://{parsed.netloc}", "/sitemap.xml"),
        urljoin(f"{parsed.scheme}://{parsed.netloc}", "/sitemap_index.xml"),
    ]

    checked = []
    urls = []

    for sitemap in candidates:
        try:
            response = get(sitemap)
            checked.append({"url": sitemap, "status": response.status_code})
            if response.ok and "xml" in response.headers.get("content-type", "").lower() or response.ok:
                try:
                    is_index, locs = parse_xml_urls(response.text)
                    if is_index:
                        for child in locs[:100]:
                            child_resp = get(child)
                            checked.append({"url": child, "status": child_resp.status_code})
                            if child_resp.ok:
                                _, child_locs = parse_xml_urls(child_resp.text)
                                urls.extend(child_locs)
                    else:
                        urls.extend(locs)
                except Exception as exc:
                    checked[-1]["parse_error"] = str(exc)
        except requests.RequestException as exc:
            checked.append({"url": sitemap, "error": str(exc)})

    data = {
        "checked": checked,
        "url_count": len(set(urls)),
        "urls": sorted(set(urls)),
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Sitemap URLs discovered: {data['url_count']} -> {args.output}")


if __name__ == "__main__":
    main()
