---
title: Privilege lifecycle
type: concept
description: Each privilege on a token is in one of four states — absent, present-disabled, present-enabled, or used. This page covers the transitions between states, what AdjustPrivileges does, how FilterToken removes a privilege permanently, and why removal is one-way.
related:
  - peios/privileges/overview
  - peios/privileges/intent-gated
  - peios/tokens/lifecycle
  - peios/tokens/restricted-tokens
---

A privilege's state on a token is more than just "yes, the token has it". The four-state model — absent, present-disabled, present-enabled, used — exists so a service can hold a sensitive privilege most of the time without exercising it, enable it briefly when it actually needs it, disable it again afterwards, and have all of those transitions auditable.

This page covers each transition: how privileges get added (only one moment), how they get enabled and disabled (many times), how they get permanently removed (one-way), and what the "used" bit means for auditing.

## The four states, redux

From the [Privileges overview](~peios/privileges/overview):

| State | Bitmask representation | Meaning |
|---|---|---|
| Absent | `present` bit clear | Not on the token. AccessCheck cannot use it. |
| Present, disabled | `present` set, `enabled` clear | On the token but not in effect. AccessCheck ignores it. |
| Present, enabled | `present` set, `enabled` set | In effect. AccessCheck will use it where applicable. |
| Used (overlaid) | `used` bit set, independent of the others | Has been exercised at least once. Sticky. |

The bitmask is a 64-bit word. Each privilege occupies a fixed bit position (its LUID determines which). The token actually carries four independent 64-bit words: `present`, `enabled`, `enabled_by_default`, and `used`. Most code only cares about the first two.

`enabled_by_default` records the initial state — what was enabled at token creation. The kernel uses it to implement the "reset to defaults" sentinel in AdjustPrivileges.

## Adding a privilege: only at creation

There is **exactly one** moment when a privilege can be added to a token: when the token is being created. Specifically:

- During boot, the kernel constructs the SYSTEM token with every privilege present and enabled.
- When authd calls `kacs_create_token`, the wire-format specification names the privileges to include and which of them should start enabled.
- When peinit calls `kacs_create_token` for a service.

DuplicateToken preserves the privilege bitmask of the source — every present bit, every enabled bit, every used bit copies into the new token. The duplicate has the same privileges as the source.

That is the entire list of paths. There is no syscall, no ioctl, no privileged API to *add* a privilege to an existing token. A token's `present` bitmask is at most what it was at creation; it can only shrink over time.

This rule is one of the load-bearing parts of the security model. It is what makes "the principal's authority is fully expressed by their token" true. If a process could acquire new privileges at runtime, the kernel would need to track which privilege-acquisition paths exist and protect each one. By making creation the only entry point and authd the only entity that can use it, the kernel concentrates the privilege-policy decision into one component, audited at one moment.

## Enabling and disabling: AdjustPrivileges

The most common runtime operation on privileges is enabling or disabling them. The syscall is `AdjustPrivileges` (also reachable as the `KACS_IOC_ADJUST_PRIVS` ioctl on a token fd).

The caller passes an array of `kacs_priv_entry` records, each containing:

- A **LUID** identifying which privilege to adjust.
- An **attributes** value telling the kernel what to do with it.

The attributes value is one of:

| Value | Effect |
|---|---|
| `0` | Disable the privilege. Clears the `enabled` bit; leaves `present` set. |
| `SE_PRIVILEGE_ENABLED` (0x02) | Enable the privilege. Sets the `enabled` bit. The privilege must already be present. |
| `SE_PRIVILEGE_REMOVED` (0x04) | Permanently remove the privilege. Clears `present`, `enabled`, and `enabled_by_default`. Does **not** clear `used`. Irreversible. |
| `KACS_PRIV_RESET_ALL_DEFAULTS` (0x80000000) | Sentinel value, used with LUID 0. Resets every privilege on the token to its `enabled_by_default` state. |

The operation is **atomic**: every entry in the array is validated first, and if any one is invalid (a LUID for a privilege not present on the token, an unknown attributes value, a duplicate LUID), the entire call fails and no changes are made. There is no partial success.

The call returns the **previous state** of every privilege touched, as a bitmask. Callers that want to do scoped privilege enable — turn on a privilege, do work, turn it off — read the return value to know what state to restore to. The pattern:

1. Save previous state by calling AdjustPrivileges to enable the desired privilege.
2. Do the work.
3. Call AdjustPrivileges again with the saved state to restore.

If the privilege was already enabled before step 1, step 3 leaves it enabled. If it was disabled, step 3 restores it to disabled. Either way the work runs with the privilege enabled and the original state is preserved.

### What AdjustPrivileges cannot do

`AdjustPrivileges` cannot:

- **Add a privilege.** A LUID for a privilege not present on the token is rejected. The token must already have the privilege; AdjustPrivileges only changes its enabled state or removes it.
- **Resurrect a removed privilege.** Once `SE_PRIVILEGE_REMOVED` is applied, the privilege is absent. A subsequent attempt to enable it fails (the privilege is no longer present).
- **Toggle the `used` bit.** The kernel sets `used` automatically when a privilege is exercised. Userspace cannot clear it.
- **Set `enabled` without `present`.** The kernel rejects this — a privilege cannot be enabled if it is not present on the token. The "enabled but absent" state is not representable.

The right to call AdjustPrivileges is gated by `TOKEN_ADJUST_PRIVILEGES` (0x0020) on the target token. A thread can always adjust its own token's privileges (the default token SD grants this right to the token's user identity); adjusting another process's token requires `PROCESS_QUERY_INFORMATION` on that process, `TOKEN_ADJUST_PRIVILEGES` on the token, and the appropriate PIP dominance.

## The "used" bit and audit

When AccessCheck or any other kernel path actually exercises a privilege on a token, the kernel sets the corresponding bit in the token's `used` bitmask. Once set, the bit remains set for the life of the token. Nothing — not AdjustPrivileges, not FilterToken, not DuplicateToken into a fresh token — clears it.

The bit is for auditing. It answers the question "did this token, at some point in its existence, exercise this privilege?". A security audit can read a token's `used` bitmask to see which privileges have been engaged so far. A privilege that is present but never used is materially different from one that has been used; the `used` bit records the difference.

This is why removal does not clear `used`. If a privilege has been exercised, removing it later does not erase the fact. The audit trail remains.

DuplicateToken copies `used` from the source. A duplicate of a token that has used a privilege is itself marked as having used it, even though the duplicate has never actually exercised it. The rationale: a duplicate inherits the source's audit history; if the source has used a privilege, anything derived from it is suspect of having access to that privilege's effects.

If you need a fresh, audit-clean token, you need a freshly-minted token (a new authentication, or a new `kacs_create_token` call). Duplicates carry history.

## Permanent removal

`SE_PRIVILEGE_REMOVED` permanently removes a privilege from a token. After removal:

- `present` is clear.
- `enabled` is clear.
- `enabled_by_default` is clear.
- `used` remains whatever it was (still set if the privilege was exercised before removal).

The removal is irreversible. There is no syscall to re-add. The only way back to a token with the privilege is to start with a different token — typically by FilterToken from a source that still has the privilege, or by a fresh authentication.

Removal is the right tool for:

- **Service hardening.** A service that holds privileges by default but only needs them at startup can remove them after the startup phase. Removing rather than disabling makes the privilege unrecoverable for the remainder of the service's lifetime — even if an attacker compromises the service later, the privileges are gone.
- **Sandbox launchers.** Code that forks a child to run untrusted work removes every dangerous privilege from the child's token before exec. The child has no way to get them back.
- **One-way demotion.** A process starting with high authority that wants to demote itself to a lower-privileged identity, irrecoverably, removes the privileges it no longer wants. This is stronger than disabling: a disabled privilege can be enabled by code running on the token (assuming `TOKEN_ADJUST_PRIVILEGES`); a removed privilege cannot.

The one-way nature is the point. The model is built around the assumption that authority shrinks. A removed privilege is gone for the same reason a disabled group can be marked use-for-deny-only and not un-marked: each is a deliberate restriction the kernel will not let userspace undo.

## FilterToken and bulk removal

For removing multiple privileges at once — typically during sandbox creation — `FilterToken` is the appropriate API. Where AdjustPrivileges with `SE_PRIVILEGE_REMOVED` removes one privilege from the calling token, FilterToken produces a **new token** with the listed privileges removed.

The difference matters: FilterToken does not modify an existing token. It creates a copy with the listed adjustments (privileges removed, groups marked use-for-deny-only, restricted SIDs added) and returns the new token. The original is unchanged.

This is the right pattern for sandbox launchers, which want to filter a token down to a restricted version for a child process without affecting their own running identity. AdjustPrivileges with `SE_PRIVILEGE_REMOVED` is the right pattern for code that wants to demote *itself*.

FilterToken is covered in [Token lifecycle](~peios/tokens/lifecycle) and [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens).

## The reset-to-defaults sentinel

A token records `enabled_by_default` separately from `enabled`. The two diverge as the token's privileges get enabled and disabled at runtime; the default record stays as it was at creation.

The `KACS_PRIV_RESET_ALL_DEFAULTS` sentinel — a `kacs_priv_entry` with `luid = 0` and the sentinel attributes value — tells AdjustPrivileges to copy `enabled_by_default` back into `enabled`. Every privilege that was enabled at creation is now enabled again; every privilege that was disabled at creation is now disabled again.

The sentinel is useful for code that does "enable a few privileges, do work, restore". Instead of saving the prior state and restoring it explicitly, the code can simply reset to defaults — which is the right behaviour as long as nothing else has changed the defaults (which nothing should, since defaults are immutable at creation).

The reset sentinel only affects `enabled`. It does not bring back removed privileges. It does not clear the `used` bit. It is a cheap way to "go back to how this token started" within the set of operations that still make sense.

## Field mutability summary

To pin the entire model on one table:

| Field | Mutability |
|---|---|
| `present` | Only ever *clears* (via `SE_PRIVILEGE_REMOVED`). Set only at token creation. |
| `enabled` | Toggled freely between `0` and the corresponding `present` bit. |
| `enabled_by_default` | Immutable after token creation. |
| `used` | Set by the kernel when the privilege is exercised. Never clears. |

The asymmetric mutability is the model's spine. Authority can decrease at runtime but not increase. State for auditing accumulates. Defaults are fixed. The "easy" mutation — toggle enabled — is the only one that goes both ways, and it does not affect what the token fundamentally is.
