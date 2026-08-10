# PSD-004 (KACS): Changes in v0.22

## Summary

v0.22 is a feature-expanding revision over the finalized v0.20. The headline
work is the rename of the "logon session" object and its associated ABI surface
to **LogonSession** (with `interactive_session_id` becoming `interactivity_scope`),
the addition of a kernel-resident **lifecycle event schema** appendix and a
`kacs_privilege_check` syscall, the activation of the previously-reserved
`SE_SERVER_SECURITY` inheritance behavior, **InheritedObjectType** inheritance
filtering, and the split of system-wide profiling into a new
`SeSystemProfilePrivilege`. The remainder is hardening (PIP/LSV coupling,
default-deny `/proc`, same-user elevation isolation) and clarification of
under-specified evaluation behavior.

## Breaking Changes

- §1.2, §2.x, §4.2–§4.7, §13.1, §13.2, §13.7 — the "logon session" object is
  renamed **LogonSession** throughout. ABI-visible consequences:
  - Syscall 1004 `kacs_create_session` → `kacs_create_logon_session`; syscall
    1006 `kacs_destroy_empty_session` → `kacs_destroy_empty_logon_session`
    (parameter renamed `session_id` → `auth_id`).
  - Ioctl `KACS_IOC_ADJUST_SESSIONID` → `KACS_IOC_ADJUST_INTERACTIVITY_SCOPE`;
    token access right `TOKEN_ADJUST_SESSIONID` →
    `TOKEN_ADJUST_INTERACTIVITY_SCOPE` (§4.8, value `0x0100` unchanged).
  - Token field `interactive_session_id` → `interactivity_scope` (§4.2);
    query class `TokenSessionId` → `TokenInteractivityScope`, wire constant
    `TOKEN_CLASS_SESSION_ID` → `TOKEN_CLASS_INTERACTIVITY_SCOPE` (§13.2, §13.7).
  - Wire-format field `session_id` → `logon_session_id` in the token and
    link-tokens specs (§13.7).
- §13.1(kacs_impersonate_peer) — now returns the **effective impersonation
  level** (0–3) on success instead of `0`.
- §4.2, §10.3 — `integrity_level` is now a numeric `uint`; any `S-1-16-X` SID
  with one sub-authority is a valid mandatory label and is compared
  numerically. v0.20 accepted only the five standard integrity SIDs and
  rejected any other `S-1-16-*` SID as malformed.
- §4.4(FilterToken) — `user_deny_only` is now **copied from the source token**
  when `write_restricted` is not requested. v0.20 forced it to `false`.
- §4.3, §13.2(KACS_IOC_INSTALL) — primary-token installation now additionally
  requires the new token's user SID and LogonSession (`auth_id`) to match the
  target's current primary token unless the caller holds SeTcbPrivilege;
  `KACS_IOC_INSTALL` also now requires `PROCESS_SET_INFORMATION` on the target.
- §7.2 — `SeProfileSingleProcessPrivilege` is redefined to gate only
  cross-task profiling of a specific other process (own-task profiling
  requires no privilege). System-wide profiling is moved to the new
  `SeSystemProfilePrivilege` (see Additions).
- §12.2 — `CAP_PERFMON` now **OR-maps** to `SeSystemProfilePrivilege OR
  SeProfileSingleProcessPrivilege OR SeLoadDriverPrivilege` (v0.20:
  `SeProfileSingleProcessPrivilege` only).
- §8.2 — `/proc/<pid>/` PIP enforcement is now **default-deny**: for a
  non-dominant caller of a PIP-protected target, all files and symlinks under
  `/proc/<pid>/` are denied. v0.20 enforced a curated entry list.
- §5.3 — the default process SD now carries a SACL mandatory-label ACE at the
  process's integrity level. A lower-integrity process can no longer perform
  write-category operations (signals, memory write, token replacement) on a
  same-user higher-integrity process.
- §10.2 — a NULL DACL now marks all granted bits as **decided** in addition to
  granting them, so the restricted-token and confinement passes see a full
  grant from a NULL DACL during their intersections.

## Additions

- §13.9 (new appendix file `9-lifecycle-events`) — Lifecycle Event Schemas:
  KMES event types and msgpack payloads for `token-create`, `process-create`,
  and `process-exec`.
- §13.1 — new syscall `kacs_privilege_check` (number **1007**): atomically
  checks a privilege set on the caller's effective token, marks them used, and
  emits audit events.
- §3.1, §3.6 — `SE_SERVER_SECURITY` is now functional. The inheritance
  algorithm appends server ACEs from the caller's primary token's default DACL
  to objects created with the flag set. v0.20 reserved the flag and required
  implementations to fail closed.
- §3.6 — **InheritedObjectType filtering**: the inheritance algorithm accepts
  an optional `child_class_guid` (a fourth input source) that scopes object-ACE
  inheritance to a specific child class.
- §3.6 — resource-attribute inheritance filtering via the new
  `CLAIM_SECURITY_ATTRIBUTE_NON_INHERITABLE` flag; auto-set of
  `SE_DACL_AUTO_INHERITED` / `SE_SACL_AUTO_INHERITED` when inherited ACEs are
  present; enforcement of the 65,535-byte serialized-SD size limit on computed
  SDs (inheritance receives no exception).
- §3.9 — new flag `CLAIM_SECURITY_ATTRIBUTE_NON_INHERITABLE` (`0x0001`); new
  validity limits: attribute name ≤ 256 UTF-16 code units, `ValueCount` ≤ 1024.
- §2.2 — additional well-known SIDs: `S-1-5-3` (Batch), `S-1-5-9` (Enterprise
  Domain Controllers), `S-1-5-12` (Restricted Code), `S-1-5-13` (Terminal
  Server Users), `S-1-5-14` (Remote Interactive Logon), `S-1-5-15` (This
  Organization), `S-1-5-17` (IUSR); BUILTIN `S-1-5-32-548/549/550/552`
  (Account/Server/Print Operators, Replicators).
- §7.2 — new privilege `SeSystemProfilePrivilege` for system-wide performance
  profiling (per-CPU, all-task, kernel-mode events).
- §9.3 — **Anonymous-in-Everyone policy**: a registry-backed, SeTcbPrivilege-
  gated kernel setting controlling whether Anonymous tokens carry Everyone
  (`S-1-1-0`). Default is excluded (secure).
- §4.3 — documented well-known LogonSession LUIDs `SYSTEM_LUID` (999) and
  `ANONYMOUS_LOGON_LUID` (998); dynamically created LogonSessions start at 1000.
- §5.2 — PIP now auto-sets LSV (Library Signature Verification) when `pip_type`
  is set to a value other than None at exec.
- §5.3 — new "Thread security model" section: no per-thread SDs;
  `kacs_open_thread_token` is gated by the process SD (`PROCESS_QUERY_INFORMATION`).
- §8.3 — new sections covering fd inheritance across PIP transitions (no fd
  sanitization in v0.22) and the absence of a PIP debug opt-out.
- §12.1 — new "Compatibility model" section: Linux-compatibility shims are a
  crash-prevention mechanism, not a security mechanism.
- §12.2 — OR-mapping mechanism for Linux capabilities that span multiple Peios
  privilege tiers.
- §13.2 — token fds are now created `O_CLOEXEC` by default (not inherited
  across `execve()` unless `FD_CLOEXEC` is explicitly cleared).

## Structural Changes

- Appendix A (chapter 13) is reordered and gains a new file. Section addresses
  changed as follows; external references must be updated:
  - kernel-api: §13.8 → **§13.4**
  - inspection: §13.4 → **§13.5**
  - boot: §13.5 → **§13.6**
  - abi-reference: §13.6 → **§13.7**
  - audit-events: §13.7 → **§13.8**
  - lifecycle-events: **§13.9** (new)

## Clarifications

- §5.3, §8.2, §14.B — signal delivery gains an explicit **structural
  same-process exemption**: delivery within the same process security state is
  not a process-boundary operation, and the exemption MUST NOT depend on the
  default SD's self-ACE (restricted/confined tokens fail AccessCheck against
  their own SD; `raise()`/`abort()`/`pthread_kill()` MUST still work). v0.20
  as originally published specified self-bypass language for the neighboring
  enforcement points but was silent for `task_kill`, and the reference
  implementation enforced the full two-check path on self-signals — a defect
  fixed alongside this clarification. The clarification is also mirrored into
  the v0.20 text as an erratum.
  Additionally specified: per-target evaluation with partial delivery for
  multi-target sends (`kill(0/-pgid/-1)`); POSIX's same-session `SIGCONT`
  exception is intentionally not implemented; terminal-generated job-control
  signals are kernel-originated and bypass the gate (authorization for them is
  possession of the controlling terminal); `si_pid`/`si_uid` are projected,
  informational-only values.
- §3.1 — an object MUST carry exactly one Security Descriptor (no semantic
  change). `SE_DACL_TRUSTED` description trimmed to "Reserved" (no semantic
  change).
- §3.3 — reserved access-mask bits reworded: now explicitly preserved during
  round-trip serialization and ignored during evaluation, rather than simply
  "MUST NOT be used."
- §3.4 — unrecognized ACE types are preserved **byte-for-byte** during
  round-trip serialization (no semantic change).
- §3.6 — ApplicationData (conditional-expression bytecode) is preserved
  verbatim during inheritance; no SID substitution or generic mapping is
  applied inside the bytecode.
- §3.7 — `SeTakeOwnershipPrivilege` overrides OWNER_RIGHTS deny ACEs (DACL
  denials are not mandatory decisions); an `SE_GROUP_OWNER` group may be set as
  owner even when deny-only (no semantic change — formalizes existing intent).
- §3.10 — resource-attribute name comparison is case-insensitive.
- §4.4 — the kernel injects only the logon SID; authd is responsible for
  including implicit groups (Everyone, Authenticated Users, etc.) in the
  supplied `groups` array.
- §9.3, §13.2 — Anonymous tokens are identity-stripped on both the socket path
  and via `KACS_IOC_DUPLICATE` to Anonymous (Anonymous is an identity boundary,
  not a cosmetic flag). New sections specify the per-call level constraint (no
  `SECURITY_QUALITY_OF_SERVICE` equivalent), the lack of thread-to-thread
  impersonation, the impersonation credential holding its own token reference,
  and the `SOCK_DGRAM` rejection rationale.
- §10.3 — a non-dominant caller's MIC allowed set always includes
  `READ_CONTROL` and `SYNCHRONIZE`.
- §10.6 — confinement conditional-expression scoping is fully specified:
  membership and device-membership operators are confinement-scoped, while
  non-membership operators evaluate against the real token's claims and the
  object's resource attributes.
- §10.10 — the intersection invariant is stated explicitly: the restricted,
  confinement, and CAAP passes can only narrow the granted set, and MIC/PIP
  denials persist through all later stages.
- §11.2 — `kacs_open` MUST run the full AccessCheck pipeline to completion even
  on denial; implementations MUST NOT short-circuit before the audit steps.
- §11.6 — ownership change is a two-phase check (WRITE_OWNER, then validation
  of the specific owner SID being set); mandatory resource-attribute protection
  rationale added.
- §6.1 — the binary-signing revocation section is expanded with the available
  and unavailable mitigations for a compromised signed binary (no semantic
  change).
- §7.2 — `SeChangeNotifyPrivilege` bypasses traverse checking via
  `FILE_TRAVERSE`, with caching guidance for the path-resolution hot path.
- §8.2 — note that `perf_event_open()` target resolution is enforced via a
  target-resolved syscall-path patch (Linux 7.0), not the stock hook alone.
