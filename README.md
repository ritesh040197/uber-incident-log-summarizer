# uber-incident-log-summarizer

_TODO: project description._

## Log format notes

The dump carries a `.jsonl` extension but is a single pretty-printed JSON array:
it opens with `[`, closes with `]`, and every record line ends with a comma.
The parser strips those structural artifacts per line.

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

Every physical line is accounted for in one of four buckets, which reconcile to
the file's total line count:

    total = processed + rejected + malformed + skipped

- `processed` — valid record carrying every required field
- `rejected` — valid JSON but missing a required field
- `malformed` — a content line that is not valid JSON
- `skipped` — blank lines and the array's `[` / `]` wrapper lines

In the current dump (45 physical lines), 0 lines are malformed JSON, but **1
record is rejected**: an `ERROR` line from `trip-dispatch` that is missing its
`message` (and `duration_ms`). It is valid JSON, so a parser that only checked
JSON-validity would miscount it as a clean processed error — hence the
required-field check above.

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
errors:    9
rejected:  1
malformed: 0
skipped:   2
reconciles: True (45 == 45)
```

## Normalisation rules

_TODO: describe how raw incident logs are normalised._

## Summary output

_TODO: describe the summary output format._

## Testing

_TODO: describe how to run the tests._

## Docker

_TODO: describe how to build and run with Docker._
