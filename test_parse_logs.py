#!/usr/bin/env python3
"""Tests for parse_logs.

The point of the malformed-line tests: never trust a `malformed: 0` that was
never run against a known bad line. Each bad-line type is planted on a numbered
line and asserted into the malformed breakdown, so a regression that lets a bad
line slip into `processed` fails loudly here.

Run:  python3 test_parse_logs.py
"""
import glob
import json
import os
import tempfile

import parse_logs

HERE = os.path.dirname(os.path.abspath(__file__))


def find_dump():
    """Locate the committed dump next to this test."""
    matches = sorted(glob.glob(os.path.join(HERE, "*.jsonl")))
    assert matches, "no .jsonl dump found next to the tests"
    return matches[0]


def run(lines):
    """Write `lines` to a temp file (no trailing newline) and parse it."""
    path = tempfile.mktemp(suffix=".jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    try:
        return parse_logs.parse(path)
    finally:
        os.remove(path)


GOOD = '{"timestamp":"t","level":"INFO","service":"s","message":"ok"},'
GOOD_LAST = '{"timestamp":"t","level":"ERROR","service":"s","message":"boom"}'


def test_planted_bad_lines_are_caught():
    """One of each bad-line type; watch each land in malformed, not processed."""
    truncated = '{"timestamp":"t","level":"INFO","service":"s","message":'
    stack_trace = '  at com.uber.dispatch.Assign(Assign.java:142),'
    double_comma = '{"timestamp":"t","level":"INFO","service":"s","message":"x"},,'
    no_level = '{"timestamp":"t","service":"s","message":"no level"},'

    c = run(["[", GOOD, truncated, stack_trace, double_comma, no_level, GOOD_LAST, "]"])

    # 2 good records (GOOD + GOOD_LAST)
    assert c["processed"] == 2, c
    # truncated + stack-trace + double-comma are not valid array elements
    assert c["invalid"] == 3, c
    # the level-less object is valid JSON but missing a required field
    assert c["missing"] == 1, c
    # the [ and ] wrapper lines
    assert c["structural"] == 2, c
    # every bad line is in malformed, none leaked into processed
    assert c["malformed"] == c["invalid"] + c["missing"] + c["structural"], c
    assert c["processed"] + c["malformed"] == c["total"], c
    print("PASS planted bad lines: truncated/stack-trace/double-comma -> invalid, "
          "no-level -> missing, none leaked into processed")


def test_stray_comma_is_not_repaired_into_processed():
    """A doubled trailing comma must be judged, not stripped into a clean record."""
    c = run(['{"timestamp":"t","level":"INFO","service":"s","message":"x"},,'])
    assert c["processed"] == 0, c
    assert c["invalid"] == 1, c
    print("PASS stray comma: doubled trailing comma -> malformed, not processed")


def test_counts_close_on_total():
    c = run(["[", GOOD, GOOD_LAST, "]"])
    assert c["processed"] + c["malformed"] == c["total"] == 4, c
    assert c["processed"] == 2 and c["structural"] == 2, c
    print("PASS reconciliation: processed + malformed == total")


def test_dump_really_is_a_json_array():
    """Evidence for the comma-strip rule, run against the real file.

    The parser accepts one trailing comma per line because the dump is a single
    JSON array, not independent JSONL. That assumption is the thing that lets a
    trailing comma through quietly, so it is checked here against the committed
    file rather than asserted in prose: the whole file must parse as a JSON
    array of objects. If the file ever stops being an array, this fails and the
    comma-strip rule loses its justification.
    """
    dump = find_dump()
    with open(dump, encoding="utf-8") as f:
        raw = f.read()

    arr = json.loads(raw)  # raises if the dump is not valid JSON as a whole
    assert isinstance(arr, list), f"dump is not a JSON array: {type(arr).__name__}"
    assert arr and all(isinstance(x, dict) for x in arr), "array has non-object elements"

    # Bind the authoritative array parse to the streaming parser: every array
    # element is one content line, each either processed or missing-a-required-
    # field, and no element line is invalid JSON. If the comma-strip rule let a
    # line through that the array parse would not, these would disagree.
    c = parse_logs.parse(dump)
    assert c["invalid"] == 0, c
    assert len(arr) == c["processed"] + c["missing"], (len(arr), c)
    print(f"PASS dump format: raw file is a valid JSON array of {len(arr)} objects; "
          f"streaming parse recovers the same {c['processed'] + c['missing']} records")


if __name__ == "__main__":
    test_planted_bad_lines_are_caught()
    test_stray_comma_is_not_repaired_into_processed()
    test_counts_close_on_total()
    test_dump_really_is_a_json_array()
    print("\nall tests passed")
