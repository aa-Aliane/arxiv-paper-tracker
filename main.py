from src.arxiv_client import load_config, fetch_all
from src.github_client import create_issues
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="Print papers without creating issues"
    )
    args = parser.parse_args()

    config = load_config()
    print("🔍 Fetching papers from ArXiv...\n")
    papers = fetch_all(config)
    print(
        f"\n✓ Found {len(papers)} unique papers in the last {config['lookback_hours']}h\n"
    )

    if args.dry_run:
        print("--- DRY RUN: no issues will be created ---\n")
        for p in papers:
            print(f"  [{p['matched_keyword']}] {p['title'][:70]}...")
        return

    print("📬 Creating GitHub Issues...\n")
    created = create_issues(papers)
    print(
        f"\n✅ Done — {len(created)} issues created, {len(papers) - len(created)} skipped."
    )


if __name__ == "__main__":
    main()
