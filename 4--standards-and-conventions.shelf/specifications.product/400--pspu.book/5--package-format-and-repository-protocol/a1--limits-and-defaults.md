---
title: Limits and Defaults
description: Every limit and default of this chapter in one place.
---

## Limits

| Limit | Value |
|---|---|
| Package name | At most 64 characters, at least 3 labels (§5.3) |
| Capability | 2 to 128 characters (§5.4) |
| Closure, index, channel, or repository name | 1 to 64 characters (§5.9) |
| PIP signature | 3310 bytes, version byte 1 (§5.16) |
| Bucket | The first 2 hexadecimal digits of SHA-256 of the name (§5.31) |

## Defaults

| Default | Value |
|---|---|
| Store | `/system/artifacts` |
| Closures | `closures/` in the artifact directory |
| Repository configuration | `/conf/ppk/repositories/`, written under `/lcl/conf/ppk/` |
| Repository state | `/var/state/ppk/` |
| Architecture | The consumer's own |
| License class | `unknown` |
| Signature context | `ppk repository` |
