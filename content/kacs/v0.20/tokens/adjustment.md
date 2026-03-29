---
title: Token Adjustment
order: 5
---

A live token's privileges and groups MAY be adjusted at runtime. These are distinct operations with separate access rights and constraint models. All adjustment operations mutate the token object in place via atomic operations. Changes are visible immediately to all threads sharing the token. All bump `modified_id`.

## AdjustPrivileges

**Requires:** `TOKEN_ADJUST_PRIVILEGES` on the token.

Three modes:

- **Enable/disable** — flip individual bits in `privileges_enabled` for privileges that are present on the token. Privileges that are not present MUST NOT be enabled. This operation cannot grant new privileges, only activate existing ones.
- **Reset to defaults** — restore `privileges_enabled` to match `privileges_enabled_by_default`. Returns all privileges to their creation-time state in a single operation.
- **Remove** — permanently delete a privilege from the token. Clears the bit in `privileges_present`, `privileges_enabled`, and `privileges_enabled_by_default`. Irreversible — the privilege MUST NOT be re-added.

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

The caller receives a report of the previous state of each adjusted group.

## AdjustDefault

**Requires:** `TOKEN_ADJUST_DEFAULT` on the token.

Three mutable fields:

- **Default DACL** — replace the DACL applied to new objects created by this token. RCU pointer swap; the old DACL is freed after an RCU grace period.
- **Owner SID index** — change which SID is used as the default owner for new objects. MUST reference the user SID or a group with SE_GROUP_OWNER on the token. Atomic index update.
- **Primary group index** — change the default primary group for new objects. MUST reference the user SID or a group SID on the token. Atomic index update.

These affect future object creation only — existing objects are unaffected. No escalation is possible: the caller is choosing among SIDs already on their token.
