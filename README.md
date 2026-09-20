# Voice Memo Review Skill

Prepare previously transcribed voice-memo CSV files for a safe, mobile review workflow.

The planned workflow uses:

- **Google Sheets** as the review database
- **AppSheet** as the iPhone-friendly interface
- A separate, explicit reconciliation step for any real deletion

## Current status

Phase 1 is implemented: normalize a source CSV into a review-ready CSV without changing the source file.

```bash
python3 scripts/prepare_csv.py path/to/transcripts.csv --output build/voice-memos-review.csv
```

The command prints a JSON report and creates a UTF-8 CSV with this schema:

```text
memo_id,recorded_at,title,transcript,audio_link,decision,review_note,reviewed_at,processed_at
```

`decision` starts as `Pending`. Actual recordings are never deleted by this tool.

## Install as a Hermes skill

Clone the repository into a Hermes skills directory, or copy it there:

```text
~/.hermes/skills/productivity/voice-memo-review/
```

Start a new Hermes session after installation so the skill catalog reloads.

## Development

```bash
python3 -m unittest discover -s tests -v
```

See [todo.md](todo.md) for the complete delivery plan.

## Safety

A `Delete` decision is only a review label. Physical deletion must remain a separate, confirmed, reversible operation.

## License

MIT
