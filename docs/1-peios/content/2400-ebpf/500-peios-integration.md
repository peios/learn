---
title: Peios Integration
type: concept
description: How BPF programs interact with Peios-native kernel primitives — KACS attach points, Peios helpers and kfuncs, KMES filtering, and the ABI tiering.
related:
  - peios/ebpf/overview-and-design
  - peios/ebpf/program-types-and-attach-points
  - peios/ebpf/privileges-and-trust
  - peios/auditing
  - peios/access-control
---

Peios's first-class commitment to eBPF means more than running unmodified Linux BPF programs — it means BPF programs can interact with **Peios-native kernel primitives** through dedicated helpers, kfuncs, and attach points. This page describes that integration surface.

The integration is **additive**. The Linux BPF subsystem (Linux helpers, Linux attach points, BPF LSM) ships intact. Peios extensions sit alongside, exposed under `bpf_kacs_*` / `bpf_lcs_*` / `bpf_kmes_*` / `bpf_process_*` namespaces and KACS-native attach points. Programs that use only Linux helpers remain portable; programs that use Peios helpers commit to Peios.

## KACS attach points

Peios access decisions go through KACS — token-based AccessCheck against a security descriptor (SD). For programmable policy at the access-decision layer, Peios exposes KACS-native attach points:

| Attach point | When it runs | What it can do |
|---|---|---|
| **`kacs_access_check_pre`** | Before the kernel evaluates an AccessCheck | Observe the request; deny it before evaluation |
| **`kacs_access_check_post`** | After AccessCheck completes, before the result is returned | Observe the result; emit audit; veto an allow |
| **`kacs_privilege_check`** | When a privilege check is performed | Observe principal and privilege; deny |
| **`kacs_token_create`** | When a new token is constructed | Observe new token construction |

These complement (do not replace) Linux's BPF LSM. BPF LSM programs see Linux-shaped state (file modes, UIDs); KACS-attached programs see Peios state (effective token, requested access mask, target SD, GUIDs).

The KACS attach points are gated by `SeLoadDriverPrivilege`. Attach operations emit audit events. The exact attach-point ABI is documented in `psd-004--kacs` (future spec extension); the surface described here is the design intent for v1+.

## Peios-native helpers and kfuncs

### Identity helpers (`bpf_process_*`)

Linux helpers like `bpf_get_current_uid_gid` return UIDs/GIDs, which **have no security meaning on Peios** — UIDs are projection IDs, not principals. Peios provides identity helpers that return the authoritative GUIDs:

| Helper | Returns |
|---|---|
| `bpf_get_current_process_guid` | The calling task's `process_guid` |
| `bpf_get_current_token_guid` | The calling task's effective token GUID |
| `bpf_get_current_primary_token_guid` | The calling task's primary (process) token GUID, regardless of impersonation |
| `bpf_get_current_session_guid` | The calling task's logon session GUID |

Programs that need to make security-relevant decisions on Peios MUST use the GUID-based helpers; the UID/GID helpers are a Linux-compat surface and must not be used as security inputs. See [Linux compatibility](../linux-compatibility) for the projection-ID rationale.

### KACS helpers (`bpf_kacs_*`)

| Helper | Purpose |
|---|---|
| `bpf_kacs_access_check` | Run AccessCheck against a target SD with a requested access mask, using a specified token |
| `bpf_kacs_privilege_check` | Check whether a token holds a privilege |
| `bpf_kacs_token_get_owner` | Retrieve a token's owner SID |
| `bpf_kacs_sd_get_owner` / `bpf_kacs_sd_get_group` / `bpf_kacs_sd_get_dacl` / `bpf_kacs_sd_get_sacl` | Inspect an SD's components |

These let BPF programs participate in Peios access control programmatically.

### LCS helpers (`bpf_lcs_*`)

| Helper | Purpose |
|---|---|
| `bpf_lcs_get_value` | Read a registry value by path |
| `bpf_lcs_get_key_sd` | Retrieve a registry key's security descriptor |
| `bpf_lcs_value_exists` | Check value existence without reading |

Used for programs that key behaviour off operator-tunable registry config without burning bytecode space on hardcoded values.

### KMES helpers (`bpf_kmes_*`)

| Helper | Purpose |
|---|---|
| `bpf_kmes_emit` | Emit a Peios-native event with the program's identity stamps and the appropriate `origin_class` |
| `bpf_kmes_emit_audit` | Emit an audit-class event (gated — only programs attached at KACS audit hooks may emit audit-class) |

This is the BPF-side counterpart to Linux's `bpf_audit_log()`. Programs use `bpf_kmes_emit` to surface observations to eventd; audit-class emission is restricted to ensure programs cannot fabricate KACS-authoritative audit records.

## KMES filtering

KMES has no kernel-side filter today — events flow into per-CPU ring buffers and userspace eventd drains them. For high-volume sources, kernel-side filtering is orders of magnitude more efficient than discarding events in userspace.

Peios's design intent is a **two-tier KMES filter model**:

1. **Declarative filters** — registry-driven expressions ("drop events of type `process.exec` where `field.path` matches `/usr/bin/innocuous`"). Cheap, federable via GPO, observable as registry config. Covers common cases.
2. **BPF filters** — full programmable filter at the KMES emit attach point, gated on `SeLoadDriverPrivilege`. Programs see the event header and payload, return keep/drop/sample.

Both run before the ring-buffer write. The declarative tier preserves an **audit-class bypass invariant** — events flagged as audit-class by the emitting subsystem (KACS, signing-policy changes, etc.) are never dropped by declarative filters. The BPF tier can technically drop audit (the privilege gate on attach is the protection), but the audit log of the BPF attach itself is the visibility-of-intent guarantee. See [Privileges and trust](privileges-and-trust) for the threat model.

The KMES filter design is captured here as design intent; the implementation is a future spec extension (`psd-003--kmes` v0.23+).

## ABI tiering

Peios-native helpers and kfuncs have an **ABI commitment** matching the broader Peios kernel ABI distinction:

| Tier | Promise | Examples |
|---|---|---|
| **Stable** | Function signature is committed; deprecation requires a version bump and a transition period | `bpf_kacs_access_check` (once stabilized), GUID identity helpers |
| **Experimental** | Signature may change between kernel versions; programs using these must be recompiled | New helpers as they're being designed |

This mirrors the stable/experimental split for symbol exports in [kernel modules](../kernel-modules/dependencies-and-metadata) — the license-based GPL gate is a Linux-historical artifact that Peios does not perpetuate for its own surface.

## Linux helpers and Peios

Linux BPF helpers ship intact; Peios does not remove them. But for security-relevant decisions, programs should prefer Peios-native helpers because:

- Linux UID/GID helpers return projection IDs, not principals.
- Linux LSM hook arguments are file modes and UIDs, not Peios SDs.
- Linux audit log helpers write to Linux's auditd, which is observational on Peios; KACS audit (via KMES) is authoritative.

Programs targeting Peios should treat Linux helpers as a compatibility tier — use them when porting Linux tools, prefer Peios-native helpers for new policy.

## See also

- [Privileges and trust](privileges-and-trust) — gating and audit for BPF attach operations.
- [Auditing](../auditing) — KACS audit and KMES origin classes.
- [Access control](../access-control) — KACS AccessCheck semantics.
- [Linux compatibility](../linux-compatibility) — UID/GID projection and why Linux identity helpers are not security inputs.
