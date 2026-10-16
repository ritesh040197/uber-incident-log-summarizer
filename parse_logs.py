#!/usr/bin/env python3
"""Streaming log parser for the incident log dump.

Reads the log file one line at a time (constant memory) and classifies every
physical line into exactly one bucket, so the buckets reconcile to the file's
total line count:

    total = processed + rejected + malformed + skipped

  skipped   -- blank lines and the array's `[` / `]` wrapper lines
  malformed -- a content line that is not valid JSON
  rejected  -- valid JSON but missing a REQUIRED field (unusable record)
  processed -- a valid record carrying every required field

`errors` counts processed records whose level == "ERROR".

Required fields are the ones a record is unusable without for summarization and
error counting. The four optional fields (host, request_id, trip_id,
duration_ms) are legitimately null/absent in the data. This list is mirrored in
the README's "Log format notes"; keep the two in sync.

The dump carries a `.jsonl` extension but is a single pretty-printed JSON array:
it opens with `[`, closes with `]`, and every record line ends with a comma.
Those structural artifacts are stripped per line before parsing.

Usage:
    python3 parse_logs.py <log_path>
"""
import json
import sys

REQUIRED_FIELDS = ("timestamp", "level", "service", "message")


def parse(path):
    counts = {
        "total": 0,       # every physical line read
        "skipped": 0,     # blank / wrapper lines
        "malformed": 0,   # not valid JSON
        "rejected": 0,    # valid JSON, missing a required field
        "processed": 0,   # valid record with all required fields
        "errors": 0,      # processed records with level == "ERROR"
    }

    with open(path, encoding="utf-8") as f:
        for line in f:
            counts["total"] += 1
            s = line.strip()

            # Blank lines and the array's `[` / `]` wrapper lines.
            if not s or s in ("[", "]"):
                counts["skipped"] += 1
                continue

            # Records are comma-separated array elements.
            if s.endswith(","):
                s = s[:-1]

            try:
                record = json.loads(s)
            except json.JSONDecodeError:
                counts["malformed"] += 1
                continue

            if not isinstance(record, dict) or any(
                field not in record for field in REQUIRED_FIELDS
            ):
                counts["rejected"] += 1
                continue

            counts["processed"] += 1
            if record.get("level") == "ERROR":
                counts["errors"] += 1

    return counts


def main(argv):
    if len(argv) != 2:
        print("usage: python3 parse_logs.py <log_path>", file=sys.stderr)
        return 2

    try:
        c = parse(argv[1])
    except OSError as exc:
        print(f"error: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 1

    print(f"total:     {c['total']}")
    print(f"processed: {c['processed']}")
    print(f"errors:    {c['errors']}")
    print(f"rejected:  {c['rejected']}")
    print(f"malformed: {c['malformed']}")
    print(f"skipped:   {c['skipped']}")

    accounted = c["processed"] + c["rejected"] + c["malformed"] + c["skipped"]
    ok = accounted == c["total"]
    print(f"reconciles: {ok} ({accounted} == {c['total']})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
