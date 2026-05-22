import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

BASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

KEYWORD_TO_LABEL = {
    "arabic NLP": "arabic-nlp",
    "low-resource machine translation": "machine-translation",
    "arabic intent detection": "intent-detection",
    "arabic transformers": "arabic-nlp",
    "model compression": "model-compression",
}


def issue_exists(arxiv_id: str) -> bool:
    """Check if an issue for this paper already exists."""
    url = f"{BASE_URL}/issues"
    params = {"state": "all", "labels": "arxiv-bot", "per_page": 100}

    with httpx.Client(headers=HEADERS, timeout=30) as client:
        response = client.get(url, params=params)

    response.raise_for_status()

    for issue in response.json():
        if arxiv_id in issue.get("body", ""):
            return True

    return False


def format_issue(paper: dict) -> dict:
    authors = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors += f" + {len(paper['authors']) - 5} more"

    body = f"""## {paper['title']}

**Authors:** {authors}
**Submitted:** {paper['submitted']}
**ArXiv ID:** `{paper['id']}`
**Link:** {paper['url']}

### Abstract
{paper['abstract']}

---

## My Notes

- [ ] Read abstract
- [ ] Read full paper
- [ ] Relevant to my research?
- [ ] Key takeaways:

<!-- arxiv_id:{paper['id']} -->
"""

    label = KEYWORD_TO_LABEL.get(paper["matched_keyword"], "arxiv-bot")

    return {
        "title": f"[ArXiv] {paper['title']}",
        "body": body,
        "labels": [label, "arxiv-bot"],
    }


def create_issue(paper: dict) -> dict | None:
    if issue_exists(paper["id"]):
        print(f"  ⏭  Already exists: {paper['title'][:60]}...")
        return None

    issue_data = format_issue(paper)

    with httpx.Client(headers=HEADERS, timeout=30) as client:
        response = client.post(f"{BASE_URL}/issues", json=issue_data)

    response.raise_for_status()
    result = response.json()
    print(f"  ✓ Created issue #{result['number']}: {paper['title'][:60]}...")
    return result


def create_issues(papers: list[dict]) -> list[dict]:
    created = []
    for paper in papers:
        issue = create_issue(paper)
        if issue:
            created.append(issue)
    return created
