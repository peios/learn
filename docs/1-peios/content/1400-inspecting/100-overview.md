---
title: Inspecting tokens, sessions, and processes
type: concept
description: The kernel exposes several read-only surfaces for inspecting live KACS state — /proc/<pid>/token, /sys/kernel/security/kacs/self, /sys/kernel/security/kacs/sessions, and the KACS_IOC_QUERY ioctl on token fds. This page is the map for what each surface gives you and the access rules for reading them.
related:
  - peios/inspecting/tokens
  - peios/inspecting/sessions
  - peios/inspecting/processes
  - peios/access-decisions/debugging-a-denial
  - peios/tokens/overview
  - peios/logon-sessions/overview
---

When something goes wrong with access control, the answer is almost always in the live kernel state — what's on the relevant token, what's on the object's SD, what session the calling thread belongs to. Static configuration (the directory, the registry) tells you what *should* be the case; the live kernel state tells you what *is* the case. Inspection is how you read it.

Peios exposes inspection through a handful of surfaces: pseudo-files under `/proc` for per-process tokens, `securityfs` entries under `/sys/kernel/security/kacs/` for the calling thread and the active sessions, and the `KACS_IOC_QUERY` ioctl on any token fd for the full menu of structured queries. This page maps the surfaces and the access rules they share; later pages in this topic cover each in depth.

## What you can inspect

Three classes of state are inspectable:

| State | Lives in | Primary inspection surface |
|---|---|---|
| **Tokens** | Per-thread (primary or effective), reference-counted in the kernel | `/proc/<pid>/token`, `/proc/<pid>/task/<tid>/token`, `/sys/kernel/security/kacs/self`, `KACS_IOC_QUERY` on a token fd |
| **Logon sessions** | Per-authentication-event, referenced by every token via `auth_id` | `/sys/kernel/security/kacs/sessions` (text listing); `TokenStatistics` query on a token (to get the session ID) |
| **Processes** | Per-process, PSB plus process SD plus token references | The process's token fd (for token state); querying the PSB (for PIP, mitigations); reading the process SD via `kacs_get_sd` |

The fourth thing one might expect — inspecting security descriptors on arbitrary objects (files, registry keys) — is covered by `kacs_get_sd`, which is the same syscall used for setting SDs in read-only mode. That surface is part of the file-access and registry-access topics, not this one. This topic covers inspection of identity-and-process state specifically.

## What you cannot inspect

A few things that are not inspectable through this topic's surfaces:

- **Per-thread state for threads other than the inspection target.** The token fd you get from `/proc/<pid>/token` is the primary token (a process-wide property). For thread-specific impersonation state, you need the thread-specific path `/proc/<pid>/task/<tid>/token`.
- **Internal kernel state.** Reference counts, internal locks, cache state — these are not exposed. The inspection surfaces expose user-meaningful state only.
- **Historical state.** A token that has been destroyed is gone; its fields cannot be recovered. The kernel does not retain a history of tokens. For historical analysis you need the audit log.
- **Other principals' state without authority.** Reading another process's token requires `PROCESS_QUERY_INFORMATION` on the process plus PIP dominance plus the token access rights. The surfaces enforce all three. There is no "global view" available to a non-privileged caller.

## Who can inspect what

The access rules for inspection mirror the access rules for the underlying state. The kernel does not have a separate "inspection" privilege; reading state requires the same rights that any other read of that state would require.

For **your own state** (your thread's effective token, your process's primary token, the sessions you are part of):

- `/proc/self/token`, `/proc/self/task/<self-tid>/token` — always readable.
- `/sys/kernel/security/kacs/self` — always readable.
- Token fd from `kacs_open_self_token` — always returnable to you.

For **another process's state**:

- `/proc/<pid>/token` requires `PROCESS_QUERY_INFORMATION` on the target process **plus** PIP dominance.
- `/proc/<pid>/task/<tid>/token` requires the same.
- Token fd from `kacs_open_process_token` requires the same plus the appropriate token rights.

For **session state**:

- `/sys/kernel/security/kacs/sessions` requires `BUILTIN\Administrators` or `SYSTEM` (enforced by the SD on the securityfs file).
- Individual session details accessible via tokens you can already read (your own, or others' subject to the above rules).

For **process state** beyond the token (process SD, PIP, mitigations):

- Read your own PSB via `kacs_open_self_token` or querying through the process-token's interface — always.
- Read another process's PSB requires `PROCESS_QUERY_INFORMATION` plus PIP dominance.

The pattern: self is free, others need standard cross-process authority. PIP dominance is the absolute ceiling that nothing — no privilege, no inspection magic — bypasses. The kernel does not expose state of higher-trust processes to lower-trust callers under any conditions.

## Two ways to read a token

The kernel exposes two complementary ways to read what a token holds:

- **Get a token fd, then query via `KACS_IOC_QUERY`.** This is the structured API. The ioctl takes a query class (one of 24 numbered classes) and returns binary data structured according to that class. Suitable for programmatic inspection.
- **Read a pseudo-file** under `/proc` or `/sys/kernel/security/kacs/`. Some of these expose token fds (open them with O_PATH semantics and pass to ioctls); others expose text formats suitable for direct reading.

Both routes converge on the same kernel state. The pseudo-file route is convenient for shell-level inspection; the ioctl route is the right tool for programmatic use. A monitoring tool will typically use the ioctl; a sysadmin debugging an issue at a terminal will typically `cat` a pseudo-file.

The pseudo-files under `/proc/<pid>/token` are not text — they are token fds. `cat`-ing them does not produce human-readable output. The way to use them from the shell is the [`token`](~peios/tokens/token-command) command, which knows how to interpret a token fd and render its contents as readable text.

The `/sys/kernel/security/kacs/sessions` file *is* a text format — designed to be `cat`-able. It is the exception; the other surfaces are binary.

## Standard query patterns

A handful of patterns come up repeatedly:

- **"Who is this thread?"** — Open `/proc/<pid>/task/<tid>/token`, query class `TOKEN_USER` or equivalent to get the user SID.
- **"What groups are on this token?"** — Open the token, query the groups class.
- **"What privileges are enabled?"** — Open the token, query the privileges class.
- **"Which session does this process belong to?"** — Open the process's primary token, query `TokenStatistics` to get the `auth_id`, then look up that ID in `/sys/kernel/security/kacs/sessions`.
- **"Who owns this session?"** — Either query `TokenStatistics` (returns the auth_id) and look up the session in the listing, or read the listing directly and find the session by its details.
- **"What PIP level is this process at?"** — Read the PSB through the process's token-related surfaces.

The two-step lookup for sessions (token → auth_id → sessions listing) is the standard pattern. Tokens know which session they belong to via auth_id; the session listing has the human-readable details (logon type, auth package, user SID, creation time).

## Where to start

If you want to inspect a token — what fields it has, how to query each one, the two-call pattern for variable-length data — read [Inspecting tokens](~peios/inspecting/tokens).

If you want to inspect a session — the text listing format, how to find which tokens belong to a session, how to track session lifecycle — read [Inspecting sessions](~peios/inspecting/sessions).

If you want to inspect a process — the process SD, the PSB's PIP and mitigation fields, the rules for cross-process inspection — read [Inspecting processes](~peios/inspecting/processes).

If you have a denial in front of you and want a systematic walk through the diagnosis, [Debugging a denial](~peios/access-decisions/debugging-a-denial) is the right page.
