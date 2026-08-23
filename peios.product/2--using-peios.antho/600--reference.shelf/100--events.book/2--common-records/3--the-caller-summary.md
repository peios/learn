---
title: The Caller Summary
description: The registry's own identity submap, why LCS carries it instead of the subject record, and how the two compare field by field.
---

LCS uses its own identity submap, `caller`, rather than the subject
record. Six of its seven audit events carry it.

It exists separately because LCS's events are emitted from a different
subsystem with a different bound on what it will serialise. The two
records overlap but are not interchangeable, and a consumer handling
both needs to read each on its own terms.

| Key | Meaning |
|---|---|
| `effective_token_guid` | The token the operation ran under. |
| `true_token_guid` | The underlying token, where impersonation is in play. |
| `process_guid` | The calling process. |
| `user_sid` | The effective token's user SID. |
| `authentication_id` | The logon session LUID. |
| `token_id` | The token's own LUID. |
| `token_type` | Primary or impersonation. |
| `impersonation_level` | 0 for a primary token. |
| `integrity_level` | The token's integrity RID. |

Nine fields, and no more. Group lists, privilege arrays, claims and
default DACLs are unbounded and are never included — the same reasoning
that shapes the subject record (§2.1), applied independently.

## Against the subject record

| | `subject` | `caller` |
|---|---|---|
| Emitted by | KACS | LCS |
| Identity by | SIDs | GUIDs, plus `user_sid` |
| Groups | `group_sids` with attributes | absent |
| PIP state | `pip_type`, `pip_trust` | absent |
| Linux projection | `projected_uid` | absent |
| Session join key | `auth_id` | `authentication_id` |

Note the session join key is spelled differently in each. Correlating a
KACS event with an LCS event on the same logon session means matching
`subject.auth_id` against `caller.authentication_id`.
