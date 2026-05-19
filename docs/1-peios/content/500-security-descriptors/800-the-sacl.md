---
title: The SACL
type: concept
description: The SACL is the system-side half of a security descriptor. It carries audit ACEs, alarm ACEs, the mandatory integrity label, the PIP trust label, scoped policy references, and resource attributes. This page covers what the SACL holds, how each entry is consumed, and why modifying it requires SeSecurityPrivilege.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/resource-attributes
  - peios/auditing/overview
  - peios/access-decisions/overview
  - peios/process-integrity-protection/overview
  - peios/central-access-policies/overview
---

The **SACL** — System Access Control List — is the half of a security descriptor that holds system-level policy. Where the DACL decides "who can do what to this object", the SACL covers everything else the kernel needs to know about the object for security purposes: which access attempts to audit, what integrity level the object has, what PIP trust label it carries, which central access policies apply to it, and what attributes it exposes for conditional evaluation.

The SACL is not part of the access-grant decision in the way the DACL is. Most of its entries do not grant or deny anything; they configure policy that runs alongside or after the DACL walk. The two access-related entries — `SYSTEM_AUDIT` and `SYSTEM_ALARM` — fire events but do not gate access.

This page covers each type of SACL entry, how the access check consumes it, and the special status of SACL modification.

## What the SACL holds

A SACL is an ACL — same on-wire structure as a DACL, the same `AceCount`/`AclSize` header and the same ACE format. But the ACE types it holds are different. While a DACL is dominated by access-control types (`ACCESS_ALLOWED`, `ACCESS_DENIED`, callbacks), a SACL holds the system-policy types:

| ACE type | Value | Purpose |
|---|---|---|
| `SYSTEM_AUDIT` | 0x02 | Fire an audit event when access matches. One-shot at handle creation. |
| `SYSTEM_AUDIT_OBJECT` | 0x07 | Same, GUID-scoped. |
| `SYSTEM_AUDIT_CALLBACK` | 0x0D | Same, with a conditional expression gating when the audit fires. |
| `SYSTEM_AUDIT_CALLBACK_OBJECT` | 0x0F | Same, GUID-scoped and conditional. |
| `SYSTEM_ALARM` | 0x03 | Configure per-operation continuous audit on an open handle. |
| `SYSTEM_ALARM_OBJECT` | 0x08 | Same, GUID-scoped. |
| `SYSTEM_ALARM_CALLBACK` | 0x0E | Same, conditional. |
| `SYSTEM_ALARM_CALLBACK_OBJECT` | 0x10 | Same, GUID-scoped and conditional. |
| `SYSTEM_MANDATORY_LABEL` | 0x11 | The object's mandatory integrity label and policy bits (MIC). |
| `SYSTEM_RESOURCE_ATTRIBUTE` | 0x12 | A typed key-value attribute on the object (covered separately under [Resource attributes](~peios/security-descriptors/resource-attributes)). |
| `SYSTEM_SCOPED_POLICY_ID` | 0x13 | A reference to a central access policy (CAAP). |
| `SYSTEM_PROCESS_TRUST_LABEL` | 0x14 | The object's PIP trust label and the explicit allowed mask for non-dominant callers. |

A SACL can mix these in any combination. Most SACLs in practice are small — a few audit ACEs, perhaps a mandatory label, sometimes a resource attribute or two. SACLs with every type populated are rare and exist only on the most highly-protected objects.

## Audit ACEs: one event per access attempt

A `SYSTEM_AUDIT` ACE specifies: when **this principal** attempts **these rights** on the object, emit an audit event if the access succeeded (`SUCCESSFUL_ACCESS_ACE_FLAG` set) or if it failed (`FAILED_ACCESS_ACE_FLAG` set) or both.

The event fires at the moment the access check completes. One event per matching audit ACE per access attempt. A handle opened with `FILE_READ_DATA | FILE_WRITE_DATA` against an SD with an audit ACE matching both rights produces one event covering both. A separate handle later, with separate access checks, produces separate events.

Audit ACEs match like other ACEs: the SID in the ACE is compared against the caller's identity. Audit ACE matching uses **deny polarity** — it considers the broadest identity view, including deny-only groups, so that any identity the caller has that should produce an audit event will produce one even if it would not match an allow ACE.

The callback variants (`SYSTEM_AUDIT_CALLBACK`, etc.) add a conditional expression. If the expression evaluates TRUE or UNKNOWN, the event fires; if FALSE, it does not. This is why conditional audit fails open — recording something is the safe choice when uncertain.

The full audit model is covered in [Auditing](~peios/auditing/overview).

## Alarm ACEs: an event per operation

`SYSTEM_ALARM` configures **continuous** auditing, not one-shot. The ACE's mask is recorded on the open handle as a **continuous audit mask**. From then on, every operation performed on the handle has its required-access mask compared against the continuous mask; if any bit overlaps, an event fires.

The difference between AUDIT and ALARM is in granularity. AUDIT records "this principal opened this object with these rights". ALARM records "this principal opened this object with these rights, *and then performed this specific operation, then this one, then this one*". The trade-off is event volume — alarm ACEs on a hot path can produce many events; audit ACEs produce one per handle.

ALARM is the right tool for objects where post-open behaviour is what matters: an audited credential store, a sensitive log file, a security-critical configuration. For most objects, AUDIT is enough.

## SYSTEM_MANDATORY_LABEL: the integrity floor

A `SYSTEM_MANDATORY_LABEL` ACE sets the object's mandatory integrity level. The ACE has two parts:

- A **SID** from the `S-1-16-*` integrity namespace (`S-1-16-8192` for Medium, `S-1-16-12288` for High, etc.).
- A **mask** containing the MIC policy bits: `SYSTEM_MANDATORY_LABEL_NO_READ_UP` (0x01), `SYSTEM_MANDATORY_LABEL_NO_WRITE_UP` (0x02), `SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP` (0x04).

When the access check evaluates the SD, it scans for a `SYSTEM_MANDATORY_LABEL` ACE. The first non-inherit-only one is the object's effective label. If none is present, the object's effective integrity is **Medium with `NO_WRITE_UP`** (the default).

A caller whose effective token's integrity level is below the object's label cannot perform the right categories blocked by the policy bits. The check runs *before* the DACL walk. A non-dominant caller's deny is decided before any allow ACE in the DACL has a chance to grant the same right.

The label is independent of identity. Two users at different integrity levels with identical SIDs see the same DACL but different effective access, because the label-vs-token-integrity comparison happens first.

MIC is covered in detail in [Access decisions](~peios/access-decisions/overview).

## SYSTEM_PROCESS_TRUST_LABEL: the PIP gate

A `SYSTEM_PROCESS_TRUST_LABEL` ACE opts the object in to process integrity protection (PIP). The ACE has:

- A **SID** of the form `S-1-19-T-L` where `T` is the PIP type and `L` is the trust level.
- A **mask** specifying the rights that non-dominant callers are explicitly allowed.

PIP enforcement is two-step. First, the access check determines whether the caller's PSB **dominates** the object's trust label — that is, the caller's `pip_type` is at least the ACE's type AND the caller's `pip_trust` is at least the ACE's trust level. If the caller dominates, the trust label imposes no restrictions. If the caller does not dominate, **only** the rights in the ACE's mask are permitted, and privilege-granted rights are revoked (which is what makes PIP different from MIC).

Objects without a PIP trust label ACE are unprotected — PIP is opt-in. The access check does not impose PIP rules unless the SACL specifically asks for them.

PIP is covered in [Process integrity protection](~peios/process-integrity-protection/overview).

## SYSTEM_SCOPED_POLICY_ID: central access policies

A `SYSTEM_SCOPED_POLICY_ID` ACE references a centrally-defined access policy by SID. The policy itself is distributed by authd (from loregd on standalone machines, from Active Directory on domain-joined ones) and held in a kernel cache. When the access check sees this ACE, it looks up the referenced policy and evaluates its rules in addition to the object's own DACL — intersecting the result, never widening.

Multiple `SYSTEM_SCOPED_POLICY_ID` ACEs in one SACL apply multiple policies. The result is the intersection of all of them with the object's DACL.

The mechanism — applies-to expressions, staged vs effective rules, the recovery policy for when a referenced policy is missing — lives in [Central access policies](~peios/central-access-policies/overview). For this page, what matters is that the entry exists, sits in the SACL, and is looked up by SID at access time.

## SYSTEM_RESOURCE_ATTRIBUTE: typed properties on the object

`SYSTEM_RESOURCE_ATTRIBUTE` carries a typed key-value attribute on the object — referenceable as `@Resource.<name>` in conditional expressions on this or any other SD. The structural role is described above; the full story is in [Resource attributes](~peios/security-descriptors/resource-attributes).

## How the SACL is consumed

The access check consults the SACL twice, at different points:

1. **Before the DACL walk**, the check scans the SACL for the MIC, PIP, and scoped-policy ACEs. MIC and PIP pre-decide certain bits as denied for non-dominant callers; scoped policies are noted for later evaluation. Resource attribute ACEs are scanned and indexed so that conditional expressions in the DACL can reference them.
2. **After the DACL walk**, the check scans the SACL again for `SYSTEM_AUDIT` and `SYSTEM_ALARM` ACEs and decides which events to fire. The MIC, PIP, and scoped-policy ACEs are not consulted again here — their job is done.

This two-pass shape is why the SACL is "structural" rather than "evaluated": its job is to set policy *for* the DACL walk and to record audit *about* the DACL walk's outcome, not to participate in the walk itself.

## Modifying the SACL

The DACL is gated by `WRITE_DAC`, which the owner has implicitly. The SACL is gated by `ACCESS_SYSTEM_SECURITY`, which the owner does **not** have implicitly. To modify a SACL, a caller needs:

- Either `SeSecurityPrivilege` (which grants `ACCESS_SYSTEM_SECURITY` on any object), or
- `SeRestorePrivilege` (which grants it for specific `kacs_set_sd` use cases — backup/restore tooling).

`WRITE_DAC` does **not** grant `ACCESS_SYSTEM_SECURITY`. An owner who can rewrite a DACL freely cannot touch the SACL. This is deliberate: the SACL holds audit policy and system-level constraints that the object's owner should not be able to unilaterally remove. An audited object's audit policy is the administrator's, not the user's.

Modifying a SACL that contains a `MANDATORY`-flagged resource attribute is further restricted: removing or changing a mandatory attribute requires `SeTcbPrivilege` (covered under [Resource attributes](~peios/security-descriptors/resource-attributes)).

## The LABEL_SECURITY_INFORMATION shortcut

The `kacs_set_sd` syscall takes a `security_information` bitmask saying which SD components to update. Two of the bits are relevant here:

| Flag | Effect |
|---|---|
| `SACL_SECURITY_INFORMATION` (0x08) | Update the SACL (all of it). Requires `ACCESS_SYSTEM_SECURITY`. |
| `LABEL_SECURITY_INFORMATION` (0x10) | Update **only** the mandatory integrity label ACE within the SACL. |

`LABEL_SECURITY_INFORMATION` is the right tool when you want to change an object's integrity level without touching its audit policy. Setting an integrity label downward (to a level at or below the caller's own integrity level) is allowed; setting it above requires `SeRelabelPrivilege`.

The two flags are mutually exclusive in a single `kacs_set_sd` call. You either replace the entire SACL or update only the label, not both at once.

## What the SACL is not

A few clarifications:

- **The SACL is not for "extra security".** It is the kernel's place for system-level policy. Putting more entries in the SACL does not make an object more secure; it just records more policy.
- **The SACL is not where the DACL goes if you forget the DACL.** The two lists are structurally distinct in the SD format; an SD with a missing DACL but a populated SACL has a NULL DACL (grant all access) regardless of what the SACL says.
- **The SACL is not visible to ordinary users.** Reading the SACL — `kacs_get_sd` with `SACL_SECURITY_INFORMATION` — also requires `ACCESS_SYSTEM_SECURITY`. An owner can read their object's DACL freely but cannot read its SACL without the same privilege required to modify it.
