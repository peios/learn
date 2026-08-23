---
title: The PSB Model
description: The per-process structure describing what a process is, independent of the principal running it.
---

The Process Security Block is a per-process structure carrying
properties that describe **what the process is**, independent of the
principal running it.

Its PIP identity fields, `pip_type` and `pip_trust`, are determined by
the binary loaded at exec (§3.6). Its other fields — process
mitigations and process restrictions — are process policy, set by
whoever launches the process. Neither category is token identity, and
neither is determined by the principal.

Keeping the PSB separate from the token is the point. The token
describes identity and travels with impersonation: when a thread
impersonates a client, the effective token changes. The PSB describes
the process, and impersonation never touches it.

> The PSB is never affected by impersonation. Impersonation changes
> who the thread is acting as. It does not change what the process is.

The canonical PSB reference lives on the task's LSM security blob,
`task_struct->security`, separate from the credential that holds the
token pointer. A mirrored, non-authoritative reference is also kept in
credential security blobs, for the benefit of Linux hooks that receive
only a credential. For any task-attached credential that mirror refers
to the same PSB as the task blob, and it never defines a different
process identity.

Credentials are swapped during impersonation, and that swap may change
the credential's token pointer — but the canonical PSB is untouched
and any credential-level mirror continues to refer to it.
