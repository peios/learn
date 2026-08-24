---
title: The DWE protocol
type: reference
description: The dwed wire protocol — newline-delimited JSON over vsock or TCP, the request and reply shapes for every operation, error codes, and the transport and versioning rules.
related:
  - peios/dwe/what-dwe-is
  - peios/dwe/driving-a-machine
---

`dwed` speaks **newline-delimited JSON**: one JSON object per line in each direction, with each response carrying the `id` of the request it answers.

JSON rather than a compact binary encoding is a deliberate trade. When `dwed` itself is the thing misbehaving, the protocol has to stay drivable by hand — and being able to type at it and read what comes back is worth more than the bytes a binary framing would save:

```console
$ nc 10.0.0.5 4820
{"id":1,"op":"info"}
{"id":1,"ok":{"reply":"info","protocol_version":1,"dwed_version":"0.1.0",...}}
```

## Framing

A request is an object with an `id` and an `op`, plus that op's arguments inline:

```json
{"id": 7, "op": "exec", "argv": ["ls", "-l", "/system"]}
```

`id` is chosen by the client and echoed back untouched. Requests on one connection are answered in order; concurrency comes from opening more connections, or from detaching work.

A response carries the same `id` and exactly one of `ok` or `error`:

```json
{"id": 7, "ok": {"reply": "exec", "exit": 0, "stdout": "…", "stderr": "", "truncated": false}}
{"id": 7, "error": {"code": "no_such_job", "message": "job 9 is unknown"}}
```

The `reply` field names the shape of the payload. It is there because several replies carry the same fields — `exec` and `job.output` both have `stdout`, `stderr` and an optional `exit` — and a reader should never have to guess which one it is holding from shape alone.

A request that does not parse is still answered, with `id: 0` and a `bad_request` error. Silence would leave a client waiting on an `id` that is never coming, which presents as a hang — the one symptom hardest to tell apart from the bug being investigated.

### Bytes

Every field carrying payload bytes is **base64**: file contents, and captured `stdout`/`stderr` alike.

Output is base64 rather than a JSON string because a guest command's output is not guaranteed to be valid UTF-8, and a tool that mangles a binary is worse than one that refuses it. Clients decode and write raw bytes back out, so the encoding never reaches whoever is driving the tool.

## Operations

### `exec`

Run a command. Synchronous unless `detach` is set.

| Field | | |
|---|---|---|
| `argv` | required | Program and arguments. Executed directly — **not** through a shell. |
| `cwd` | optional | Working directory. |
| `env` | optional | Extra environment, as `[name, value]` pairs, on top of the service's own. |
| `stdin` | optional | Bytes written to the child's stdin, which is then closed. |
| `detach` | optional | Return a job handle immediately instead of waiting. |

Replies `exec` with `exit` (null if signalled), `signal`, `stdout`, `stderr` and `truncated`; or `job` with a `job` handle when `detach` was set.

Both output streams are captured concurrently. A child that fills one pipe while the other goes undrained would otherwise deadlock, and "the command hung" is the least useful thing a debugging tool can report.

### `job.list`

No arguments. Replies `job_list` with a `jobs` array of `{job, argv, running, exit, signal, started}`.

Jobs outlive the connection that created them. They do not outlive `dwed` itself.

### `job.output`

| Field | | |
|---|---|---|
| `job` | required | The handle. |
| `since_stdout` | optional | Resume stdout from this byte offset. |
| `since_stderr` | optional | Resume stderr from this byte offset. |

Replies `job_output` with `stdout`, `stderr`, `stdout_next`, `stderr_next`, `running`, `exit`, `signal` and `truncated`.

The `*_next` values are what to pass as `since_*` on the following call. Cursors are the caller's to keep: `dwed` has no sessions and cannot distinguish two callers, so a server-side cursor would have concurrent readers consuming each other's output. An offset past the end is clamped rather than rejected.

### `job.signal`

`{job, signal}` — deliver a signal to a running job. Replies `done`. A job that has already exited gives `not_running`.

### `file.read`

`{path}` — replies `file_read` with `bytes` and `mode`.

### `file.write`

`{path, bytes, mode?}` — replies `done`. `mode` is applied after writing.

### `info`

No arguments. Replies `info`:

| Field | |
|---|---|
| `protocol_version` | The version `dwed` speaks. |
| `dwed_version` | Its own release. |
| `boot_id` | Distinguishes one boot from the next. |
| `uptime` | Seconds since boot. |

`boot_id` is the field worth using. It lets a client tell "the machine rebooted under me" from "my connection dropped" — two situations that look identical from the socket and mean entirely different things.

## Errors

| `code` | |
|---|---|
| `bad_request` | Malformed JSON, an unknown op, or empty `argv`. |
| `io` | An underlying system call failed. Carries `errno`. |
| `no_such_job` | No job with that handle. |
| `not_running` | The job has already exited. |

`errno` is carried separately from the message so a client can match on the cause rather than parse English.

## Transports

**vsock** is the default, on port 4820. It needs no networking in the guest — which matters, because a machine whose networking is part of what broke is squarely one of the cases DWE exists for. `dwed` binds `VMADDR_CID_ANY`: a guest does not reliably know its own context id, and does not need to.

**TCP** is available on the same port but is **opt-in** (`dwed --tcp 0.0.0.0:4820`). Listening by default would hand the machine to anyone who can route to it, which is more than starting a service should quietly do given there is nothing behind it.

The protocol is identical over either.

> [!CAUTION]
> Neither transport authenticates anything. Whatever reaches the socket owns the machine as `SYSTEM`. See [the security posture](~peios/dwe/what-dwe-is#the-security-posture).

## Versioning

`PROTOCOL_VERSION` is bumped whenever any wire type changes shape. A client compares it against `info` and reports a mismatch rather than misparsing a response it half understands.

There is no negotiation and no compatibility window. Both halves ship from one repository and are built together; a version check is there to give a clear error, not to bridge a gap.
