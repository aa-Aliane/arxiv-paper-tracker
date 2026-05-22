# 📄 ArXiv Paper Tracker

Automatically monitors ArXiv for NLP/ML papers matching my research interests and opens them as GitHub Issues in a dedicated repo (paper-reading-list) tagged, formatted, and ready for your notes.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## How it works

1. Reads a keyword list from `config.yaml`
2. Queries the ArXiv API for each keyword (last 6 months, sorted by relevance)
3. Deduplicates papers that match multiple keywords
4. Creates one GitHub Issue per unique paper in the paper-reading-list repo
5. Skips papers that already have an open issue (duplicate check by ArXiv ID)

Each issue includes the title, authors, abstract, ArXiv link, and a personal notes checklist:

```
## My Notes
- [ ] Read abstract
- [ ] Read full paper
- [ ] Relevant to my research?
- [ ] Key takeaways:
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/arxiv-paper-tracker.git
cd arxiv-paper-tracker
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure keywords

Edit `config.yaml` to match your research interests:

```yaml
keywords:
  - "arabic NLP"
  - "low-resource machine translation"
  - " intent detection"
  - "model compression NLP"

categories:
  - cs.CL
  - cs.AI

max_results_per_keyword: 50
lookback_hours: 4380 # ~6 months
```

### 3. Set up credentials

Create a `.env` file (never commit this):

```bash
cp .env.example .env
```

Then fill in your values:

```
GITHUB_TOKEN=your_fine_grained_pat
GITHUB_OWNER=your-username
GITHUB_REPO=paper-reading-list
```

Generate a fine-grained PAT at **Settings → Developer Settings → Personal Access Tokens**.
Required permission: **Issues: Read & Write**, scoped to your reading-list repo.

### 4. Run

```bash
# Live run — creates GitHub Issues
python main.py

# Dry run — prints papers without touching GitHub
python main.py --dry-run
```

---

## Automation with GitHub Actions

A workflow runs the tracker automatically every day at 08:00 UTC.

```yaml
# .github/workflows/daily_tracker.yml
on:
  schedule:
    - cron: "0 8 * * *"
  workflow_dispatch: # also triggerable manually from the GitHub UI
```

Add these as repository secrets under **Settings → Secrets and variables → Actions**:

| Secret         | Value                              |
| -------------- | ---------------------------------- |
| `GITHUB_TOKEN` | Your fine-grained PAT              |
| `TARGET_REPO`  | `your-username/paper-reading-list` |

---

## Project structure

```
arxiv-paper-tracker/
├── main.py                 # Entry point
├── src/
│   ├── arxiv_client.py     # ArXiv API fetcher + filtering
│   └── github_client.py    # GitHub Issues creator
├── config.yaml             # Keywords, categories, lookback window
├── .env                    # Secrets (gitignored)
├── .env.example            # Template (committed, no real values)
├── requirements.txt
└── README.md
```

---

## Possible extensions

- **Weekly digest** — a Monday workflow that summarises the week's papers into one Issue
- **Semantic Scholar integration** — filter by citation count as a relevance proxy
- **Slack / email notifications** — ping yourself when new papers are found
- **FastAPI endpoint** — trigger the tracker on demand via HTTP

---

## License

MIT — see [LICENSE](LICENSE)
