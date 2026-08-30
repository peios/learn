---
title: Using evctl
description: Run eventd queries from a terminal or pipeline, select a stable output encoding, and understand when results become visible.
---

`evctl` is eventd's native command-line client. Its normal operation has no
subcommand: the one positional argument is a PSPU observability query.

```sh
evctl 'EVENTS kacs.* SINCE 1h ago TAKE 50'
evctl 'LOGS FROM authd ERROR ONLY STREAM'
evctl 'METRIC cpu.usage SINCE 10m ago AVG'
```

Quote the complete query. Without the quotes, the shell can split string
literals or expand `*` patterns before `evctl` sees them. Query syntax and
semantics remain those of PSPU §3.18–§3.27; `evctl` does not maintain a second
flag-based query language.

## Commands and queries

Exact standalone words such as `help` and `version` occupy the command
namespace. Anything whose first word is `EVENTS`, `LOGS` or `METRIC`, matched
without regard to ASCII case, is a query. This leaves room for administrative
commands without requiring the common query operation to be written as
`evctl query ...`.

The query can instead be read from a UTF-8 file or standard input:

```sh
evctl --file denied-events.evq
printf '%s\n' 'EVENTS synthetic.* SINCE 1d ago' | evctl -
```

The default socket is `/run/eventd/query.sock`. `--socket PATH` selects a
nonstandard configured socket. The server obtains the caller from the Unix
socket peer token and performs every identifier and field access check; the
client never opens an eventd database or substitutes its own authorization
decision.

## Output

Data is written to standard output. Diagnostics and query errors are written
to standard error, so redirecting or piping the result does not mix the two.

| Format | Selection | Use |
|---|---|---|
| Pretty | `--format pretty` (default) | One self-describing record per line, with terminal emphasis on field names. |
| JSON Lines | `--format jsonl` | One JSON object per record for text pipelines. Binary, extension and non-finite floating-point values use tagged objects rather than being discarded. |
| MessagePack | `--format msgpack` | A lossless binary sequence. Each record is preceded by a four-byte little-endian payload length. |

Records do not have a uniform schema. A field absent from one line is not
necessarily absent from later lines. Scripts should select the fields they
need in the query or tolerate missing object keys.

## Result commitment

An `ok` response is not, by itself, a completed result. A non-streaming query
only succeeds when eventd sends `end`; a streaming query's initial result only
succeeds when eventd sends `watch` (PSPU §3.16). If eventd reports an error
before that point, every preceding record belongs to an invalid partial result
and must be discarded.

`evctl` therefore renders initial records into an anonymous temporary spool.
It publishes the spool to standard output only after `end` or `watch`. The
spool bounds heap use independently of the result count and has no pathname to
clean up after a crash. After `watch`, new records are written directly as they
arrive. Closing `evctl`, including with Ctrl-C, closes the query connection and
ends the watch.

As with every streaming client, a blocked output pipeline eventually applies
socket backpressure. eventd may terminate that stream rather than allowing a
slow observer to interfere with ingestion.
