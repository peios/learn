---
title: Events and coverage
type: how-to
description: How to capture Provium's structured event stream — to a file, to stdout, or over a Unix socket — and feed it to provium-coverage or your own consumer.
---

Provium emits a structured msgpack event stream covering every file, test, VM, fixture, and pool transition. This page covers the practical side of consuming it; the wire format is on [events](~provium/reference/events).

## Why events

The human-readable `PASS / FAIL` summary is fine for the dev loop, but not enough for:

- Coverage reports (which test exercised which spec section?).
- Dashboards (live view of pool state, in-flight files, fixture builds).
- Post-hoc analysis ("why did this CI run take 4× longer than yesterday?").
- Debugging fixture rebuilds (which file is waiting on which build lock?).

For all of these, the event stream is what you want.

## Output channels

Provium can route events to three places independently. Combine flags freely.

### `--save-events <path>` — to a file

```
provium tests/ --save-events events.msgpack
```

Writes length-prefixed msgpack frames to the file. Use for post-hoc analysis or replay.

Under `--watch`, the file is truncated at each iteration so it contains exactly the most recent run.

### `--events-stdout` — to stdout

```
provium tests/ --events-stdout | provium-coverage --from -
```

Streams events on stdout. The human-readable / JSON renderer redirects to stderr so consumers piping `provium --events-stdout | …` don't see human text interleaved into their msgpack parser.

Mutually exclusive with `--json`.

### `--events-socket <path>` — over a Unix socket

```
provium tests/ --watch --events-socket /tmp/provium.sock
# in another terminal:
provium-coverage --from-socket /tmp/provium.sock
```

The binary listens, accepts connections, and fans out frames. Useful for live dashboards. The socket persists across `--watch` iterations so connected clients aren't dropped on every re-run.

## Coverage post-run

`--coverage` is sugar over `--save-events` + a post-run pipe to `provium-coverage`:

```
provium tests/ --coverage
```

Internally:

1. If `--save-events <path>` is also set, Provium uses that file.
2. Otherwise, Provium tees events to a scratch tempfile (`$TMPDIR/provium-coverage-<pid>.msgpack`) with a sibling marker file.
3. After the run, runs `provium-coverage --from <path>`.
4. Cleans up the tempfile if Provium owns it (the marker is the proof).

Failures from the post-run pipe propagate as the exit code — a coverage failure shows up as exit `1`.

The cleanup is robust: SIGINT / SIGTERM handlers and an `atexit` hook clear the tempfile even on a killed run, so CI won't accumulate orphaned msgpack files.

## What's in the stream

| Event | Emitted when |
|---|---|
| `file_discovered` | Each `*.test.lua` found in pre-run scan. Includes `fixture_refs`. |
| `file_dispatched` | A runner thread picks up a file. Includes `reservation`. |
| `file_blocked` | A file is waiting on the pool or PSI pressure. |
| `file_completed` | A file finishes (`passed` / `failed` / `timed_out` / `crashed`). |
| `test_started` | A `test()` block begins. |
| `test_passed` / `test_failed` / `test_skipped` | A `test()` block ends. `test_failed` includes `console_excerpt`. |
| `vm_spawned` / `vm_shutdown` | VM lifecycle. Includes CID, profile, memory. |
| `pool_state` | Periodic 1 Hz snapshot of pool usage. |
| `claim_acquired` / `claim_released` | A file's `provium:claim(...)` lifecycle. |
| `fixture_build_started` / `fixture_build_done` | A fixture's build lifecycle. |
| `fixture_build_waiting` | A second file is queued behind a peer's build. |
| `fixture_cache_hit` | A fixture was resumed from cache. |

Every frame is `{ts, kind, payload}` — see [events reference](~provium/reference/events) for the full wire shape.

## Replay and analysis

```
provium tests/ --save-events events.msgpack
provium-coverage --from events.msgpack
```

The msgpack file is portable. You can analyse it on a different host than the one that produced it, or run multiple consumers against the same file:

```
provium-coverage --from events.msgpack > coverage.html
my-custom-tool --from events.msgpack > metrics.json
```

## Building your own consumer

The protocol is `provium-protocol`'s `EventFrame` over length-prefixed msgpack frames (the same framing as the agent wire protocol). The framing helpers in `provium-protocol::frame` are exposed for reuse.

A minimal Rust consumer:

```rust
use provium_protocol::events::{Event, EventFrame};
use provium_protocol::frame::{read_frame, DEFAULT_MAX_FRAME_BYTES};
use std::fs::File;
use std::io::BufReader;

fn main() -> std::io::Result<()> {
    let f = File::open("events.msgpack")?;
    let mut r = BufReader::new(f);
    loop {
        let frame: EventFrame = match read_frame(&mut r, DEFAULT_MAX_FRAME_BYTES) {
            Ok(f) => f,
            Err(_) => break,  // EOF or malformed; production code should distinguish
        };
        match frame.event {
            Event::TestPassed(t) => println!("PASS {}::{}", t.path, t.name),
            Event::TestFailed(t) => println!("FAIL {}::{} — {}", t.path, t.name, t.reason),
            _ => {}
        }
    }
    Ok(())
}
```

For other languages, use any msgpack library that handles the length-prefix framing (e.g. read 4 bytes BE length, then read N bytes, then deserialize as msgpack).

## Live multiplexing for dashboards

`--events-socket` is the right shape when you have a long-running dashboard:

```
# Provium runs in watch mode; events flow over the socket.
provium tests/ --watch --events-socket /tmp/provium.sock

# Dashboard connects once and stays connected across reruns.
my-dashboard --from-socket /tmp/provium.sock
```

The socket persists across `--watch` iterations precisely so dashboards don't have to reconnect on every re-run.

For non-dashboard pipelines (CI feeding a coverage tool), prefer `--events-stdout` — simpler, no socket-file management.

## Observability event guarantees

The harness ensures:

- `file_discovered` for every file, before any dispatching.
- For each file: at most one `file_dispatched`, optional `file_blocked`(s) before it, exactly one `file_completed` after.
- For each test: exactly one `test_started`, then exactly one of `test_passed` / `test_failed` / `test_skipped`.
- `claim_acquired` and `claim_released` are paired per file.
- `fixture_build_started` / `fixture_build_done` are paired per build.
- `fixture_cache_hit` fires AFTER successful restore — never on a corrupt entry that turns into a rebuild.

Consumers can rely on these to track in-flight state — e.g. counting "in-flight files" as `file_dispatched - file_completed`.

## Practical patterns

### "Why did this run take so long?"

```
provium tests/ --save-events events.msgpack
# parse events.msgpack to find the longest file_completed.duration_ns
```

### "Which fixtures rebuilt?"

```
provium tests/ --save-events events.msgpack
# count fixture_build_started events
```

If many fixtures are rebuilding, something invalidated the cache — usually a kernel swap or a helper edit.

### "Spec coverage report"

```
provium tests/ --include-slow --coverage
```

`provium-coverage` reads `meta.spec` from each `test_passed` / `test_failed` event and produces a spec-section report.

### "What was the guest doing when this test failed?"

The `test_failed` event includes `console_excerpt` — the last 4 KiB of every booted VM's console log captured at the failure moment. Useful when failures are kernel-side and reproducing locally is expensive.

## See also

- [Events reference](~provium/reference/events) — every event, every field.
- [Protocol version](~provium/reference/protocol-version) — wire-shape pinning.
- [The CLI](~provium/running-tests/the-cli) — `--save-events`, `--events-stdout`, `--events-socket`, `--coverage`.
