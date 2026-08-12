---
name: grant-compass
description: Find fully-funded scholarships and programs at any degree level (Bachelor's, Master's, PhD) for any country the applicant names, defaulting to Europe if they don't say. Also finds matching professors for research degrees. Use when the user asks about funded study/PhD positions, scholarships, or Erasmus/Erasmus Mundus/DAAD/MSCA/Study Portals programs.
---

Token budget matters here. Do all deterministic fetching/parsing/scoring in the
`grantcompass` CLI (local Python, no LLM tokens). Only read the final compact
`output/report.md` back into context, never raw HTML, raw JSON, or full page
dumps. Do not pad the final answer with encouragement or filler; report the
table and one line on grade fit and deadlines, nothing else.

Steps:

1. Run `python -m grantcompass init` (from the repo root). If it just created
   `config.local.yaml` (or if `applicant.name` is still the placeholder
   `"Your Name"`), **ask the user directly, in the conversation**, before doing
   anything else:
   - Which country/countries do they want to target? If they don't say,
     default to all of Europe and tell them that's what you're doing.
   - Which degree level(s): Bachelor's, Master's/MS, and/or PhD?
   - Their field/keywords, and their grade (GPA/CGPA/percentage, whatever
     scale they use) and its scale.
   Write their answers into `config.local.yaml` yourself (it's gitignored,
   never guess or invent values, and never commit it). Then continue.
2. Run `python -m grantcompass professors`, a deterministic OpenReview/OpenAlex
   pass, no LLM involvement. Skip this entirely if `degree_target` is
   Bachelor's only, undergrad applicants don't need PI matching.
3. Program/funding listings have no stable public API, so this step needs your
   own web access:
   - Read `src/grantcompass/sources.yaml`.
   - Filter entries to those matching the applicant's `degree_target` (each
     entry's `levels` field) and `countries`.
   - For each matching entry with `has_api: false`, build a query from
     `config.local.yaml`'s `applicant.field_keywords` + `degree_target`, then
     WebSearch/WebFetch that source's `url_template`. Prioritize the aggregator
     platforms (Scholarshipportal/Bachelorsportal/Mastersportal/PhDportal,
     European Funding Guide) first, one query there surfaces many individual
     scholarships at once, which is far cheaper than querying every scheme
     site individually.
   - Extract only: name, degree_type, funding coverage, deadline (if stated),
     country, url. Append each as one compact JSON object to
     `data/programs_raw.json` (create the file/array if absent). Do NOT paste
     raw page text anywhere in context or into the file.
4. Run `python -m grantcompass score` then `python -m grantcompass report`.
5. Read only `output/report.md` and present it to the user as-is (or lightly
   reformatted), plus one line noting how many results were `borderline` vs
   `meets_minimum` on grade fit, and whether any deadlines were found. Stop
   there.
