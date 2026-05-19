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

## A limitation

`stdbuf` adjusts the *default* buffering. A command that manages its own stream buffering will override what `stdbuf` sets, and some commands do not use buffered streams at all — for those, `stdbuf` has no effect.

## Exit status

`stdbuf` exits with the command's own status, or a `stdbuf`-level error code if the command could not be started.
