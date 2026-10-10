---
title: Save incident event evidence
type: how-to
description: Save a bounded evctl query with its diagnostics and context, check that the capture completed, and keep sensitive records private.
related:
  - peios/logs-and-events/find-missing-records
  - peios/logs-and-events/overview
  - peios/evctl/using-evctl
  - peios/file-permissions/managing-file-security
---

Use `evctl` to save a finite event query before changing configuration or
cleaning up storage. Keep the result, diagnostics and capture context
together so another authorized reviewer can tell what was queried and
whether it finished.

This procedure saves the records available to your query. It does not
recover missing records or establish a complete incident history.

## 1. Choose a private destination

Work in an **existing, writable directory you control**, whose native
security descriptor and new-file inheritance already restrict access to
the intended readers. Event payloads and diagnostics may contain sensitive
information. Check the destination policy before writing, using
[Managing file security](~peios/file-permissions/managing-file-security) and
[Inheritance](~peios/security-descriptors/inheritance). If the required
policy is unknown, have the responsible administrator check it first.
Do not rely on `chmod` or a shell `umask` to establish Peios-native privacy.

Choose **new, unused filenames** for both the result and diagnostics.
The shell opens redirection targets before `evctl` runs: reusing a name
can truncate previous evidence even if the query later fails. Do not
target existing files, symlinks or pipes.

Allow space for both the result and `evctl`'s temporary spool. The temporary
directory selected by the process must also be suitable for sensitive data,
writable, have free space, and support anonymous temporary files
(`O_TMPFILE`). A writable output directory alone is not enough.

## 2. Record what you are capturing

In your private incident notes, record:

- the host and the identity running the query;
- the incident time range and time zone, and when you start the capture;
- the exact query, output format, destination filenames and any nondefault
  query socket;
- the installed tool version, shown by `evctl version`;
- relevant service, job and boot identifiers, if known.

Choose the event names and time range for the incident. The example below
asks for at most 50 readable `kacs.*` events since one hour ago. It is a
bounded sample, not all events from that hour. A relative range also moves
when you rerun it, which makes the capture time important.

The query runs with the caller's access. Do not widen permissions to make
the result appear complete. For query options and formats, see
[Using evctl](~peios/evctl/using-evctl).

## 3. Save the result and diagnostics separately

After selecting the private working directory and confirming that both
names are unused, run the complete quoted query. Save the exit status
immediately, before running another command:

```sh
evctl --format jsonl 'EVENTS kacs.* SINCE 1h ago TAKE 50' > incident-events.jsonl 2> incident-events.err
capture_status=$?
printf 'evctl exit status: %s\n' "$capture_status"
```

JSON Lines writes one JSON object per record. Standard error goes to the
separate diagnostic file. Record the displayed status and the capture's
finish time in the same notes, then inspect the diagnostics.

Leave `STREAM` out of a finite capture. Do not pipe the capture through
`head` or another consumer that can close early: `evctl` treats a broken
output pipe as success, so a zero pipeline status cannot prove that all
query output was saved. Review or filter the saved file afterward.

## 4. Decide whether the capture completed

For the direct-to-regular-file command above, `evctl` reports:

| Status | Meaning | Next step |
|---|---|---|
| `0` | The finite query completed and output publication succeeded. | Keep the result with the diagnostics and context. |
| `2` | Command-line usage error. | Read the diagnostic, correct the invocation, and use new filenames. |
| `1` | Query, connection, protocol, input or output failure. | Keep the error and mark the capture failed; diagnose before retrying with new filenames. |

If the shell cannot open a redirection target, `evctl` may never run;
record that shell error too. Treat any interrupted or otherwise nonzero
attempt as failed.

`evctl` buffers initial records until the server completes the query. A
server error before completion prevents those records from being published.
However, copying the completed result to your file is **not atomic**: a
destination write or flush failure can leave a partial file. Do not treat
such a file as a completed query result, even if some lines look valid.
Keep it labelled as a failed attempt with its diagnostics.

An empty output file alone is ambiguous. It can accompany a failed query,
or a successful query with no visible matching records. Always check status
and diagnostics. If the capture failed, inspect both destination and
temporary-filesystem errors; do not delete eventd databases to make room.

## 5. Keep the limits with the evidence

Retain the exact query and its `TAKE` limit, times, identity, version,
status and diagnostics with the result. Read policy can omit records
without notice, and retention, collection loss or an unavailable store
can limit what remains queryable. Follow
[Find missing records](~peios/logs-and-events/find-missing-records) when
expected data is absent.

Keep the original capture private and unchanged while reviewing it.
Check the contents and intended recipient before sharing; a result you
may read is not automatically suitable for a wider audience.

## Implementation reference

The capture behavior above is backed by these paths in eventd commit
`3df88bab845d962e866158896807eac2976b83e3`. Check the installed version when
applying it to another build.

- [CLI options and output channels](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/cli.rs#L9-L35)
- [Query completion and publication](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/main.rs#L43-L87)
- [Exit status and broken-pipe handling](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/main.rs#L14-L22),
  with [failure classifications](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/main.rs#L106-L119)
- [Temporary spool and final copy](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/output.rs#L42-L95)
