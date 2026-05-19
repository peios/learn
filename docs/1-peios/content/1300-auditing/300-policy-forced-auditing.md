---
title: Policy-forced auditing
type: concept
description: Some audit events fire independent of any SACL ACE. Privilege-use events fire when a privilege contributes to the granted mask. The token's audit_policy bitmask forces success or failure events on object access regardless of SACL. This page covers both mechanisms, when they fire, and how they interact with SACL-driven audit.
related:
  - peios/auditing/overview
  - peios/auditing/audit-aces
  - peios/auditing/events-and-transport
  - peios/privileges/overview
  - peios/tokens/token-types
---

Not every audit event comes from an audit ACE in an SACL. Two mechanisms produce events that fire regardless of whether an SACL ACE matched: **privilege-use audit** (fires when a privilege contributes bits to the granted mask) and the **token's audit_policy bitmask** (forces object-access or privilege-use events whenever the corresponding flag is set on the token).

Both mechanisms are *forced* by something other than an SACL ACE — by the privilege exercise itself, or by the token's per-principal audit policy. They run during the same audit walk as SACL ACEs but are independent of any specific ACE matching.

This page covers both mechanisms, when each fires, and how they compose with SACL-driven audit.

## Privilege-use audit

When AccessCheck completes, the pipeline knows which privileges contributed bits to the granted mask. A backup tool that used `SeBackup` to bypass the DACL has the privilege recorded against the bits it contributed; an administrator who used `SeTakeOwnership` to gain `WRITE_OWNER` has that privilege recorded.

If the calling token's `audit_policy` requests it, the kernel fires a **privilege-use event** for each privilege that contributed. The events fall into two flavours:

| Flavour | Triggered by | Fires when |
|---|---|---|
| **Successful privilege use** | `audit_policy & PRIVILEGE_USE_SUCCESS` (0x04) | A privilege contributed bits AND those bits survived to the final granted mask. |
| **Failed privilege use** | `audit_policy & PRIVILEGE_USE_FAILURE` (0x08) | A privilege contributed bits BUT those bits did NOT survive (stripped by a later layer like confinement or CAAP). |

The "failed" case is the interesting one. A privilege that fires but does not actually grant access tells the audit log that the caller attempted to exercise a privilege and was prevented by some narrowing layer. This is observable separately from a plain "access denied" — the privilege got far enough to fire and then was stripped.

A worked example. A token with `SeBackupPrivilege` enabled tries to read a confined object. The pipeline:

1. Step 4: SeBackup grants read-category bits via the privilege.
2. Step 8: DACL walk grants nothing additional.
3. Step 11: confinement intersection strips the privilege-granted bits (confinement does not preserve privilege grants).
4. Final granted mask: empty.

If `audit_policy & PRIVILEGE_USE_SUCCESS` is set, no event fires (no bits survived). If `audit_policy & PRIVILEGE_USE_FAILURE` is set, a failed-use event fires, recording "SeBackupPrivilege contributed FILE_READ_DATA but the bits were stripped".

Either configuration is useful. Tracking only success tells you when privileges actually grant access; tracking only failure tells you when privileges *try* to grant access but cannot. Tracking both gives you a complete picture of privilege exercise.

The event itself includes the privilege name (e.g. `SeBackupPrivilege`), the bits the privilege contributed pre-narrowing, the bits that survived to the final result, and a success boolean. The exact schema is in [Events and transport](~peios/auditing/events-and-transport).

## Token audit_policy

The token's `audit_policy` field is a small bitmask with four flags:

| Flag | Value | Effect |
|---|---|---|
| `OBJECT_ACCESS_SUCCESS` | 0x01 | Force an audit event on every successful access by this token, regardless of SACL ACE matches. |
| `OBJECT_ACCESS_FAILURE` | 0x02 | Force an audit event on every failed access by this token. |
| `PRIVILEGE_USE_SUCCESS` | 0x04 | Emit successful privilege-use events. |
| `PRIVILEGE_USE_FAILURE` | 0x08 | Emit failed privilege-use events. |

`PRIVILEGE_USE_*` controls privilege-use audit (above). `OBJECT_ACCESS_*` controls a separate kind of force: object-access events that fire even when no SACL audit ACE matched.

### How OBJECT_ACCESS_SUCCESS / FAILURE work

When the calling token's `audit_policy` has `OBJECT_ACCESS_SUCCESS` set, step 14b of the pipeline fires an object-access event for every access by this token where the granted mask is non-empty — regardless of whether any SACL audit ACE would have matched.

When `OBJECT_ACCESS_FAILURE` is set, an event fires for every access where the granted mask did not satisfy the requested mask (i.e. some requested rights were denied).

These flags effectively say: "audit every access this principal makes, end of story". The audit log gets an event whether or not the object's owner thought to put an audit ACE in the SACL.

The use case: surveillance of specific principals. A security team responding to a suspected compromised account can set `OBJECT_ACCESS_SUCCESS | OBJECT_ACCESS_FAILURE` on that account's tokens (via authd reissuing the token) and capture every access the account makes. The objects' SACLs do not need to be modified; the audit comes from the token policy.

Another use case: high-sensitivity contractors or third parties who need temporary access. Their tokens are issued with `OBJECT_ACCESS_*` flags set so every access is logged independently of which specific objects they touch.

### Setting audit_policy

The `audit_policy` field is set at token creation and is immutable for the lifetime of the token. authd specifies the value when minting the token via `kacs_create_token`. There is no AdjustPrivileges-style call to modify `audit_policy` at runtime.

This is consistent with the rest of the immutable token state. A token's audit policy is decided when it is issued; changing it requires a new token.

For administrators wanting to toggle audit policy on a principal, the mechanism is: have authd reissue the principal's tokens with the new policy. Existing sessions continue to operate under the old policy; new sessions get the new policy. (For more immediate effect, revoke the existing sessions and force re-authentication.)

## Composition with SACL audit

The SACL audit walk (step 14) and the token audit policy (step 14b) run independently. Both can fire events for the same access.

A worked composition example. A SACL has one audit ACE on `Everyone` for `FILE_READ_DATA` with `SUCCESSFUL_ACCESS_ACE_FLAG`. The calling token has `audit_policy = OBJECT_ACCESS_SUCCESS`. An access for read succeeds.

- Step 14 (SACL walk): the audit ACE matches Everyone, the access succeeded, the success flag is set, fire one event with trigger = "sacl" and the matched ACE.
- Step 14b (token-forced): `OBJECT_ACCESS_SUCCESS` is set, the access succeeded, fire one event with trigger = "policy".

Two events for one access. They are not duplicates — they have different triggers, and an audit consumer can distinguish them. The SACL-driven event records that this specific audit ACE matched; the policy-driven event records that the token's audit policy required logging.

In practice, audit consumers either treat both events as one entry (deduplicating by some criteria like access context) or keep them separate. The kernel does not merge them; both fire.

## What policy-forced auditing does *not* do

A few clarifications:

- **Token audit_policy does not affect the access decision.** The flags fire events; they do not gate access. A token with `OBJECT_ACCESS_FAILURE` set is not somehow more likely to be denied; the access check runs identically.
- **Token audit_policy does not fire on every kernel surface.** It fires on AccessCheck-mediated accesses. Operations that do not go through AccessCheck (a syscall the kernel handles directly without an SD lookup, an internal kernel operation) are not subject to it. Privilege-use audit fires only on privileges that fire during AccessCheck, not on privileges exercised in kernel-standalone paths.
- **Privilege-use audit does not always fire.** It fires only when the token's `audit_policy` has the corresponding bit set. A token with `audit_policy = 0` produces no privilege-use events, even when privileges are exercised. The policy is opt-in per token.

## The four bits in detail

A summary table of what each bit controls:

| Bit | Controls | When event fires |
|---|---|---|
| `OBJECT_ACCESS_SUCCESS` (0x01) | Successful object access | After step 14b, when granted mask is non-empty |
| `OBJECT_ACCESS_FAILURE` (0x02) | Failed object access | After step 14b, when requested mask is not fully granted |
| `PRIVILEGE_USE_SUCCESS` (0x04) | Privilege use that succeeded | After step 13, when a privilege's contributed bits survived |
| `PRIVILEGE_USE_FAILURE` (0x08) | Privilege use that failed | After step 13, when a privilege's contributed bits were stripped |

The bits are independent. A token can have all four, none, or any combination. The most common configurations:

| `audit_policy` | Use case |
|---|---|
| `0` | Default. Audit only from SACL ACEs. |
| `OBJECT_ACCESS_FAILURE | PRIVILEGE_USE_FAILURE` | Capture every denial. Useful for security monitoring. |
| `OBJECT_ACCESS_SUCCESS | OBJECT_ACCESS_FAILURE` | Surveillance — every access by this principal. |
| All four | Maximum visibility. Compliance audit, forensics. |

The choice is operational: how much audit volume can the deployment afford to handle, and what is the audit pipeline configured to do with the events. There is no security benefit to setting more bits than the consumer can actually process — events that are dropped because the consumer fell behind are not useful audit.

## Putting it together

The full set of auditing channels:

| Source | Fires when |
|---|---|
| `SYSTEM_AUDIT*` ACE in SACL | The ACE matches the caller's identity and access |
| `SYSTEM_ALARM*` ACE in SACL | Per-operation on an open handle when the operation overlaps the ACE's mask |
| CAAP effective SACL audit ACE | The CAAP rule applied and its audit ACE matched |
| `PRIVILEGE_USE_SUCCESS` audit policy | A privilege contributed surviving bits to the granted mask |
| `PRIVILEGE_USE_FAILURE` audit policy | A privilege contributed bits that were stripped by a later layer |
| `OBJECT_ACCESS_SUCCESS` audit policy | The access succeeded (granted mask non-empty), no SACL ACE match required |
| `OBJECT_ACCESS_FAILURE` audit policy | The access failed (some requested bits denied), no SACL ACE match required |

Plus the session-destruction event (covered in [Logon sessions](~peios/logon-sessions/lifecycle)) which fires independently of any access check.

A single access can produce events from many of these channels at once. An audit consumer sees them, deduplicates or correlates as appropriate, and persists what is needed for downstream use.
