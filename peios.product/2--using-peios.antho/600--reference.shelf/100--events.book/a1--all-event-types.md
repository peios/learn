---
title: All Event Types
description: Every event type in this book in one table — thirty-four types across six emitters, plus the registry's watch records and the known holes.
---

Every event type in this book, in one table. Thirty-four types across
six emitters, plus the registry's watch records, which are a separate
mechanism.

## KMES events

| Type | Emitter | Where |
|---|---|---|
| `access-audit` | KACS | §3.1 |
| `continuous-audit` | KACS | §3.2 |
| `privilege-use` | KACS | §3.3 |
| `caap-policy-diagnostic` | KACS | §3.4 |
| `logon-session-destroyed` | KACS | §3.5 |
| `corrupt-sd` | KACS | §3.6 |
| `STRATAFS_COPY_UP` | StrataFS | §4.1 |
| `STRATAFS_MUTATION_REFUSED` | StrataFS | §4.2 |
| `LCS_KEY_OPEN_AUDIT` | LCS | §5.2 |
| `LCS_BACKUP_START` | LCS | §5.1 |
| `LCS_BACKUP_COMPLETE` | LCS | §5.1 |
| `LCS_RESTORE_START` | LCS | §5.1 |
| `LCS_RESTORE_COMPLETE` | LCS | §5.1 |
| `LCS_SOURCE_VALIDATION_FAILURE` | LCS | §5.3 |
| `LCS_SELF_CONFIG_INVALID` | LCS | §5.3 |
| `job.created` | peinit | §6.1 |
| `job.started` | peinit | §6.1 |
| `job.ended` | peinit | §6.1 |
| `operation.requested` | peinit | §6.2 |
| `operation.started` | peinit | §6.2 |
| `operation.completed` | peinit | §6.2 |
| `operation.failed` | peinit | §6.2 |
| `operation.cancelled` | peinit | §6.2 |
| `operation.merged` | peinit | §6.2 |
| `operation.aborted` | peinit | §6.2 |
| `peipkg.install` | peipkg | §7.1 |
| `peipkg.upgrade` | peipkg | §7.1 |
| `peipkg.uninstall` | peipkg | §7.1 |
| `peipkg.refresh` | peipkg | §7.1 |
| `peipkg.transaction-failed` | peipkg | §7.1 |
| `peipkg.recovery` | peipkg | §7.1 |
| `peipkg.authorisation` | peipkg | §7.1 |
| `peipkg.repo-add` | peipkg | §7.1 |
| `peipkg.repo-remove` | peipkg | §7.1 |
| `peipkg.claim` | peipkg | §7.1 |
| `peipkg.config-change` | peipkg | §7.1 — **specified, not emitted** |

## Not KMES

| Type | Emitter | Transport | Where |
|---|---|---|---|
| `synthetic.gap` | eventd | Written direct to a shard | §8.1 |
| `synthetic.startup` | eventd | Written direct to a shard | §8.1 |
| `synthetic.shutdown` | eventd | Written direct to a shard | §8.1 |
| `synthetic.storage_error` | eventd | Written direct to a shard | §8.1 |
| `synthetic.config_change` | eventd | Written direct to a shard | §8.1 |
| Watch records | LCS | `read()` on a key fd | §5.4 |

## Which carry an identity, and how

| Events | Identity from |
|---|---|
| KACS, all but `logon-session-destroyed` | `subject` record in the payload (§2.1) |
| `logon-session-destroyed` | `user_sid` and `session_id` directly; the session was the subject |
| LCS, six of seven | `caller` summary in the payload (§2.3) |
| StrataFS, peinit, peipkg | The **envelope** only. No identity in the payload (§1.2) |
| eventd synthetic | None. eventd is describing itself |

## Known holes

Collected from the chapters, because a reader planning coverage needs
them in one place:

- `peipkg.config-change` is never emitted (§7.1).
- peipkg omits the source repository on install and upgrade, the
  transaction id on committed cross-root success, and emits nothing for
  automatic recovery, recovery failures, declined prompts, insecure
  transport, unsigned installs under an `optional` policy, or
  `peipkg-compose` (§7.2).
- A registry key open requesting `MAXIMUM_ALLOWED` alone emits no
  `LCS_KEY_OPEN_AUDIT`, because the mapped desired mask is zero and no
  ACE matches zero (§5.2).
- StrataFS refusals raised before a provider is known emit an empty
  `provider_stratum` (§4.2).
- `caap-policy-diagnostic` with `kind = staging-mismatch` does not
  identify which rule differed, and its two masks can be equal while
  `object_results_differ` is true (§3.4).
- There is no `logon-session-created`, no `token-created`, and no
  heartbeat (§3.6).
- peipkg emits nothing when the caller's token lacks the audit privilege
  (§7.1).
