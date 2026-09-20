#!/usr/bin/env python3
"""Normalize a transcribed voice-memo CSV for mobile review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

OUTPUT_FIELDS = [
    "memo_id",
    "recorded_at",
    "title",
    "transcript",
    "audio_link",
    "decision",
    "review_note",
    "reviewed_at",
    "processed_at",
]

ALIASES = {
    "memo_id": ["memo_id", "id", "identifier", "uuid", "voice_memo_id"],
    "recorded_at": [
        "recorded_at",
        "recorded",
        "created_at",
        "created",
        "date",
        "timestamp",
    ],
    "title": ["title", "description", "name", "subject", "memo_description"],
    "transcript": [
        "transcript",
        "transcription",
        "content",
        "text",
        "body",
        "memo_text",
    ],
    "audio_link": [
        "audio_link",
        "audio_url",
        "url",
        "link",
        "file_url",
        "recording_url",
        "path",
    ],
}


def normalized_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def detect_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def resolve_column(
    fieldnames: list[str], canonical: str, explicit: str | None
) -> str | None:
    by_normalized = {normalized_heading(name): name for name in fieldnames}
    if explicit:
        if explicit in fieldnames:
            return explicit
        normalized = normalized_heading(explicit)
        if normalized in by_normalized:
            return by_normalized[normalized]
        raise ValueError(
            f"Column {explicit!r} was requested for {canonical!r}, "
            f"but available columns are: {', '.join(fieldnames)}"
        )
    for alias in ALIASES[canonical]:
        if alias in by_normalized:
            return by_normalized[alias]
    return None


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def generated_title(transcript: str, limit: int = 80) -> str:
    one_line = " ".join(transcript.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1].rstrip() + "…"


def generated_id(
    recorded_at: str, title: str, transcript: str, audio_link: str, row_number: int
) -> str:
    payload = json.dumps(
        [recorded_at, title, transcript, audio_link, row_number],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"vm_{digest}"


def unique_id(candidate: str, used: set[str]) -> str:
    base = candidate
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def normalize_rows(
    rows: Iterable[dict[str, str]], mapping: dict[str, str | None]
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    used_ids: set[str] = set()

    for row_number, row in enumerate(rows, start=2):
        transcript = clean(row.get(mapping["transcript"] or ""))
        title = clean(row.get(mapping["title"] or "")) or generated_title(transcript)
        recorded_at = clean(row.get(mapping["recorded_at"] or ""))
        audio_link = clean(row.get(mapping["audio_link"] or ""))
        source_id = clean(row.get(mapping["memo_id"] or ""))
        memo_id = source_id or generated_id(
            recorded_at, title, transcript, audio_link, row_number
        )
        memo_id = unique_id(memo_id, used_ids)

        output.append(
            {
                "memo_id": memo_id,
                "recorded_at": recorded_at,
                "title": title,
                "transcript": transcript,
                "audio_link": audio_link,
                "decision": "Pending",
                "review_note": "",
                "reviewed_at": "",
                "processed_at": "",
            }
        )
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare a transcribed voice-memo CSV for mobile review."
    )
    parser.add_argument("input", type=Path, help="Source CSV (never modified)")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV path")
    parser.add_argument("--id-column")
    parser.add_argument("--date-column")
    parser.add_argument("--title-column")
    parser.add_argument("--transcript-column")
    parser.add_argument("--audio-column")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()

    if source == output:
        raise ValueError("The output path must differ from the source path.")
    if not source.is_file():
        raise FileNotFoundError(f"Source CSV not found: {source}")

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(65536)
        handle.seek(0)
        reader = csv.DictReader(handle, dialect=detect_dialect(sample))
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise ValueError("The source CSV has no header row.")

        mapping = {
            "memo_id": resolve_column(fieldnames, "memo_id", args.id_column),
            "recorded_at": resolve_column(fieldnames, "recorded_at", args.date_column),
            "title": resolve_column(fieldnames, "title", args.title_column),
            "transcript": resolve_column(
                fieldnames, "transcript", args.transcript_column
            ),
            "audio_link": resolve_column(fieldnames, "audio_link", args.audio_column),
        }
        if mapping["transcript"] is None:
            raise ValueError(
                "No transcript/content column was detected. "
                "Use --transcript-column to identify it."
            )
        normalized = normalize_rows(reader, mapping)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)

    report = {
        "status": "prepared",
        "source": str(source),
        "output": str(output),
        "columns": mapping,
        "rows_read": len(normalized),
        "rows_written": len(normalized),
        "unique_ids": len({row["memo_id"] for row in normalized}),
        "default_decision": "Pending",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
