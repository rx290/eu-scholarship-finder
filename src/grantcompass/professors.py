"""
Deterministic PI-discovery pipeline: OpenReview accepted papers -> last author
(flagged as likely PI) -> OpenAlex enrichment (institution, country, h-index) ->
filtered to Europe -> data/professors_raw.json.

Clean-room design note: this reimplements the *concept* of arjunk00/phd-finder
(OpenReview -> last-author -> citation-metrics) using only OpenReview's and
OpenAlex's public, keyless, ToS-permitted REST APIs. No code from that repo
(which carries no license) was copied.
"""
import json
import time
import urllib.parse
from pathlib import Path

import requests

from .config import load_config

OPENREVIEW_API = "https://api2.openreview.net/notes"
OPENALEX_API = "https://api.openalex.org/authors"
EUROPEAN_COUNTRY_CODES = {
    "DE", "FR", "NL", "CH", "SE", "NO", "FI", "DK", "IT", "ES", "PT", "AT",
    "BE", "IE", "PL", "GB", "UK", "CZ", "HU", "GR", "RO", "BG", "HR", "SI",
    "SK", "EE", "LV", "LT", "LU", "IS", "CY", "MT",
}
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _get(url, params, retries=2, timeout=15):
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == retries:
                return None
            time.sleep(1)


def fetch_venue_papers(venue_keyword: str, max_papers: int) -> list[dict]:
    """Fetch accepted papers whose venue/content mentions venue_keyword."""
    data = _get(OPENREVIEW_API, {"term": venue_keyword, "limit": max_papers})
    if not data:
        return []
    return data.get("notes", [])


def last_author_of(paper: dict) -> str | None:
    authors = (paper.get("content", {}) or {}).get("authors", {})
    value = authors.get("value") if isinstance(authors, dict) else authors
    if isinstance(value, list) and value:
        return value[-1]
    return None


def enrich_author(name: str) -> dict | None:
    data = _get(OPENALEX_API, {"search": name, "per_page": 1})
    if not data or not data.get("results"):
        return None
    a = data["results"][0]
    inst = (a.get("last_known_institutions") or [{}])[0]
    country = inst.get("country_code")
    return {
        "name": a.get("display_name", name),
        "institution": inst.get("display_name"),
        "country_code": country,
        "h_index": (a.get("summary_stats") or {}).get("h_index"),
        "works_count": a.get("works_count"),
        "openalex_id": a.get("id"),
    }


def run() -> list[dict]:
    cfg = load_config()
    search_cfg = cfg.get("search", {})
    venues = search_cfg.get("venues", [])
    max_papers = search_cfg.get("max_papers_per_venue", 50)
    keywords = cfg.get("applicant", {}).get("field_keywords", [])

    records = []
    seen_authors = set()
    for venue in venues:
        for kw in keywords or [venue]:
            term = f"{venue} {kw}".strip()
            for paper in fetch_venue_papers(term, max_papers):
                author = last_author_of(paper)
                if not author or author in seen_authors:
                    continue
                seen_authors.add(author)
                enriched = enrich_author(author)
                if not enriched:
                    continue
                if enriched.get("country_code") not in EUROPEAN_COUNTRY_CODES:
                    continue
                enriched["source_venue"] = venue
                enriched["source_paper_title"] = (paper.get("content", {}) or {}).get("title", {}).get("value")
                records.append(enriched)

    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / "professors_raw.json"
    out_path.write_text(json.dumps(records, indent=2))
    return records


if __name__ == "__main__":
    results = run()
    print(f"Wrote {len(results)} European PI records to data/professors_raw.json")
