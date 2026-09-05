---
title: Token Adjustment
description: What can be changed on a live token — privileges, groups, interactivity scope and object-creation defaults — and what cannot.
---

A live token's privileges, groups, default object-creation metadata,
and interactive session metadata can be adjusted at runtime. These are
distinct operations with separate access rights and constraint models.
All of them mutate the token object in place using atomic operations,
all become visible immediately to every thread sharing the token, and
all bump `modified_id`. [*token.adjust.in-place-visible-bumps-modified-id]

## AdjustPrivileges

Requires `TOKEN_ADJUST_PRIVILEGES` on the token, and has three modes. [*token.adjust.privs.requires-right]

**Enable and disable** flips individual bits in `privileges_enabled`
for privileges present on the token. A privilege that is not present
cannot be enabled, and disabling one that is already absent is a
no-op. [*token.adjust.privs.absent-enable-fails-disable-noop] The operation activates existing privileges; it never grants
new ones.

**Reset to defaults** restores `privileges_enabled` to match
`privileges_enabled_by_default`, returning every privilege to its
creation-time state in one operation. It is encoded as a single
`kacs_priv_entry` with `luid = 0` and
`attributes = KACS_PRIV_RESET_ALL_DEFAULTS`. [*token.adjust.privs.reset-encoding] The reset touches only
`privileges_enabled`: it does not restore privileges that were removed
from `privileges_present`. [*token.adjust.privs.reset-does-not-restore-removed]

**Remove** permanently deletes a privilege, clearing its bit in
`privileges_present`, `privileges_enabled`, and
`privileges_enabled_by_default` together. Removing an already-absent
privilege is a no-op. [*token.adjust.privs.remove-absent-noop] The deletion is irreversible; nothing re-adds a
privilege to a token.

Duplicate privilege indices in one request are invalid. [*token.adjust.privs.duplicate-indices-invalid] The kernel
validates every entry before applying any change, so an invalid entry
fails the whole operation with no state change at all. [*token.adjust.privs.all-or-nothing] The caller
receives a report of each adjusted privilege's previous state. [*token.adjust.privs.reports-previous-state]

## AdjustGroups

Requires `TOKEN_ADJUST_GROUPS` on the token, and has two modes. [*token.adjust.groups.requires-right]

**Enable and disable** flips `SE_GROUP_ENABLED` on individual groups,
within two constraints. A group carrying `SE_GROUP_MANDATORY`,
`SE_GROUP_USE_FOR_DENY_ONLY`, or `SE_GROUP_LOGON_ID` cannot be
adjusted **in either direction** — not enabled, not disabled, whatever
its current state; naming one in a request fails the whole call. [*token.adjust.groups.protected-attributes-either-direction] And
the user SID, when it appears in the group list, cannot be disabled,
which is the one constraint that is direction-scoped. [*token.adjust.groups.user-sid-cannot-disable]

**Reset to defaults** restores every group to its creation-time
enabled state. It restores only that state — it does not clear
`SE_GROUP_USE_FOR_DENY_ONLY` from a group that FilterToken marked
deny-only afterwards. [*token.adjust.groups.reset-keeps-deny-only]

Groups are addressed by zero-based index into the token's groups
array. A count of 0 is invalid, as is a count above 1024, as are
duplicate indices in one request. [*token.adjust.groups.count-and-duplicate-limits] Reset is encoded as a single
`kacs_group_entry` of `{ index = 0xFFFFFFFF, enable = 0 }`. [*token.adjust.groups.reset-encoding]

The caller receives the previous enabled state of every group as a
1024-bit mask encoded as sixteen 64-bit words in ascending order: word
0 covers group indices 0–63, word 1 covers 64–127, and bit `i % 64` of
word `i / 64` corresponds to group index `i`. Since group arrays cap
at 1024 entries, the mask is complete for any valid token. [*token.adjust.groups.previous-state-mask]

## AdjustInteractivityScope

Requires `TOKEN_ADJUST_INTERACTIVITY_SCOPE` on the token and
`SeTcbPrivilege` on the caller's real token. [*token.adjust.interactivity-scope.gates] It changes the token's
`interactivity_scope` to a new `u32` and nothing else: the field is
metadata, and changing it grants or removes no privilege, group,
access right, label, claim, default owner, default primary group,
default DACL, or any other authorization state. [*token.adjust.interactivity-scope.metadata-only]

## AdjustDefault

Requires `TOKEN_ADJUST_DEFAULT` on the token, and covers three fields. [*token.adjust.default.requires-right]

The **default DACL** applied to new objects is replaced by an RCU
pointer swap, with the old DACL freed after a grace period. The
**owner SID index** changes which SID becomes the default owner of new
objects, and has to reference the user SID or a group carrying
`SE_GROUP_OWNER`. The **primary group index** changes the default
primary group, and has to reference the user SID or any group SID on
the token. Both index updates are atomic.

All three affect future object creation only; existing objects are
untouched. [*token.adjust.default.future-objects-only] None can escalate anything, because the caller is choosing
among SIDs already on their own token.

`audit_policy` is fixed at creation, and no adjustment operation
changes it.
