---
title: stdbuf
type: reference
description: Run a command with altered buffering on its standard streams.
related:
  - peios/system-and-processes/overview
---

`stdbuf` runs a command with **altered buffering** on its standard streams.

```
stdbuf [options] command...
```

```
$ slow-producer | stdbuf -oL grep error
```

## What buffering is, and why change it

A program usually does not write each piece of output the instant it is produced — it collects output in a buffer and writes it in batches, which is faster. The cost is *delay*: when a program's output feeds a pipe, that batching can hold lines back for a long time, which is unhelpful when you are watching a pipeline live.

`stdbuf` lets you override that batching for a command, so its output appears sooner.

## Setting the buffering

| Option | Stream |
|---|---|
| `-i`, `--input=MODE` | Standard input. |
| `-o`, `--output=MODE` | Standard output. |
| `-e`, `--error=MODE` | Standard error. |

`MODE` is one of:

| MODE | Buffering |
|---|---|
| `0` | Unbuffered — every write goes out immediately. |
| `L` | Line-buffered — output is flushed at the end of each line. Not valid for input. |
| a size | Fully buffered with a buffer of that many bytes. Accepts suffixes — `K`, `M`, and so on. |

`-oL` — line-buffered output — is the common case: it makes a command in a pipeline emit each line as it is finished.

## How it works

`stdbuf` carries a small helper library inside itself. Before running the command it writes that library to a private temporary directory, readable by no one else, and preloads it into the command so the C library's buffering defaults are changed before the command's `main` runs. `stdbuf` then waits for the command and removes the directory afterwards.

The temporary directory lives under `$TMPDIR`. A `TMPDIR` whose path contains a colon cannot be used, because the preload variable is colon-separated; `stdbuf` refuses it rather than run the command with a mangled preload list.

## A limitation

`stdbuf` adjusts the *default* buffering. A command that manages its own stream buffering will override what `stdbuf` sets, and some commands do not use buffered streams at all — for those, `stdbuf` has no effect.

## Exit status

When `stdbuf` runs a command, it exits with **that command's** status. The exception is a failure in `stdbuf` itself:

| Code | Meaning |
|---|---|
| (command's own) | The command ran; this is its exit status. If the command was killed by a signal, `stdbuf` exits with 128 plus the signal number, as a shell would. |
| `125` | `stdbuf` itself failed, for example an unusable `TMPDIR`. |
| `126` / `127` | The command could not be run / could not be found. |
