# PyroDB4 Write-Ahead Log (WAL) Specification

Status: milestone 1. Scope is `PyroTable(..., use_wal=True)`. `use_wal=False` (the default)
behaves exactly like pyroDB3, except that snapshots are now written to a temp file in the same
directory and moved into place with `os.replace`.

The invariants below are the contract. Tests in `pyroDB4.py` (`run_all_tests`) enforce them;
when code and this document disagree, fix the code or update both.

## 1. File layout

For a table at `{loc}` there are exactly three files:

| File          | Purpose                                                      |
|---------------|--------------------------------------------------------------|
| `{loc}`       | msgpack snapshot (same format as pyroDB3, plus `__wal_gen__`) |
| `{loc}.wal`   | append-only log of framed records since the last checkpoint  |
| `{loc}.lock`  | inter-process lock (`FileLock`, byte 0)                      |

No other sidecar files. The only other file that ever appears is a short-lived snapshot temp file
in the same directory, which `os.replace` moves onto `{loc}` (or which is removed if the write fails).

## 2. Record frame

```
[u32 len][u32 crc32(payload)][payload: msgpack]     little endian, no padding
```

- `len` is the payload length in bytes. `crc32` is `zlib.crc32(payload) & 0xFFFFFFFF`.
- The payload is a msgpack map with key `"k"` (record kind) plus the fields listed in section 3.
  Datetimes use the same `__datetime__` hook as snapshots.
- Replay stops at the first frame with a short header, short payload, CRC mismatch, undecodable
  payload, or schema violation. Everything from that point on is a **torn tail** and is ignored.

## 3. Record kinds and required fields

Every record carries `k`. Required fields are validated on encode **and** decode (`_WAL_SCHEMA`).

| Kind          | Required fields                          | Emitted in milestone 1 |
|---------------|------------------------------------------|------------------------|
| `checkpoint`  | `gen` (int), `snapshot_mtime` (int, ns)  | yes, always frame 0    |
| `txn_begin`   | `txid` (int)                             | yes                    |
| `txn_commit`  | `txid` (int)                             | yes                    |
| `set_cell`    | `col` (str), `row_id` (int), `val`       | yes                    |
| `add_row`     | `row_id` (int), `pos` (int or None), `vals` (map col -> value) | yes |
| `del_row`     | `row_id` (int)                           | yes                    |
| `add_column`  | `name` (str)                             | reserved, not emitted  |
| `del_column`  | `name` (str)                             | reserved, not emitted  |
| `meta`        | `key` (str), `val`                       | reserved, not emitted  |

Rows are always addressed by `row_id`, never by row index (except `add_row.pos`, which is the
insert position at the time of the write; `None` means append).

## 4. Idempotency

Replaying any committed transaction twice must leave the same state as replaying it once:

- `add_row`: skipped if `row_id in self.ids`.
- `del_row`: skipped if `row_id not in self.ids`.
- `set_cell`: writes an absolute value; skipped if the row or column no longer exists.
- `add_column` (reserved): skipped if `name in self.column_names_set`.

Tests replay the same WAL twice and check for no duplicates and an identical state.

## 5. Transactions

- Logged mutations buffer records in `self._wal_pending`. When `auto_dump(AD=True, logged=True)`
  runs, the buffer is written as `txn_begin{txid}`, records..., `txn_commit{txid}` in one write,
  followed by `fdatasync` (or `fsync` where `fdatasync` does not exist) if `sync=True`.
- Replay applies only transactions whose `txn_commit` frame is intact and whose txid matches the
  open `txn_begin`. An unterminated transaction (crash mid-write) is discarded.
- This makes `batch_set_cells`, `add_rows`, `add_rows_as_list`, `remove_duplicates`, row
  `update()`, and column `set_all()` atomic.

## 6. Logged vs. checkpoint-only operations

Logged (`auto_dump(..., logged=True)`): `set_cell` (and everything built on it: row/column/cell
setters), `batch_set_cells`, `add_row` / `insert_row` / `add_row_as_list`, `add_rows` /
`add_rows_as_list`, `pop_row` / `del_row` / `del_row_id`, `remove_duplicates`, row `update()`,
column `set_all()`.

Everything else that mutates calls `auto_dump(AD)` with the default `logged=False`. That sets
`_wal_force_checkpoint = True`, and the next flush becomes a full checkpoint. This includes
`add_column`, `del_column`, column rename, `clear`, `blank_sheet`, `index_column`,
`drop_column_index`, `load_json`, `load_csv`, `extend`, `add`, and **`sort`**.

**Why `sort` is special:** it reorders columns with `db._pk.db[col][:] = [...]`, which is a
list-in-place mutation and produces no `set_cell` records. It is therefore checkpoint-only.
Do not "optimise" it into per-cell records without a dedicated `sort` record kind.

Falling back to a checkpoint is correct by construction: any unknown mutation path is
persisted by a full snapshot.

## 7. Checkpoint (`dump()` in WAL mode)

Under `{loc}.lock`:

1. Catch up on the WAL (section 9) so committed records from other processes are not lost.
2. `gen = __wal_gen__ + 1`; store `__wal_gen__ = gen` and `__id__ = self.ids` in the snapshot root.
3. Write the msgpack snapshot to a temp file in the **same directory** as `{loc}`, `fsync` it,
   then `os.replace(temp, loc)` (retrying on Windows `PermissionError`), then `fsync` the parent
   directory (POSIX only; on Windows directory handles cannot be fsynced).
4. Rewrite `{loc}.wal` so it holds only `checkpoint{gen, snapshot_mtime}`, then fsync it.
   Truncation retries on `PermissionError`.
5. Clear the pending buffer and `_wal_force_checkpoint`.

Crash between steps 3 and 4: the snapshot has `gen` but the WAL header still has `gen - 1`, so
the whole WAL is treated as **stale** and ignored. The snapshot already contains those changes.

A WAL is valid only if frame 0 is `checkpoint` with `gen == snapshot.__wal_gen__`. A missing,
torn, or mismatched header makes the WAL stale. If a writer finds a stale WAL, it checkpoints
instead of appending.

`dump(filepath)` to a different path is a plain export (a snapshot copy, with no WAL).

## 8. Recomputed metadata (never logged)

- `__id__` is derived from the replayed `self.ids` and only written to the snapshot at checkpoint.
- `__indexed_columns__` changes only through checkpoint-only operations.
- `__epoch__` and `__wal_gen__` live only in the snapshot.

If `__id__` is missing or its length does not match the height when a table is loaded, new ids are
generated and `_wal_force_checkpoint` is set, so ids are persisted before any WAL record refers
to them.

## 9. Rescan (incremental catch-up)

Each WAL table tracks:

- `_wal_snap_sig = (st_mtime_ns, st_size)` of `{loc}`
- `_wal_seen = (st_size, st_mtime_ns)` of `{loc}.wal`
- `_wal_gen` (gen of the validated header, or `None` when stale)
- `_wal_offset` (byte offset just past the last committed transaction that was applied)

`rescan()`:

1. Stat both files without taking the lock. If both signatures are unchanged, return `False`.
2. Otherwise take `{loc}.lock` and run the catch-up:
   - If the snapshot signature changed, if the WAL is now shorter than `_wal_offset`, or if the
     WAL was stale, do a **full reload**: reload the snapshot and replay the WAL from frame 0.
   - Otherwise read frames from `_wal_offset`, apply committed transactions only, and advance
     `_wal_offset` to the end of the last commit.

Both size and mtime are compared because Windows mtime resolution is too coarse on its own.
`PyroDB.rescan()` delegates to the table through `_rescan_hook`, so `_pk.keys()` and similar calls
cannot bypass WAL replay by reloading only the snapshot.

## 10. Multi-process writes

Logged and checkpoint-only mutators run inside `_wal_writer`: TaskExecutor lock, then
`FileLock({loc}.lock)` (reentrant), then catch-up, then the mutation, then the flush. Appends always
happen right after a catch-up under the same lock. The writer seeks to `_wal_offset`, truncates
there (dropping any torn or unterminated tail), and writes. `O_APPEND` is not used, because its
semantics differ on Windows.

## 11. fsync policy

`PyroTable(..., use_wal=True, sync=True)`:

- `txn_commit`: `fdatasync` (`fsync` on Windows) of the WAL.
- Checkpoint: `fsync` the snapshot temp file before `os.replace`, `fsync` the parent directory
  (POSIX), and `fsync` the reset WAL.

`sync=False` skips every fsync (for benchmarks). In non-WAL mode, snapshots are not fsynced,
matching pyroDB3.

## 12. Windows notes

- `FileLock` uses `msvcrt.locking` on byte 0 of `{loc}.lock` (region lock, not reentrant at the OS
  level; `FileLock` keeps a per-path depth counter).
- `os.replace` onto a file another process holds open raises `PermissionError`; retry with backoff.
- WAL truncation (`f.truncate`) retries on `PermissionError`, the same as `_safe_remove` in the tests.
- The WAL is opened per append and closed immediately, so no long-lived handle blocks other processes.
- Parent-directory fsync is skipped on Windows.
- The whole suite must pass on Windows (`cd dev_src; python pyroDB4.py`).

## 13. Known limitations (milestone 1)

- `AD=False` records stay buffered until the next commit or dump. If another process changes
  the file in between, a full reload drops the unflushed local changes (pyroDB3 behaves the same).
- Do not run WAL and non-WAL instances **concurrently** on the same file. Switching modes between
  runs is safe: when a non-WAL table opens a file whose WAL has committed records, it replays
  them, writes a snapshot, and removes the WAL.
- `add_column`, `del_column`, `sort`, and the other operations in section 6 cost a full snapshot write.
