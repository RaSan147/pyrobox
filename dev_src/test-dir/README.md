# `dev_src/test-dir` - live / manual fixtures

Serve this directory (or `live_served/`) to exercise the UI against awkward names:

```bash
cd dev_src
python server.py --directory test-dir/live_served
# or: pyrobox --directory test-dir
```

## Why this folder used to be `te-st`

`.gitignore` had `**/*test*`, which hid any path containing `test`. That rule is now narrowed with exceptions so **`dev_src/test-dir/`** and **`dev_src/tests/`** (pytest) are tracked.

| Path | Purpose |
|------|---------|
| `dev_src/test-dir/` | Manual scripts + sample files for live server browsing |
| `dev_src/test-dir/live_served/` | Odd names meant to be the HTTP document root |
| `dev_src/tests/` | Automated pytest suite |
