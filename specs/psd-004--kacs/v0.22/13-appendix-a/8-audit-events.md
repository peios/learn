---
title: Audit Event Schemas
---

This appendix defines the exact KMES event type strings and msgpack payload
schemas for the KACS event families currently owned by the slow track. KACS
owns these schemas. KMES owns event transport, buffering, and the common event
header.

This appendix is intentionally bounded to:

- object-access audit events from the SACL walk and token audit-policy forcing
- privilege-use audit events from privilege contribution accounting
- per-operation continuous-audit events emitted by enforcement points for
  handles carrying a continuous audit mask
- CAAP diagnostic events from CAAP SACL evaluation errors and staged/effective
  result differences
- logon-session destroy events emitted when the final token reference to a
  published session is released

It does not define:

- KMES header or transport behavior

## Common payload rules

All KACS audit event payloads are msgpack maps with UTF-8 string keys.

- Consumers MUST ignore unknown keys.
- Required keys MUST be present.
- Msgpack map key order is not significant.
- SID values are msgpack `bin` objects containing the exact binary SID bytes
  defined by `sids/format.md`.
- ACE values are msgpack `bin` objects containing the exact binary ACE bytes
  defined by `security-descriptors/ace-types.md`.
- `object_context` is the caller-supplied `object_audit_context` blob from
  `kacs_access_check*`, carried through verbatim as msgpack `bin`. For
  enforcement-point continuous-audit events that do not retain such a blob, or
  when the caller supplied no object context, `object_context` is msgpack
  `nil`.

The `subject` map captures the effective token used for the access decision.
During impersonation, this is the impersonated token, not the thread's primary
token.

### subject map

| Key | Type | Meaning |
|---|---|---|
| `user_sid` | `bin` | Effective token user SID. |
| `group_sids` | `array<bin>` | Full effective token group SID set in token order. Disabled and deny-only groups are still included. |
| `integrity_level` | `uint` | Effective token integrity level value. |
| `pip_type` | `uint` | Effective token PIP type used for the decision. |
| `pip_trust` | `uint` | Effective token PIP trust value used for the decision. |

### process map

| Key | Type | Meaning |
|---|---|---|
| `pid` | `uint` | PID of the current task at emission time. |
| `name` | `str` | Current task name. |
| `executable_path` | `str` | Executable path of the current task. |

## access-audit

KMES event type string: `access-audit`

This event family covers object-access audit events emitted from the
AccessCheck SACL walk and from token audit-policy forcing.

Payload keys:

| Key | Type | Meaning |
|---|---|---|
| `subject` | `map` | Subject map defined above. |
| `object_context` | `bin` or `nil` | Caller-provided opaque object identifier. |
| `requested_access` | `uint` | Generic-mapped requested access mask (`mapped_desired`). |
| `granted_access` | `uint` | Final granted mask used to determine success/failure. |
| `success` | `bool` | Final access outcome. |
| `trigger` | `map` | Trigger map defined below. |
| `process` | `map` | Process map defined above. |

### access-audit trigger map

| Key | Type | Meaning |
|---|---|---|
| `kind` | `str` | One of: `sacl`, `policy`. |
| `ace` | `bin` or `nil` | Exact matched audit ACE bytes when `kind = "sacl"`. `nil` when `kind = "policy"`. |

Trigger semantics:

- `kind = "sacl"` means the event was emitted because a matching audit ACE
  fired during the SACL walk.
- `kind = "policy"` means the event was emitted only because the token's
  `audit_policy` forced object-access auditing for this outcome.

## continuous-audit

KMES event type string: `continuous-audit`

This event family covers per-operation events emitted after AccessCheck has
returned a continuous audit mask and an enforcement point has stored that mask
on a handle.

Payload keys:

| Key | Type | Meaning |
|---|---|---|
| `subject` | `map` | Operation-time effective token subject map defined above. |
| `object_context` | `bin` or `nil` | Opaque object identifier when retained by the enforcement point; otherwise `nil`. |
| `operation` | `str` | Stable enforcement-point operation name. FACS file-handle operations use `file.*` names. |
| `requested_access` | `uint` | Normalized required-access mask for the attempted operation. |
| `matched_access` | `uint` | Nonzero subset of `requested_access` that overlapped the handle's continuous audit mask. |
| `granted_access` | `uint` | Access mask cached on the handle at the time of the operation. |
| `success` | `bool` | Per-operation enforcement result. |
| `process` | `map` | Operation-time process map defined above. |

Emission semantics:

- An enforcement point MUST emit this event when
  `(continuous_audit_mask & requested_access) != 0`.
- No event is emitted for unmanaged handles, zero required-access operations,
  or operations whose required mask does not overlap the handle's continuous
  audit mask.
- The event is emitted after the operation-specific access decision is known,
  so both successful and denied attempts are represented.
- `subject` and `process` identify the task performing the operation. They do
  not need to match the opener that caused the handle's continuous audit mask
  to be populated.
- If the enforcement point cannot construct a required event, it MUST fail
  closed. KMES transport readiness, buffering, and drop accounting are KMES
  behavior.

## privilege-use

KMES event type string: `privilege-use`

This event family covers privilege-use audit events emitted after the complete
AccessCheck pipeline.

Payload keys:

| Key | Type | Meaning |
|---|---|---|
| `subject` | `map` | Subject map defined above. |
| `object_context` | `bin` or `nil` | Caller-provided opaque object identifier. |
| `privilege` | `str` | Canonical privilege name from `privileges/catalog.md` (for example `SeBackupPrivilege`). |
| `requested_access` | `uint` | Requested access bits attributed to this privilege. |
| `granted_access` | `uint` | Bits granted by this privilege before later narrowing by MIC, confinement, or CAP. |
| `surviving_access` | `uint` | Bits from `granted_access` that survived into the final result. |
| `success` | `bool` | True when at least one requested bit contributed by the privilege survived to the final result; false otherwise. |
| `process` | `map` | Process map defined above. |

## caap-policy-diagnostic

KMES event type string: `caap-policy-diagnostic`

This event family covers diagnostics required by `PSD-004 §10.8` for CAAP
policy evaluation. It is not an access decision event. It records policy
evaluation conditions that MUST be durable even though enforcement continues
under the normal CAAP rules.

Payload keys:

| Key | Type | Meaning |
|---|---|---|
| `subject` | `map` | Subject map defined above. |
| `object_context` | `bin` or `nil` | Caller-provided opaque object identifier. |
| `kind` | `str` | One of: `sacl-error`, `staging-mismatch`. |
| `phase` | `str` or `nil` | `effective-sacl` or `staged-sacl` for `sacl-error`; `nil` for `staging-mismatch`. |
| `policy_sid` | `bin` or `nil` | Scoped policy SID when the diagnostic is tied to a single CAAP rule; otherwise `nil`. |
| `rule_index` | `uint` or `nil` | Zero-based rule index when the diagnostic is tied to a single CAAP rule; otherwise `nil`. |
| `reason` | `str` | Stable diagnostic reason string. |
| `requested_access` | `uint` | Generic-mapped requested access mask (`mapped_desired`). |
| `effective_granted_access` | `uint` | Effective CAAP scalar/root granted mask after policy evaluation. |
| `staged_granted_access` | `uint` | Staged CAAP scalar/root granted mask after policy evaluation. |
| `object_results_differ` | `bool` | True when result-list effective and staged per-node grants differ. |
| `process` | `map` | Process map defined above. |

Emission semantics:

- `kind = "sacl-error"` MUST be emitted when a CAAP effective or staged SACL
  cannot be parsed or evaluated at runtime. The failing SACL contribution is
  skipped. The error MUST NOT widen access and MUST NOT suppress other object
  or CAAP SACL contributions.
- `kind = "staging-mismatch"` MUST be emitted when effective and staged CAAP
  DACL or SACL results differ. The staged result MUST NOT affect access or
  normal audit emission.
- For result-list AccessCheck, `effective_granted_access` and
  `staged_granted_access` carry the scalar/root grants. Per-node differences
  are represented by `object_results_differ`.
- If a required CAAP diagnostic event cannot be constructed or emitted, the
  AccessCheck ingress path MUST fail closed.

## logon-session-destroyed

KMES event type string: `logon-session-destroyed`

This event family covers logon-session lifecycle cleanup emitted when a
published session object is destroyed after the final token reference is
released.

Payload keys:

| Key | Type | Meaning |
|---|---|---|
| `session_id` | `uint` | Destroyed session id (`auth_id`). |
| `user_sid` | `bin` | Session user SID. |
| `logon_type` | `uint` | Session logon type value. |
| `auth_package` | `str` | Session authentication package string. |
| `created_at` | `uint` | Session creation timestamp stored on the destroyed session object. |

Lifecycle semantics:

- The event is emitted exactly once for a given published session object.
- The event is emitted after the session has been removed from the published
  session set, so later session lookup by id fails.
- The event payload is derived from the destroyed session object's stored
  fields; no additional userspace lookup is consulted.
