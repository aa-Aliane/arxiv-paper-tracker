import httpx
import feedparser
from datetime import datetime, timezone, timedelta
import yaml
import time


def load_config(path: str = "config.yml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def fetch_papers(
    keyword: str, categories: list[str], max_results: int = 10
) -> list[dict]:
    url = "https://export.arxiv.org/api/query"

    # Also auto-wrap keywords in quotes to fix the precision issue we discussed
    clean_keyword = keyword.strip()
    if not (clean_keyword.startswith('"') and clean_keyword.endswith('"')):
        search_keyword = f'"{clean_keyword}"'
    else:
        search_keyword = clean_keyword

    category_filter = " OR ".join([f"cat:{c}" for c in categories])
    search_query = f"all:{search_keyword} AND ({category_filter})"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    # Custom User-Agent helps pass through some automated firewall checks
    headers = {
        "User-Agent": "ArxivPaperTrackerBot/1.0 (Contact: your_email@example.com)"
    }

    retries = 3
    wait = 15

    for attempt in range(retries):
        try:
            with httpx.Client(
                timeout=30, follow_redirects=True, headers=headers
            ) as client:
                response = client.get(url, params=params)

            if response.status_code == 429:
                print(
                    f"  Rate limited. Waiting {wait}s before retry ({attempt + 1}/{retries})..."
                )
                time.sleep(wait)
                wait *= 2
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

        except (httpx.ConnectTimeout, httpx.ConnectError) as e:
            # 🛡️ Catches the network timeouts/drops and triggers a retry attempt
            print(
                f"  [Network Warning] Connection failed: {e}. Retrying ({attempt + 1}/{retries}) in {wait}s..."
            )
            time.sleep(wait)
            wait *= 2
        except Exception as e:
            # Catches other unexpected issues (like bad XML parsing) and stops cleanly
            print(f"  [Error] Unhandled exception fetching '{keyword}': {e}")
            break

    print(f"  Failed to fetch '{keyword}' after {retries} attempts. Skipping.")
    return []


def filter_recent(papers: list[dict], hours: int) -> list[dict]:
    # 🌟 NEW: Setting lookback_hours to 0 skips chronological filtering entirely
    if hours <= 0:
        return papers

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
    categories = config.get("categories", ["cs.CL"])
    max_results = config.get("max_results_per_keyword", 50)
    hours = config.get("lookback_hours", 4380)

    seen_ids = set()
    all_papers = []

    for keyword in keywords:
        print(f"Fetching: '{keyword}'...")
        papers = fetch_papers(keyword, categories, max_results)
        recent = filter_recent(papers, hours)

        for paper in recent:
            if paper["id"] not in seen_ids:
                seen_ids.add(paper["id"])
                paper["matched_keyword"] = keyword
                all_papers.append(paper)

        time.sleep(5)  # Safe delay between keyword batches

    return all_papers


if __name__ == "__main__":
    config = load_config()
    papers = fetch_all(config)
    print(f"\n✓ Found {len(papers)} unique highly-relevant papers.\n")
