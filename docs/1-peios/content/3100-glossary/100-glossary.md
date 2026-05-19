---
title: Glossary
type: reference
description: Brief definitions for every key term used across the Peios documentation. Each entry links to its primary conceptual page for the full story.
related:
  - peios/identity/overview
  - peios/tokens/overview
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
---

This page is a quick reference for terminology. Each entry is one or two sentences plus a link to the conceptual page that covers it fully.

For the structural reference (numbers, struct layouts, constants), see [Constants and catalogs](~peios/constants-and-catalogs/overview).

## A

**AccessCheck.** The kernel function that decides whether a given token may exercise a given access mask against a given security descriptor. Runs as a 15-step pipeline; the output is a granted mask. See [Access decisions](~peios/access-decisions/overview).

**ACE (Access Control Entry).** A single rule inside an ACL — a type byte, flag byte, access mask, SID, and (depending on the type) optional GUIDs or application data. See [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces).

**ACL (Access Control List).** An ordered list of ACEs. The DACL contains access-grant/deny ACEs; the SACL contains audit and system-policy ACEs.

**Anonymous (impersonation level).** The lowest impersonation level. The server gets a token whose user SID is the well-known Anonymous SID (`S-1-5-7`), with no privileges and Untrusted integrity. See [Impersonation levels](~peios/impersonation/impersonation-levels).

**Anonymous token.** A kernel-direct singleton token used as the identity for Anonymous-level impersonation. Session ID 998. See [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens).

**authd.** The userspace authentication daemon. Authenticates users, mints tokens, manages logon sessions, distributes CAAP to the kernel. See [authd handoff](~peios/boot-and-trust-establishment/authd-handoff).

**Auth_id.** A token's reference to the logon session it belongs to. Same value as the session's `session_id`. See [Logon sessions](~peios/logon-sessions/overview).

## B

**BACKUP_INTENT.** A flag passed to AccessCheck that activates `SeBackupPrivilege`. Without it, SeBackup is invisible to the access check. See [Intent-gated privileges](~peios/privileges/intent-gated).

**Binary signing.** The mechanism by which a binary's exec-time PIP type and trust level are decided. Signing is the only path to PIP protection. See [Binary signing](~peios/binary-signing/overview).

**Bootstrap tokens.** The SYSTEM and Anonymous tokens, constructed by direct kernel initialisation rather than via `kacs_create_token`. See [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens).

## C

**CAAP (Central Access and Auditing Policy).** A centrally-defined access policy that objects reference by SID in their SACL. The policy's effective DACL is intersected with the running grant. CAAP only narrows. See [Central access policies](~peios/central-access-policies/overview).

**Capability SID.** A SID in the `S-1-15-3-*` range that names a capability. Used in confinement and in positive confinement. See [Capabilities and modes](~peios/confinement/capabilities-and-modes).

**Capability switchboard.** The classification of the 41 Linux capabilities as ALLOW (always present), PRIVILEGE (mapped to KACS privilege), or DENY (always denied). See [DAC neutralization and capabilities](~peios/linux-compatibility/dac-neutralization-and-capabilities).

**CFI / CFIF / CFIB.** Control Flow Integrity mitigations. CFIF (forward) constrains indirect branches to ENDBR-marked targets; CFIB (backward) verifies returns via the shadow stack. CFI is a legacy alias setting both. See [Process mitigations catalog](~peios/process-mitigations/catalog).

**Claim.** A typed key-value attribute on a token (user or device claims) or object (resource attributes). Referenced in conditional ACE expressions. See [Claims on a token](~peios/identity/claims).

**Conditional ACE.** An ACE whose grant or deny is gated by a conditional expression in a stack-based bytecode. See [Conditional ACEs](~peios/security-descriptors/conditional-aces).

**Confinement.** The sandbox model that intersects a token's access to the rights its confinement identity (confinement_sid + capabilities) would have been granted. Cannot be bypassed by privileges. See [Confinement](~peios/confinement/overview).

**Confinement_exempt.** A token field that, when set, causes the confinement pass to be skipped entirely. See [The confinement pass](~peios/confinement/the-confinement-pass).

**Continuous audit.** Per-operation auditing configured by `SYSTEM_ALARM*` ACEs. Each operation on the open handle whose required mask overlaps the alarm mask produces a `continuous-audit` event. See [Audit ACEs](~peios/auditing/audit-aces).

**Credential projection.** The one-way derivation of Linux UID/GID/supplementary GIDs from a token's identity. See [Credential projection](~peios/linux-compatibility/credential-projection).

## D

**DACL (Discretionary Access Control List).** The ACL controlling who may access an object. Walked first-writer-wins during AccessCheck. See [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

**DAC neutralization.** The set of mandatory Linux capabilities (CAP_DAC_OVERRIDE, etc.) that every process carries so the kernel's classical DAC checks always defer to the LSM layer. See [DAC neutralization and capabilities](~peios/linux-compatibility/dac-neutralization-and-capabilities).

**Default DACL.** The DACL applied to new objects when the creator does not supply an explicit SD. Stored on the creating token. See [Token lifecycle](~peios/tokens/lifecycle).

**Delegation (impersonation level).** The highest impersonation level. Acts as Impersonation locally and additionally forwards client credentials to remote machines via Kerberos. See [Impersonation levels](~peios/impersonation/impersonation-levels).

**Derived capability.** A capability SID computed from a string name via SHA-256 split into 8 sub-authorities. Lets vendors define their own capabilities without coordination. See [Capabilities and modes](~peios/confinement/capabilities-and-modes).

## E

**Effective token.** The token AccessCheck reads on a thread — the impersonation token if the thread is impersonating, the primary token otherwise. See [Tokens overview](~peios/tokens/overview).

**Eager inheritance.** The Peios inheritance model: a child object's SD is fully computed at creation time. Parent changes do not propagate to existing children. See [Inheritance](~peios/security-descriptors/inheritance).

**Elevation type.** A token field marking it as `Default` (no pair), `Full` (elevated half), or `Limited` (non-elevated half) of a linked pair. See [Elevation and linked tokens](~peios/tokens/elevation).

**eventd.** The userspace audit daemon that drains KMES audit events and persists them.

## F

**FACS (File Access Control Shim).** The kernel layer that applies KACS to files. Implements the handle model — AccessCheck once at open; granted mask cached on the fd. See [File access](~peios/file-access/overview).

**FilterToken.** A token operation that produces a new, more-restricted token by removing privileges, marking groups deny-only, and/or adding restricted SIDs. See [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens).

**First-writer-wins.** The DACL evaluation rule: once a bit is decided by any ACE during the walk, no later ACE can change the decision for that bit. See [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

## G

**GenericMapping.** A per-object-type table that translates generic rights (GENERIC_READ, etc.) to object-specific bits at evaluation time. See [Access mask bits](~peios/constants-and-catalogs/access-mask-bits).

**Granted access mask.** The 32-bit mask of rights that AccessCheck decided the caller has. Cached on FACS-managed file descriptors at open. See [The handle model](~peios/file-access/the-handle-model).

## H

**Handle model.** The FACS rule that AccessCheck runs once at open and the granted mask is cached on the resulting fd; subsequent operations consult the cached mask rather than re-evaluating. See [The handle model](~peios/file-access/the-handle-model).

## I

**Identification (impersonation level).** An impersonation level where the server may inspect the client's identity but not use the token for AccessCheck. Every access check using an Identification-level token returns ACCESS_DENIED. See [Impersonation levels](~peios/impersonation/impersonation-levels).

**Impersonation.** The mechanism by which a thread temporarily acts as another principal by installing a per-thread impersonation token. See [Impersonation](~peios/impersonation/overview).

**Impersonation token.** A token installed on a thread to override the primary token for AccessCheck. Always per-thread. See [Tokens overview](~peios/tokens/overview).

**Inheritance.** The process by which a new object's SD is computed from inheritable ACEs in the parent's SD plus the creator's defaults. Eager — happens at creation, not at access. See [Inheritance](~peios/security-descriptors/inheritance).

**Integrity level.** A numeric trust rank on tokens and objects: Untrusted, Low, Medium, High, System. Used by MIC. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

**Isolation boundary.** A token field reserved for future use; would make out-of-boundary objects invisible rather than just denied. Not enforced in v0.20. See [The confinement pass](~peios/confinement/the-confinement-pass).

## J

**Just-in-time impersonation (JIT).** The recommended pattern for services on M:N runtimes (Go, Rust async, etc.): capture the peer's token fd at request start, install it only at the moment of the access-requiring action, revert immediately. See [Impersonation overview](~peios/impersonation/overview).

## K

**KACS (Kernel Access Control Subsystem).** The kernel-level authorisation engine in Peios. Implemented as the PKM LSM.

**KMES (Kernel Message Event Stream).** The kernel-to-userspace event transport that carries audit events. Best-effort delivery.

## L

**Linked token pair.** Two tokens — Full (elevated) and Limited (non-elevated) — for the same principal, associated through their shared logon session. The UAC-style elevation primitive. See [Elevation and linked tokens](~peios/tokens/elevation).

**Local claims.** Per-AccessCheck-call attributes in the `@Local.*` namespace, supplied by the caller. Available to conditional ACE expressions. See [Claims on a token](~peios/identity/claims).

**Logon session.** A kernel object recording one authentication event. Every token references one via `auth_id`. See [Logon sessions](~peios/logon-sessions/overview).

**Logon SID.** A per-session SID `S-1-5-5-X-Y` derived from the session ID. Carried by every token of the session. See [Logon sessions](~peios/logon-sessions/overview).

**Logon type.** A session's classification — Interactive, Network, Service, Batch, NetworkCleartext, NewCredentials. See [Logon types](~peios/logon-sessions/logon-types).

**LSV (Library Signature Verification).** A process mitigation that refuses to `mmap(PROT_EXEC)` libraries whose signatures don't meet the calling process's PIP trust. See [Process mitigations catalog](~peios/process-mitigations/catalog).

**LUID.** A 64-bit Locally Unique Identifier. Used as session IDs, token IDs, source LUIDs, and privilege bit positions.

## M

**MAC (Mandatory Access Control).** A general class of LSM (SELinux, AppArmor, SMACK, TOMOYO). All MAC LSMs are excluded from Peios's LSM stack. See [Kernel invariants](~peios/boot-and-trust-establishment/kernel-invariants).

**MAXIMUM_ALLOWED.** A bit in a requested access mask (0x02000000) signalling "tell me the maximum rights I could be granted". Not a real right; never appears in ACEs. See [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

**MIC (Mandatory Integrity Control).** The pre-DACL check that compares the token's integrity level against the object's mandatory label. Denies write/read/execute up by default. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

**Mitigation.** A per-process kernel-enforced hardening rule (WXP, LSV, TLP, CFI, PIE, SML, NO_CHILD). One-way; stored on the PSB. See [Process mitigations](~peios/process-mitigations/overview).

**Mount policy.** A per-superblock setting controlling how FACS treats a filesystem. One of `facs_deny_missing`, `facs_synthesize_ephemeral`, `facs_synthesize_persistent`, `unmanaged`. See [Mount policies](~peios/mount-policies/overview).

## N

**NEW_PROCESS_MIN.** A `mandatory_policy` flag that, when set, lowers the token's integrity to match the new binary's mandatory label at exec if the binary's label is lower. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

**NO_CHILD (NO_CHILD_PROCESS).** A mitigation that refuses fork and clone-new-process. Once set, the process cannot create child processes. See [Process mitigations catalog](~peios/process-mitigations/catalog).

**NO_WRITE_UP.** The default MIC policy bit: lower-integrity callers cannot write to higher-integrity objects. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

**NULL DACL.** An SD without `SE_DACL_PRESENT` set. Grants all rights to every caller. Different from an empty DACL (DACL present, zero ACEs — grants nothing). See [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

## O

**Object ACE.** An ACE type extended with a property GUID, enabling per-property access control on directory-style objects. See [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces).

**Object type list.** A caller-supplied tree of GUIDs representing properties being requested. Required for `kacs_access_check_list`. See [Access decisions overview](~peios/access-decisions/overview).

**Owner implicit rights.** The READ_CONTROL and WRITE_DAC rights an SD's owner gets automatically, before the DACL walk. Suppressible via an OWNER RIGHTS (`S-1-3-4`) ACE. See [Ownership and implicit rights](~peios/security-descriptors/ownership).

**OWNER RIGHTS.** The well-known SID `S-1-3-4`. When present in a DACL, it suppresses the owner's implicit rights. See [Ownership and implicit rights](~peios/security-descriptors/ownership).

## P

**peinit.** The Peios PID-1 process — signed at TCB, running with the SYSTEM token, responsible for the rest of userspace boot and as the TCB lifecycle manager. See [peinit at PID 1](~peios/boot-and-trust-establishment/peinit-pid-1).

**PIE (Position-Independent Executable).** A mitigation that refuses to exec non-PIE binaries. Combined with ASLR, randomises the binary's load address. See [Process mitigations catalog](~peios/process-mitigations/catalog).

**PIP (Process Integrity Protection).** The 2D trust model (type + trust level) on processes, set at exec from the binary's signature. Gates cross-process operations. See [Process integrity protection](~peios/process-integrity-protection/overview).

**PIP dominance.** The all-or-nothing comparison: caller dominates target iff `caller.pip_type >= target.pip_type AND caller.pip_trust >= target.pip_trust`. See [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).

**PKM (Peios Kernel Module).** The LSM that implements KACS. The sole authoritative access-decision LSM on a Peios system.

**Positive confinement.** The convention of placing capability SIDs in a token's normal `groups` list (in addition to or instead of `confinement_capabilities`), so the capability acts as a grant via the DACL walk rather than a confinement constraint. Does not bypass confinement. See [Positive confinement](~peios/confinement/positive-confinement).

**Primary token.** A process's baseline identity, inherited at fork, used when threads are not impersonating. See [Tokens overview](~peios/tokens/overview).

**Principal.** A user, group, service, or machine identifiable by a SID. See [Identity](~peios/identity/overview).

**PRINCIPAL_SELF.** The well-known placeholder SID `S-1-5-10`. Substituted with the caller-supplied `self_sid` during AccessCheck. See [Well-known principals](~peios/identity/well-known-principals).

**Privilege.** A system-wide right on a token that gates a specific operation. Orthogonal to group membership. See [Privileges](~peios/privileges/overview).

**Process SD.** The security descriptor on a process, distinct from the SD on its token. Governs operations on the process. See [The process security descriptor](~peios/process-integrity-protection/the-process-security-descriptor).

**Projection.** See **Credential projection**.

**PSB (Process Security Block).** The per-process kernel structure holding PIP fields, mitigation flags, the process SD, and other process-level security state. See [Process integrity protection](~peios/process-integrity-protection/overview).

## R

**Recovery policy.** The hardcoded CAAP fallback applied when a referenced policy SID is missing from the kernel cache. Grants `GENERIC_ALL` to `BUILTIN\Administrators`, SYSTEM, and `OWNER_RIGHTS` only. See [Distribution and recovery](~peios/central-access-policies/distribution-and-recovery).

**Resource attribute.** A typed key-value attribute on an object, stored in a `SYSTEM_RESOURCE_ATTRIBUTE_ACE` in the SACL. Available to conditional ACE expressions as `@Resource.<name>`. See [Resource attributes](~peios/security-descriptors/resource-attributes).

**Restricted token.** A token carrying a secondary `restricted_sids` list. AccessCheck runs twice and intersects. See [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens).

**RESTORE_INTENT.** A flag passed to AccessCheck that activates `SeRestorePrivilege`. See [Intent-gated privileges](~peios/privileges/intent-gated).

## S

**SACL (System Access Control List).** The system half of an SD. Carries audit ACEs, the mandatory integrity label, resource attributes, scoped policy references, and PIP trust labels. Modifying requires `ACCESS_SYSTEM_SECURITY`. See [The SACL](~peios/security-descriptors/the-sacl).

**Security descriptor (SD).** The four-part policy structure (owner, primary group, DACL, SACL) on every protected object. See [Security descriptors](~peios/security-descriptors/overview).

**Self_sid.** The caller-supplied SID that `PRINCIPAL_SELF` resolves to during a specific AccessCheck. Used by directory-style objects where an ACE refers to "the principal this object is about".

**Service SID.** A SID in the `S-1-5-80-*` range derived from a service's name via SHA-1. Used to grant access specifically to a named service. See [Well-known principals](~peios/identity/well-known-principals).

**SID (Security Identifier).** The unique name for a principal. Hierarchical, binary-comparable, 8–68 bytes encoded. See [SIDs](~peios/identity/sids).

**SML (Speculation Mitigation Lock).** A mitigation that enables the strictest set of CPU speculation-execution defences on the process. See [Process mitigations catalog](~peios/process-mitigations/catalog).

**Staged DACL / SACL.** Proposed replacements for the effective DACL / SACL in a CAAP rule, evaluated in parallel during AccessCheck without affecting the granted mask. Used for testing policy changes. See [Staged policies](~peios/central-access-policies/staged-policies).

**Staging mismatch.** A boolean flag in AccessCheck's output indicating that a staged CAAP version would have produced different behaviour than the effective version. See [Staged policies](~peios/central-access-policies/staged-policies).

**Subject record.** The portion of an audit event identifying the calling principal. See [Common records](~peios/audit-event-reference/common-records).

**SYSTEM token.** A kernel-direct singleton token with every privilege enabled, integrity System, attached to init. Session ID 0. See [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens).

## T

**TCB (Trusted Computing Base).** The kernel plus the TCB binaries (peinit, authd, loregd, lpsd, eventd) whose correctness the security model depends on.

**TLP (Trusted Library Paths).** A mitigation that requires `mmap(PROT_EXEC)`'d files to come from one of the approved directory prefixes (configured machine-wide at boot). See [Process mitigations catalog](~peios/process-mitigations/catalog).

**Token.** The per-thread runtime identity object holding the user SID, groups, privileges, integrity level, etc. The input to AccessCheck. See [Tokens overview](~peios/tokens/overview).

**Token fd.** A file descriptor referring to a token. Carries an access mask (TOKEN_*) gating operations on the fd. See [Inspecting tokens](~peios/inspecting/tokens).

**Two-check rule.** The PIP rule: every cross-process operation runs both an SD check (against the target's process SD) and a PIP dominance check. Both must pass. See [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).

**Two-gate model.** The impersonation rule: identity gate (same-user or `SeImpersonatePrivilege`) plus integrity ceiling (capped at server's integrity). Determines the effective impersonation level. See [The two-gate model](~peios/impersonation/the-two-gates).

## U

**uid0.** A userspace utility that cosmetically sets `cred->uid/euid/suid` to 0 for legacy programs that check `getuid() == 0`. Does not change the underlying KACS token. See [setuid and uid0](~peios/linux-compatibility/setuid-and-uid0).

**Unmanaged (mount policy).** A mount policy class meaning FACS does not apply. Used by the kernel for `/proc` and `/sys`. Not settable via the public ABI. See [Policy classes](~peios/mount-policies/policy-classes).

**UNKNOWN.** The third value in conditional ACE three-valued logic. Behaviour depends on context: skips allow ACEs and CAAP rules; fires deny ACEs and audit ACEs. See [Conditional ACEs](~peios/security-descriptors/conditional-aces).

## V

**Virtual group injection.** The pre-DACL step where `OWNER RIGHTS` and `PRINCIPAL_SELF` are injected into the token's effective group list when the caller owns the object or matches `self_sid` respectively. See [Access decisions overview](~peios/access-decisions/overview).

## W

**Well-known SID.** A SID whose value is defined by the system rather than allocated at runtime. See [Well-known principals](~peios/identity/well-known-principals).

**Write-restricted token.** A variant of restricted token where the intersection applies only to write-category rights; reads and execute come from the normal pass. See [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens).

**WXP (Write-XOR-Execute).** A mitigation refusing W→X page transitions and refusing pages mapped writable-and-executable simultaneously. See [Process mitigations catalog](~peios/process-mitigations/catalog).
