---
name: voice-memo-review
description: Prepare transcribed voice memos for mobile review.
version: 0.1.0
author: CloudSecMentor (cloudsecmentor), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Voice-Memos, CSV, Google-Sheets, AppSheet]
    related_skills: []
---

# Voice Memo Review Skill

Prepare a transcribed voice-memo CSV for review in Google Sheets and, later, AppSheet. The workflow records decisions without deleting recordings.

## When to Use

- A user has a CSV containing voice-memo descriptions or transcripts.
- A user wants to classify memos as Keep, Delete, or Unsure on a phone.
- A review dataset needs stable IDs before it is imported into a mobile interface.

Do not use this workflow to delete original recordings during review.

## Prerequisites

- Python 3.10 or later.
- A source CSV with a transcript-like column such as `content`, `transcript`, or `transcription`.
- Google Sheets access for the manual import step.

No third-party Python packages are required.

## How to Run

Use `terminal` from the repository root:

```bash
python3 scripts/prepare_csv.py INPUT.csv --output build/voice-memos-review.csv
```

For unusual headings, set explicit mappings:

```bash
python3 scripts/prepare_csv.py INPUT.csv \
  --output build/voice-memos-review.csv \
  --transcript-column "Memo Text" \
  --title-column "Memo Description" \
  --date-column "Created"
```

## Procedure

1. Use `read_file` to inspect the source headings without modifying the source.
2. Run `scripts/prepare_csv.py` with `terminal` and capture its JSON report.
3. Confirm `rows_read` equals `rows_written`, `unique_ids` equals `rows_written`, and `default_decision` is `Pending`.
4. Import the generated CSV into a blank Google Sheet using the steps in `todo.md`.
5. Confirm the Sheet's data-row count equals `rows_written` before review begins.

## Pitfalls

- Automatic mapping cannot infer every custom heading; use the column override arguments when needed.
- Generated IDs are deterministic for the same row content and order, but a source-provided stable ID is preferable.
- An audio path on one computer may not be playable on an iPhone. Use a shareable URL only when its privacy model is acceptable.
- `Delete` is a label. Do not interpret it as authorization for permanent deletion.

## Verification

- Run `python3 -m unittest discover -s tests -v` with `terminal`.
- Confirm the source file remains untouched.
- Confirm each output `memo_id` is non-empty and unique.
- Confirm each output `decision` is `Pending`.
- Confirm the Google Sheet row count matches the script report.
