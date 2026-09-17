#!/usr/bin/env python3
"""
Basic SEO crawler.

Usage:
  python scripts/crawl.py https://example.com --output crawl.json --max-pages 200

Dependencies:
  pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


UA = "GeminiCLI-SEO-Audit/1.0 (+website-audit)"
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".gz", ".mp4", ".mp3", ".avi", ".mov",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".xml"
}


def normalize(url):
    url, _ = urldefrag(url)
    return url.rstrip("/") or url


def same_host(a, b):
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def likely_html(url):
    path = urlparse(url).path.lower()
    return not any(path.endswith(ext) for ext in SKIP_EXTENSIONS)


def text_length(soup):
    return len(re.findall(r"\b[\w'-]+\b", soup.get_text(" ", strip=True)))


def extract_page(url, response):
    soup = BeautifulSoup(response.text, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    description = description_tag.get("content", "").strip() if description_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    robots = robots_tag.get("content", "").strip() if robots_tag else ""

    canonical_tag = soup.find("link", rel=lambda x: x and "canonical" in x)
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    headings = {
        f"h{i}": [x.get_text(" ", strip=True) for x in soup.find_all(f"h{i}")]
        for i in range(1, 7)
    }

    internal = []
    external = []
    for a in soup.find_all("a", href=True):
        target = normalize(urljoin(url, a["href"]))
        if target.startswith(("http://", "https://")):
            if same_host(url, target):
                internal.append(target)
            else:
                external.append(target)

    images = []
    for img in soup.find_all("img"):
        images.append({
            "src": normalize(urljoin(url, img.get("src", ""))) if img.get("src") else "",
            "alt": img.get("alt"),
            "width": img.get("width"),
            "height": img.get("height"),
            "loading": img.get("loading"),
        })

    jsonld = []
    for script in soup.find_all("script", attrs={"type": re.compile("application/ld\\+json", re.I)}):
        jsonld.append(script.get_text(strip=True))

    og = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name")
        if prop and prop.lower().startswith(("og:", "twitter:")):
            og[prop.lower()] = meta.get("content", "")

    hreflang = []
    for link in soup.find_all("link", href=True):
        rel = link.get("rel") or []
        if any(str(x).lower() == "alternate" for x in rel) and link.get("hreflang"):
            hreflang.append({
                "hreflang": link.get("hreflang"),
                "href": normalize(urljoin(url, link["href"]))
            })

    viewport = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)})

    return {
        "url": url,
        "status": response.status_code,
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "response_time_ms": None,
        "title": title,
        "meta_description": description,
        "robots": robots,
        "x_robots_tag": response.headers.get("X-Robots-Tag", ""),
        "canonical": normalize(urljoin(url, canonical)) if canonical else "",
        "headings": headings,
        "word_count": text_length(soup),
        "html_bytes": len(response.content),
        "internal_links": sorted(set(internal)),
        "external_links": sorted(set(external)),
        "images": images,
        "jsonld": jsonld,
        "social_meta": og,
        "hreflang": hreflang,
        "viewport": viewport.get("content", "") if viewport else "",
    }


def crawl(start, max_pages, delay):
    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    start = normalize(start)
    queue = deque([start])
    seen = set()
    pages = []

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        if not same_host(start, url) or not likely_html(url):
            continue

        try:
            began = time.perf_counter()
            response = session.get(url, timeout=20, allow_redirects=True)
            elapsed = (time.perf_counter() - began) * 1000
            item = extract_page(url, response)
            item["response_time_ms"] = round(elapsed, 2)
            pages.append(item)

            if "text/html" in item["content_type"].lower():
                for link in item["internal_links"]:
                    if link not in seen and len(seen) < max_pages * 4:
                        queue.append(link)

        except requests.RequestException as exc:
            pages.append({
                "url": url,
                "status": None,
                "error": str(exc),
            })

        time.sleep(delay)

    return {
        "start_url": start,
        "pages": pages,
        "page_count": len(pages),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", default="crawl.json")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args()

    data = crawl(args.url, args.max_pages, args.delay)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Crawled {data['page_count']} pages -> {args.output}")


if __name__ == "__main__":
    main()
