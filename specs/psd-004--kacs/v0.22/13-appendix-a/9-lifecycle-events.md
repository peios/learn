---
title: Lifecycle Event Schemas
---

This appendix defines the KMES event type strings and msgpack payload schemas
for KACS lifecycle events. These events record the creation and transformation
of security-relevant objects (tokens, processes) so that eventd can correlate
KMES identity stamps back to concrete identities.

This appendix is complementary to the Audit Event Schemas appendix, which
defines AccessCheck-generated events. Lifecycle events are structurally
different — they record object creation, not access decisions.

## Common payload rules

All KACS lifecycle event payloads are msgpack maps with UTF-8 string keys.

- Consumers MUST ignore unknown keys.
- Required keys MUST be present.
- Msgpack map key order is not significant.
- SID values are msgpack `bin` objects containing the exact binary SID bytes
  defined by `sids/format.md`.
- UUID values are msgpack `bin` objects containing exactly 16 bytes.

A null UUID (16 zero bytes) indicates the referenced object does not exist
(e.g., a process with no parent, or a token created outside the normal path).

## token-create

KMES event type string: `token-create`

Emitted whenever KACS creates a new token object. This includes all three
creation paths: minting from scratch (CreateToken), duplicating an existing
token (DuplicateToken), and filtering/restricting an existing token
(FilterToken). The NEW_PROCESS_MIN mechanism, which internally follows
DuplicateToken semantics, also emits this event.

### Payload keys

| Key | Type | Meaning |
|---|---|---|
| `mode` | `str` | One of: `mint`, `duplicate`, `filter`. |
| `token_guid` | `bin` (16 bytes) | The new token's GUID. |
| `source_token_guid` | `bin` (16 bytes) or `nil` | The source token's GUID for `duplicate` and `filter` modes. `nil` for `mint`. |
| `user_sid` | `bin` | The new token's user SID. |
| `user_deny_only` | `bool` | Whether the user SID is deny-only. |
| `group_sids` | `array<bin>` | Full group SID set in token order. |
| `restricted_sids` | `array<bin>` or `nil` | Restricted SID set. `nil` if unrestricted. |
| `write_restricted` | `bool` | Whether the token is write-restricted. |
| `privileges_present` | `uint` | Bitmask of privileges present on the token. |
| `privileges_enabled` | `uint` | Bitmask of privileges enabled on the token. |
| `integrity_level` | `uint` | Token integrity level value. |
| `token_type` | `uint` | 1 = Primary, 2 = Impersonation. |
| `impersonation_level` | `uint` | 0 = Anonymous, 1 = Identification, 2 = Impersonation, 3 = Delegation. |
| `auth_id` | `uint` | LogonSession LUID. |
| `confinement_sid` | `bin` or `nil` | Confinement SID. `nil` if not confined. |
| `interactivity_scope` | `uint` | Interactivity scope number. |
| `projected_uid` | `uint` | Linux UID projection. |
| `projected_gid` | `uint` | Linux GID projection. |

### Mode semantics

- **`mint`**: a new token created from scratch via CreateToken. `source_token_guid` is `nil`. The identity fields reflect the caller-supplied specification plus kernel-generated defaults.

- **`duplicate`**: a token created via DuplicateToken. `source_token_guid` identifies the original token. The identity fields reflect the new token's state after duplication (which may differ from the source in token type and impersonation level). When the target impersonation level is Anonymous, the identity fields reflect the stripped Anonymous token, not the source.

- **`filter`**: a token created via FilterToken. `source_token_guid` identifies the original token. The identity fields reflect the new token's state after filtering (privileges removed, groups set to deny-only, restricted SIDs added, etc.).

The payload always carries the new token's final state, not a delta from the source. This means eventd can resolve a `token_guid` to a complete identity snapshot from a single event, without needing to chase the `source_token_guid` chain.

## process-create

KMES event type string: `process-create`

Emitted when a new process is created (clone without CLONE_THREAD). The event
fires after the child's PSB is initialized with its new `process_guid`.

### Payload keys

| Key | Type | Meaning |
|---|---|---|
| `process_guid` | `bin` (16 bytes) | The new process's GUID. |
| `parent_process_guid` | `bin` (16 bytes) | The parent process's GUID. |
| `token_guid` | `bin` (16 bytes) | The new process's primary token GUID at creation time. |
| `pid` | `uint` | PID of the new process. |
| `parent_pid` | `uint` | PID of the parent process. |

The `token_guid` reflects the token at fork time. If the token is later
replaced (e.g., by peinit installing a service token via IOC_INSTALL), a
separate `token-create` event will have been emitted for the new token, and the
KMES event header on subsequent events will carry the new token's GUID.

## process-exec

KMES event type string: `process-exec`

Emitted when a process calls execve(). This event captures the binary identity
that the process is now running — information not available at fork time.

### Payload keys

| Key | Type | Meaning |
|---|---|---|
| `process_guid` | `bin` (16 bytes) | The process's GUID (unchanged from fork). |
| `token_guid` | `bin` (16 bytes) | The process's primary token GUID at exec time. May differ from the fork-time token if peinit installed a new token between fork and exec. |
| `executable_path` | `str` | Path to the executable being loaded. |
| `pip_type` | `uint` | PIP type determined from the binary's signature. |
| `pip_trust` | `uint` | PIP trust level determined from the binary's signature. |
| `pid` | `uint` | PID of the process. |
