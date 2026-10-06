---
title: "lcs.audit.key.opened"
description: "The record that a registry key was opened and what access the open received."
---

- **Event type:** `lcs.audit.key.opened`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** a matching SACL audit ACE on the key
- **Cardinality:** once per matching open

The record that a registry key was opened and what access the open
received. SACL evaluation follows the KACS AccessCheck algorithm, with the
SACL evaluated alongside the DACL rather than separately.

**A request of `MAXIMUM_ALLOWED` alone records nothing.** It maps to a
desired mask of zero, and the SACL walk tests each audit ACE's mask against
that mask, so no ACE matches. The one request shape that asks for
everything is the one shape that produces no record — a real hole for
anyone auditing key opens, and the same defect KACS's own SACL walk was
changed to close.

Emission failure is handled in two halves. If a valid payload cannot be
**constructed**, the open fails with `EIO` and no key descriptor is
published — the audit is a precondition of the access. If a valid payload
cannot be **retained** by KMES, the decision and the descriptor stand, and
the loss is accounted as a gap in the stream rather than as a failed open.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`caller`](~peios/events/groups/group-caller) | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`caller`](~peios/events/groups/group-caller) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`caller`](~peios/events/groups/group-caller) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`caller`](~peios/events/groups/group-caller) | The impersonation level of the effective token. |
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `key`. Names the table the access masks decode against. |
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | required | The registry key an operation acted on. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | After registry generic mapping, with `MAXIMUM_ALLOWED` re-added when the caller asked for it. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | Forced to zero on a denial, and enforced rather than merely intended — a denied record carrying a non-zero granted mask is rejected as malformed. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the open was allowed. Replaces the former `decision` string, which carried the same two states as words. |
| [`trigger.sacl-match`](~peios/events/field-index/fields-trigger#trigger.sacl-match) | `uint.flags` | required | Which flavour of audit ACE matched. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
