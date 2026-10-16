# uber-incident-log-summarizer

_TODO: project description._

## Log format notes

The dump carries a `.jsonl` extension but is a single pretty-printed JSON array:
it opens with `[`, closes with `]`, and every record line ends with a comma.
The parser strips those structural artifacts per line.

Each record is a JSON object with eight fields:

- `timestamp`
- `level`
- `service`
- `host`
- `request_id`
- `trip_id`
- `message`
- `duration_ms`

The `level` field takes four distinct values, exactly as they appear in the file:

- `INFO`
- `ERROR`
- `WARN`
- `DEBUG`

No malformed lines were found in the current dump (malformed count: 0).

## Usage

Run the streaming log parser, passing the log file path as an argument:

```bash
python3 parse_logs.py "Trip-Booking Outage Incident Log Dump (10 March 2025).jsonl"
```

It reads the log one line at a time, skips malformed lines, and prints the
processed, error, and malformed counts:

```
processed: 43
errors:    10
malformed: 0
```

## Normalisation rules

_TODO: describe how raw incident logs are normalised._

## Summary output

_TODO: describe the summary output format._

## Testing

_TODO: describe how to run the tests._

## Docker

_TODO: describe how to build and run with Docker._
