---
title: peipkg
description: The package manager itself — its verbs, the flags that change what a transaction may do, and how it exits.
---

`peipkg` is the consumer: the program an operator runs to change what is
installed on a system.

## Verbs

| Verb | Effect |
|---|---|
| `install` | Add packages, resolving and installing their dependency closure |
| `upgrade` | Move installed packages to newer versions; with no name, every installed package |
| `downgrade` | Move a package to an older version, requiring explicit authorisation |
| `uninstall` | Remove packages, cascading to or refusing on dependents |
| `undo` | Revert the effect of a previous transaction |
| `claim` | Inspect, grant, or revoke the holder of a role |
| `repo` | Add, list, remove, and refresh repositories |
| `query`, `list`, `info`, `owns` | Read the package database |
| `verify` | Re-hash installed files against what was recorded at install |
| `recover` | Resolve an interrupted transaction |
| `clean` | Garbage-collect the index cache |

`install` also accepts a local package file rather than a repository
name. A local file has no originating repository and therefore no trust
set to verify its signature against; it is accepted on the operator's
say-so and its format is validated in full, but its authenticity is not
established.

## Flags that change what a transaction is allowed to do

| Flag | Effect |
|---|---|
| `--yes` | Confirm the routine "apply this plan?" prompt |
| `--cascade` | On uninstall, remove dependents rather than refusing |
| `--allow-stale` | Proceed despite a repository's trust state exceeding its maximum age |
| `--claim`, `--claim-all`, `--no-claim` | Change which roles an install claims (§9.4) |
| `--dangerously-bypass-path-restrictions` | Permit an out-of-layout payload from a package that declares itself a special system package |

`--yes` confirms the routine prompt and nothing else. Every elevated
action — a downgrade, a foreign `replaces`, a low-trust provider filling
a high-trust role — raises a distinct authorization that `--yes` does
not satisfy and that is confirmed on its own terms (§13.4).

## Exit behaviour

A refused plan, a failed verification, and a rolled-back transaction all
exit non-zero and name the condition. A committed transaction whose
side effects failed exits zero with a warning: the packages installed,
and a stale cache is recoverable by re-invocation (§11.3).
