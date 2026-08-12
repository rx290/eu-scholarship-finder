"""
Pure-Python scoring: no network calls. Combines GPA eligibility against typical
per-scheme minimums with a keyword/field match score, producing one sort key
per record. Never silently drops a record for GPA reasons -- only flags it.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Typical published/observed minimums, normalized to a 4.0 GPA scale. These are
# rough eligibility signals, not guarantees -- always flagged, never enforced
# as a hard filter.
SCHEME_TYPICAL_MINIMUMS = {
    "daad": 2.5,
    "erasmus mundus": 3.0,
    "erasmus": 2.5,  # broader mobility/undergrad grants tend to be less GPA-strict than Erasmus Mundus
    "msca": 3.0,
    "marie curie": 3.0,
    "euraxess": 3.0,
    "findaphd": 3.0,
    "academictransfer": 3.0,
    "academicpositions": 3.0,
    "stipendium hungaricum": 2.5,
    "türkiye": 2.5,
    "turkiye": 2.5,  # ascii fallback in case a source uses the unaccented spelling
    "scholarshipportal": 2.5,
    "bachelorsportal": 2.5,
    "mastersportal": 3.0,
    "phdportal": 3.0,
    "european funding guide": 2.5,
    "default": 3.0,
}

BORDERLINE_MARGIN = 0.15  # within this much of the minimum counts as "borderline"


def gpa_fit(applicant_gpa: float, applicant_scale: float, scheme_name: str) -> str:
    """Return 'meets_minimum', 'borderline', or 'below_typical_minimum'."""
    normalized = applicant_gpa / applicant_scale * 4.0
    key = next((k for k in SCHEME_TYPICAL_MINIMUMS if k in scheme_name.lower()), "default")
    minimum = SCHEME_TYPICAL_MINIMUMS[key]
    if normalized >= minimum + BORDERLINE_MARGIN:
        return "meets_minimum"
    if normalized >= minimum - BORDERLINE_MARGIN:
        return "borderline"
    return "below_typical_minimum"


def keyword_match_score(record_text: str, field_keywords: list[str]) -> float:
    """Fraction of field_keywords found (case-insensitive substring) in record_text."""
    if not field_keywords:
        return 0.0
    text = (record_text or "").lower()
    hits = sum(1 for kw in field_keywords if kw.lower() in text)
    return hits / len(field_keywords)


GPA_FIT_RANK = {"meets_minimum": 2, "borderline": 1, "below_typical_minimum": 0}


def score_record(record: dict, applicant: dict, source_name: str) -> dict:
    text = " ".join(
        str(record.get(k, "")) for k in ("name", "institution", "source_venue", "source_paper_title", "title", "description")
    )
    fit = gpa_fit(applicant["gpa"], applicant["gpa_scale"], source_name)
    match = keyword_match_score(text, applicant.get("field_keywords", []))
    sort_key = GPA_FIT_RANK[fit] * 10 + match * 10
    return {**record, "source": source_name, "gpa_fit": fit, "match_score": round(match, 2), "sort_key": round(sort_key, 2)}


def run() -> list[dict]:
    from .config import load_config

    cfg = load_config()
    applicant = cfg["applicant"]

    scored = []
    for fname, source_label in (
        ("professors_raw.json", "OpenReview/OpenAlex PI match"),
        ("programs_raw.json", "program"),
    ):
        path = DATA_DIR / fname
        if not path.exists():
            continue
        records = json.loads(path.read_text())
        for r in records:
            source_name = r.get("source", source_label)
            scored.append(score_record(r, applicant, source_name))

    scored.sort(key=lambda r: r["sort_key"], reverse=True)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "scored.json").write_text(json.dumps(scored, indent=2))
    return scored


if __name__ == "__main__":
    results = run()
    print(f"Scored {len(results)} records -> data/scored.json")
