import httpx
import feedparser
from datetime import datetime, timezone, timedelta
import yaml
import time


def load_config(path: str = "config.yml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def fetch_papers(keyword: str, max_results: int = 10) -> list[dict]:
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    retries = 3
    wait = 15

    for attempt in range(retries):
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            response = client.get(url, params=params)

        if response.status_code == 429:
            print(
                f"  Rate limited. Waiting {wait}s before retry ({attempt + 1}/{retries})..."
            )
            time.sleep(wait)
            wait *= 2  # 15s → 30s → 60s
            continue

        response.raise_for_status()

        feed = feedparser.parse(response.text)
        papers = []

        for entry in feed.entries:
            papers.append(
                {
                    "id": entry.id.split("/abs/")[-1],
                    "title": entry.title.replace("\n", " ").strip(),
                    "authors": [a.name for a in entry.authors],
                    "abstract": entry.summary.replace("\n", " ").strip(),
                    "url": entry.id,
                    "submitted": entry.published,
                }
            )

        return papers

    print(f"  Failed to fetch '{keyword}' after {retries} attempts. Skipping.")
    return []


def filter_recent(papers: list[dict], hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []

    for paper in papers:
        submitted = datetime.strptime(paper["submitted"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

        if submitted >= cutoff:
            recent.append(paper)

    return recent


def fetch_all(config: dict) -> list[dict]:
    keywords = config["keywords"]
    max_results = config.get("max_results_per_keyword", 10)
    hours = config.get("lookback_hours", 24)

    seen_ids = set()
    all_papers = []

    for keyword in keywords:
        print(f"Fetching: '{keyword}'...")
        papers = fetch_papers(keyword, max_results)
        recent = filter_recent(papers, hours)

        for paper in recent:
            if paper["id"] not in seen_ids:
                seen_ids.add(paper["id"])
                paper["matched_keyword"] = keyword
                all_papers.append(paper)

        time.sleep(8)

    return all_papers


if __name__ == "__main__":
    config = load_config()
    papers = fetch_all(config)

    print(
        f"\n✓ Found {len(papers)} unique papers in the last {config['lookback_hours']}h\n"
    )

    for p in papers:
        print(f"  [{p['matched_keyword']}]")
        print(f"  {p['title']}")
        print(f"  {p['url']}")
        print(
            f"  Authors: {', '.join(p['authors'][:3])}{'...' if len(p['authors']) > 3 else ''}"
        )
        print()
