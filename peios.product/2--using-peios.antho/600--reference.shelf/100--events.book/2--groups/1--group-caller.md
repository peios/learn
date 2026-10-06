---
title: "caller group"
description: "The identity LCS records on an audited operation."
---

- **Group:** `caller`
- **Defined in:** `lcs.evman`

The identity LCS records on an audited operation. A deliberate subset of
`subject` — the token's durable GUIDs ride in the event header, and the
group SIDs and PIP state that KACS records are absent here.

**That absence is a gap rather than a design.** Access to a registry key is
granted through a group as often as to a user SID directly, so an LCS
record cannot answer "which membership let this through" where the
equivalent KACS record can. The two subsystems reached the bound on what to
serialise independently and landed in different places.

## Fields

| Field | Type | Meaning |
|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | The impersonation level of the effective token. |

## Carried by

- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended)
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended)
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started)

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
