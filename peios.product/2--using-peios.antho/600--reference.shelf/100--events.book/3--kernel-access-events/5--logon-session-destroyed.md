---
title: logon-session-destroyed
description: The event fired when a logon session loses its last token reference — why it has no subject or process, and why nothing matches it at creation.
---

Fires when a logon session loses its last token reference and the kernel
destroys it.

Event type string: `logon-session-destroyed`.

| Key | Type | Meaning |
|---|---|---|
| `session_id` | uint | The destroyed session's LUID. |
| `user_sid` | bin | The session's user SID. |
| `logon_type` | uint | Interactive, Network, and so on. |
| `auth_package` | string | The authenticating package — `Kerberos`, `NTLM`, `local`. |
| `created_at` | uint | When the session was created. |

Every field is always present.

## No subject, no process

This is the only KACS event with neither. The session *was* the subject,
and it has just ended. No process caused it — the last reference simply
went away, which may have been any process exiting, or none in
particular.

## Correlating

`session_id` is the same LUID that every token in that session reported
as `subject.auth_id` (§2.1), and that LCS events report as
`caller.authentication_id` (§2.3). It is the join key for everything
that session ever did.

With `created_at`, the event bounds a session's whole lifetime, which is
what makes it useful for reconstructing a login after the fact.

The event fires **exactly once** per session. Consumers — authd
especially — use it to release session-scoped state: Kerberos tickets,
cached directory data, per-session credentials.

## There is no matching creation event

Nothing is emitted when a session is created, so the pair is asymmetric.
See §3.6 for what else is absent and why.
