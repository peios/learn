---
title: Machine Repository Configuration
description: The repositories a machine fetches from, the file for each, its key and the channel it tracks, and what the machine records of each.
---

A machine fetches from the repositories its configuration names.

## Files

Each repository is a file of its own, `/conf/ppk/repositories/<name>.toml`,
where `<name>` follows §5.9:

```toml
path = "/mnt/peios-repo"
key = "ml-dsa-65:…"
track = "stable"
```

| Key | Holds |
|---|---|
| `path` | REQUIRED: where the repository is |
| `key` | Its public key (§5.33); with it, the pointer file's signature is checked |
| `track` | The index or channel a request for a bare name follows |

A consumer MUST refuse any other key. `/conf` merges what the system ships,
under `/usr/conf`, with the machine's own, under `/lcl/conf`: a consumer
reads `/conf/ppk` and writes what the machine adds under `/lcl/conf/ppk`.

## Tracking

A request for a package by a bare name or a constraint, naming no index and
not one exact version, follows the index or channel its repository tracks,
if it tracks one. The closure's inventory records the index (§5.25), so its
meaning doesn't depend on the configuration that chose it.

## State

What the machine has seen of each repository is state, not configuration: a
consumer keeps the highest sequence it has seen of each in
`/var/state/ppk/sequences/<name>`, as a decimal number and a newline
(§5.34).
