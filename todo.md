# Voice Memo Review — Delivery Plan

## Principles

- Keep the original CSV unchanged.
- Give every memo a stable identifier before review.
- Treat `Delete` as a label, not an immediate destructive action.
- Keep review decisions portable through CSV export.
- Limit transcript text placed in the review Sheet to a 200-character preview; keep full transcripts outside the Sheet.
- Make the basic workflow usable without hosting a custom server.

## Phase 1 — Prepare the CSV for review

- [x] Define the canonical review schema:
  - `memo_id`
  - `recorded_at`
  - `title`
  - `transcript`
  - `audio_link`
  - `decision`
  - `review_note`
  - `reviewed_at`
  - `processed_at`
- [x] Implement a standard-library CSV normalization script.
- [x] Detect common source headings such as `description`, `content`, `transcription`, `date`, and `url`.
- [x] Allow explicit column overrides for unfamiliar CSV formats.
- [x] Generate deterministic memo IDs when the source has no usable ID.
- [x] Reject files that do not contain a transcript/content column.
- [x] Preserve the source file and write to a separate output path.
- [x] Default every review decision to `Pending`.
- [x] Add automated tests for normalization, overrides, missing columns, and duplicate rows.
- [x] Document manual import into Google Sheets.
- [x] Validate the workflow against the owner's real transcription CSV (259 rows, 259 unique IDs).
- [x] Import the resulting review data into the owner's Google Sheet and verify all rows remotely.

### Google Sheets import

1. Run `scripts/prepare_csv.py` against the source export.
2. Review the command's JSON report and confirm the expected input columns were mapped.
3. Open Google Sheets on the web and create a blank spreadsheet.
4. Select **File → Import → Upload** and choose the generated CSV.
5. Select **Replace current sheet** and let Google Sheets detect commas automatically.
6. Freeze the first row and enable a filter.
7. Add data validation to the `decision` column with these values: `Pending`, `Keep`, `Delete`, `Unsure`.
8. Confirm the imported row count equals the script's `rows_written` value.
9. Keep the source CSV as the immutable backup.

### Phase 1 acceptance criteria

- The source CSV checksum and modification time are unchanged.
- Every input row produces exactly one output row.
- Every output row has a non-empty, unique `memo_id`.
- Every output row starts with `decision=Pending`.
- The imported Google Sheet row count matches the normalization report.

## Phase 2 — Build the AppSheet iPhone interface

- [ ] Create an AppSheet app backed by the review Sheet.
- [ ] Configure a one-memo-at-a-time detail view.
- [ ] Add `Keep`, `Delete`, and `Unsure` actions.
- [ ] Add an editable review-note field.
- [ ] Add views for Pending, Keep, Delete, Unsure, and Completed.
- [ ] Automatically populate `reviewed_at` when a decision changes.
- [ ] Test layout and navigation on an iPhone.
- [ ] Document AppSheet setup with screenshots.

## Phase 3 — Review and quality control

- [ ] Complete an initial review from the iPhone.
- [x] Add progress counts by decision.
- [x] Detect records with missing or invalid decisions.
- [x] Support correction of earlier decisions.
- [x] Export a decision snapshot as CSV.
- [x] Compare exported IDs with the original prepared dataset.

## Phase 4 — Reconcile decisions safely

- [ ] Define how `memo_id` maps back to each original Voice Memo.
- [ ] Produce separate Keep, Delete, and Unsure manifests.
- [ ] Require explicit confirmation before applying a Delete manifest.
- [ ] Prefer moving recordings to a recoverable archive or Recently Deleted.
- [ ] Record `processed_at` only after successful reconciliation.
- [ ] Verify every requested action and report unresolved IDs.

## Optional Phase 5 — Telegram front end

- [ ] Add a Telegram bot with inline decision buttons.
- [ ] Keep Google Sheets or SQLite as the authoritative store.
- [ ] Add Previous, Next, Skip, and Add note actions.
- [ ] Handle Telegram message-length limits for long transcripts.
- [ ] Prevent duplicate button presses from creating conflicting updates.

## Optional Phase 6 — Custom web application

- [ ] Consider only if AppSheet limitations block required features.
- [ ] Add authenticated card-based review.
- [ ] Add direct audio playback where a usable audio URL exists.
- [ ] Add keyboard/swipe controls, bulk review, and audit history.
- [ ] Define hosting, backups, authentication, and upgrade ownership.
