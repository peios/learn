---
title: PSB Overview
---

The Process Security Block (PSB) is a per-process security structure that carries properties describing **what the process is**, independent of the principal running it.

The PSB's PIP identity fields (`pip_type` and `pip_trust`) are determined by the binary loaded at exec time as specified in §5.2 and §6.1. Other PSB fields, including process mitigations and process restrictions, are process policy fields governed by §5.2; they are not token identity and are not determined by the principal running the process.

The PSB is separate from the token. The token describes identity and travels with impersonation -- when a thread impersonates a client, the effective token changes. The PSB describes the process and MUST NOT be affected by impersonation. This is the load-bearing invariant:

> The PSB is never affected by impersonation. Impersonation changes who the thread is acting as. It does not change what the process is.

The canonical PSB reference lives on the task's LSM security blob (`task_struct->security`), separate from the credential which holds the token pointer. Implementations MAY also store a mirrored, non-authoritative PSB reference in credential security blobs for Linux hooks that receive only credentials. For any task-attached credential, this mirrored reference MUST refer to the same PSB as the task security blob, and it MUST NOT be used to define a different process identity.

The credential may be swapped during impersonation. Impersonation MAY change the credential's token pointer, but it MUST NOT change the canonical PSB, and any credential-level PSB mirror MUST continue to refer to the same PSB.
