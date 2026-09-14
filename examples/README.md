# Examples

`demo/` is a six-slide synthetic non-clinical project fixture. Build it with:

```sh
python scripts/mpa.py validate examples/demo
python scripts/mpa.py build examples/demo
python scripts/mpa.py render examples/demo --engine powerpoint  # Windows + Office
```

It demonstrates flow, timeline, comparison table, native chart and checklist layouts. All illustrative values are invented. It does not contain patient examples or a ready-to-teach medical deck. Rendered/private output is git-ignored.
