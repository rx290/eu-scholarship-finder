"""Render scored.json into a compact output/report.md (top N) + output/full_results.csv."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"

COLUMNS = ["name", "type", "source", "country_code", "gpa_fit", "match_score", "deadline", "url"]


def _row(r: dict) -> dict:
    return {
        "name": r.get("name") or r.get("title") or "(unnamed)",
        "type": r.get("degree_type") or ("PI" if "h_index" in r else "program"),
        "source": r.get("source", ""),
        "country_code": r.get("country_code") or r.get("country") or "",
        "gpa_fit": r.get("gpa_fit", ""),
        "match_score": r.get("match_score", ""),
        "deadline": r.get("deadline", "unknown"),
        "url": r.get("url") or r.get("openalex_id") or "",
    }


def run(top_n: int = 15) -> Path:
    scored_path = DATA_DIR / "scored.json"
    scored = json.loads(scored_path.read_text()) if scored_path.exists() else []
    rows = [_row(r) for r in scored]

    OUTPUT_DIR.mkdir(exist_ok=True)

    csv_path = OUTPUT_DIR / "full_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    md_path = OUTPUT_DIR / "report.md"
    lines = [f"# Top {min(top_n, len(rows))} matches ({len(rows)} total scored)", ""]
    lines.append("| " + " | ".join(COLUMNS) + " |")
    lines.append("|" + "|".join(["---"] * len(COLUMNS)) + "|")
    for row in rows[:top_n]:
        lines.append("| " + " | ".join(str(row[c]) for c in COLUMNS) + " |")
    md_path.write_text("\n".join(lines) + "\n")
    return md_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote {path}")
