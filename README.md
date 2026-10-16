# uber-incident-log-summarizer

_TODO: project description._

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
