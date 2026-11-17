---
title: Machine Repository Configuration
description: The repositories a machine fetches from, the file for each, the identity it requires, whether an unrooted chain is accepted, the channel it tracks, and what the machine records of each.
---

A machine fetches from the repositories its configuration names.

## Files

Each repository is a file of its own, `/conf/ppk/repositories/<name>.toml`,
where `<name>` follows §5.9:

```toml
path = "/mnt/peios-repo"
identity = "pkgs.peios.org"
track = "stable"
```

A repository served over HTTP (§5.34) is given by its base URLs, tried in
order:

```toml
urls = ["http://cache.lan/peios/", "https://pkgs.peios.org/"]
identity = "pkgs.peios.org"
track = "stable"
```

| Key | Holds |
|---|---|
| `path` | Where the repository is, as a directory |
| `urls` | The base URLs the repository is served at, at least one, tried in order (§5.34) |
| `identity` | The name its pointer file is signed under (§5.33); with it, the signature is checked |
| `unrooted` | `true` to accept an Unrooted chain as well as a Rooted one; `false` by default |
| `anchor` | The object hash of the top-level its chain has to end at, in lowercase hexadecimal |
| `track` | The index or channel a request for a bare name follows |

A file MUST have exactly one of `path` and `urls`. `unrooted` and `anchor`
are given only with `identity`. A consumer MUST refuse any other key.
`/conf` merges what the system ships, under `/usr/conf`, with the
machine's own, under `/lcl/conf`: a consumer reads `/conf/ppk` and writes
what the machine adds under `/lcl/conf/ppk`.

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
