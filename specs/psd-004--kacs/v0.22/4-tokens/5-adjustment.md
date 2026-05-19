---
title: Token Adjustment
---

A live token's privileges, groups, default object-creation metadata, and interactive session metadata MAY be adjusted at runtime. These are distinct operations with separate access rights and constraint models. All adjustment operations mutate the token object in place via atomic operations. Changes are visible immediately to all threads sharing the token. All bump `modified_id`.

## AdjustPrivileges

**Requires:** `TOKEN_ADJUST_PRIVILEGES` on the token.

Three modes:

- **Enable/disable** — flip individual bits in `privileges_enabled` for privileges that are present on the token. Privileges that are not present MUST NOT be enabled. Disabling a privilege that is already absent is a no-op. This operation cannot grant new privileges, only activate existing ones.
- **Reset to defaults** — restore `privileges_enabled` to match `privileges_enabled_by_default`. Returns all privileges to their creation-time state in a single operation.
- **Remove** — permanently delete a privilege from the token. Clears the bit in `privileges_present`, `privileges_enabled`, and `privileges_enabled_by_default`. Removing a privilege that is already absent is a no-op. Irreversible — the privilege MUST NOT be re-added.

Appendix A encodes reset-to-defaults as a single `kacs_priv_entry` with
`luid = 0` and `attributes = KACS_PRIV_RESET_ALL_DEFAULTS`. This reset changes
only `privileges_enabled`; it does NOT restore privileges previously removed
from `privileges_present`.

Appendix A treats duplicate privilege indices in one request as invalid. The
kernel validates all entries before applying any change; if any entry is
invalid, the entire operation fails with no state change.

The caller receives a report of the previous state of each adjusted privilege.

## AdjustGroups

**Requires:** `TOKEN_ADJUST_GROUPS` on the token.

Two modes:

- **Enable/disable** — flip SE_GROUP_ENABLED on individual groups, subject to constraints:
  - SE_GROUP_MANDATORY groups MUST NOT be disabled.
  - SE_GROUP_USE_FOR_DENY_ONLY groups MUST NOT be re-enabled.
  - The logon SID (SE_GROUP_LOGON_ID) MUST NOT be disabled.
  - The user SID (if present in the group list) MUST NOT be disabled.
- **Reset to defaults** — restore all groups to their creation-time enabled/disabled state.

Appendix A encodes groups by zero-based index into the token's groups array.
`count = 0` is invalid. `count > 64` is invalid. Reset-to-defaults is encoded as a single
`kacs_group_entry` with `{ index = 0xFFFFFFFF, enable = 0 }`. Duplicate group
indices in one request are invalid. Reset restores only the enabled/disabled
state; it does NOT clear `SE_GROUP_USE_FOR_DENY_ONLY` if that bit was added
later by FilterToken.

The caller receives a report of the previous enabled state of every group as a
64-bit bitmask. Because token group arrays are capped at 64 entries, this
bitmask is complete for every valid token.

## AdjustSessionID

**Requires:** `TOKEN_ADJUST_SESSIONID` on the token and `SeTcbPrivilege` on the
caller's real token.

AdjustSessionID changes only the token's `interactive_session_id`. The new value
is a `u32` interactive session identifier. The field is metadata: changing it
MUST NOT grant or remove privileges, groups, access rights, labels, claims,
default owner, default primary group, default DACL, or any other authorization
state.

## AdjustDefault

**Requires:** `TOKEN_ADJUST_DEFAULT` on the token.

Three mutable fields:

- **Default DACL** — replace the DACL applied to new objects created by this token. RCU pointer swap; the old DACL is freed after an RCU grace period.
- **Owner SID index** — change which SID is used as the default owner for new objects. MUST reference the user SID or a group with SE_GROUP_OWNER on the token. Atomic index update.
- **Primary group index** — change the default primary group for new objects. MUST reference the user SID or a group SID on the token. Atomic index update.

These affect future object creation only — existing objects are unaffected. No escalation is possible: the caller is choosing among SIDs already on their token.

`audit_policy` is fixed at token creation. No token adjustment operation changes
`audit_policy`.
