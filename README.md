# uber-incident-log-summarizer

_TODO: project description._

## Log format notes

The dump carries a `.jsonl` extension but is a single pretty-printed JSON array:
it opens with `[`, closes with `]`, and every element line ends with one
separator comma. That the file really is one JSON array — not independent JSONL
— is the premise the comma-strip rule rests on, so it is not asserted here but
**checked against the committed file** by `test_dump_really_is_a_json_array`
(see [Testing](#testing)): the whole file must parse as a JSON array of objects,
and the streaming parser must recover exactly those elements. If the file ever
stops being an array, that test fails and the rule loses its justification.

Given that premise, the parser recognizes the one separator comma as the known
format — it does **not** repair a line before judging it. A line is accepted as
a record only when it is a JSON object followed by at most one trailing comma;
a truncated object, a stack-trace line, a stray/doubled comma, or a non-object
is judged malformed rather than rewritten into something parseable.

Each record is a JSON object with eight fields. Four are **required** — a record
is unusable for summarization or error counting without them — and four are
optional (legitimately null or absent in the data). The parser rejects any
record missing a required field, and this list is the single source of truth it
validates against:

| Field | Required? |
|---|---|
| `timestamp` | required |
| `level` | required |
| `service` | required |
| `message` | required |
| `host` | optional |
| `request_id` | optional |
| `trip_id` | optional |
| `duration_ms` | optional |

The `level` field takes four distinct values, exactly as they appear in the file:

- `INFO`
- `ERROR`
- `WARN`
- `DEBUG`

Every physical line is one of two things, and the two close on the file's total
line count — the sum a reader actually checks:

    total = processed + malformed

- `processed` — a usable record: valid JSON object with every required field
- `malformed` — any line that is not a usable record

`malformed` is broken down underneath by reason (invalid JSON, missing a
required field, or a structural/blank line), but that split is detail; the
headline numbers close on `processed + malformed`.

### What's actually in this dump

The whole file parses as a valid 43-element JSON array — verified by
`test_dump_really_is_a_json_array`, not just claimed — which means it contains
**no** truncated object, stack-trace line, or stray trailing-comma line; any of
those would break that parse. Its
only data defect is **one record missing a required field**: an `ERROR` line
from `trip-dispatch` (line 44) that has no `message` (and no `duration_ms`). It
is valid JSON, so a parser that only checked JSON-validity would miscount it as
a clean processed error — hence the required-field check above.

The `malformed: 0` for invalid JSON is not an untested claim: `test_parse_logs.py`
plants a truncated object, a stack-trace line, and a doubled-comma line and
asserts each lands in `malformed` (never `processed`). See [Testing](#testing).

## Usage

Run the streaming log parser, passing the log file path as an argument:

```bash
python3 parse_logs.py "Trip-Booking Outage Incident Log Dump (10 March 2025).jsonl"
```

It reads the log one line at a time, classifies every physical line into one
bucket, and prints counts plus a reconciliation line. To get the file's total
line count independently (for cross-checking the `total` it reports), note the
dump has no trailing newline, so add 1 to `wc -l`:

```bash
echo $(( $(wc -l < "Trip-Booking Outage Incident Log Dump (10 March 2025).jsonl") + 1 ))
```

Output on the current dump:

```
total:     45
processed: 42
malformed: 3
  - invalid JSON:            0
  - missing required field:  1
  - structural (wrapper/blank): 2
errors (of processed):     9
check: processed + malformed = 42 + 3 = 45 == total 45  [OK]
```

`processed (42) + malformed (3) = 45 = total`. The three malformed are the one
missing-field record plus the two array-envelope lines (`[` and `]`); the
breakdown says which is which.

## Normalisation rules

_TODO: describe how raw incident logs are normalised._

## Summary output

_TODO: describe the summary output format._

## Testing

```bash
python3 test_parse_logs.py
```

The tests plant one of each bad-line type — a truncated object, a stack-trace
line, a doubled trailing comma, and a record missing a required field — and
assert each is counted as malformed and none leaks into `processed`. This is
what backs the `invalid JSON: 0` on the real dump: the zero has been run against
known bad lines, not merely observed.

`test_dump_really_is_a_json_array` runs against the committed dump itself: it is
the evidence for the comma-strip rule. It asserts the whole file parses as a
JSON array of objects and that the streaming parser recovers exactly those
elements (`invalid JSON: 0`, and array length == processed + missing). The rule
that lets a trailing comma through is therefore justified by a check anyone can
re-run, not by a claim in this README.

## Docker

_TODO: describe how to build and run with Docker._
