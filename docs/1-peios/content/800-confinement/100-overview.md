---
title: Confinement
type: concept
description: Confinement is the sandbox model in Peios — a policy applied to an application from outside that narrows what its token can reach, even past what privileges would normally bypass. This page covers what confinement is, who it is for, and how it differs from the restricted-token model.
related:
  - peios/confinement/capabilities-and-modes
  - peios/confinement/the-confinement-pass
  - peios/confinement/positive-confinement
  - peios/tokens/restricted-tokens
  - peios/tokens/token-types
  - peios/access-decisions/narrowing-layers
---

**Confinement** is the sandbox model in Peios. A confined application is one whose token carries a confinement identity — a single SID identifying which package or sandbox the application belongs to — and an enumerated list of capability SIDs naming what the sandbox is allowed to reach. The kernel enforces this confinement *whether or not the code knows about it*: the application cannot opt out, cannot disable it, cannot exercise a privilege to escape it.

Confinement is the answer to a specific question: how do you run code you do not fully trust on a system whose other resources you do trust? The answer is to give the code a token with a confinement identity and capabilities that name only what it should reach. The kernel then performs an absolute intersection: even if the code somehow obtains broader access through normal means, the confinement layer strips it back to what the capabilities permit.

## Who confinement is for

Confinement is administratively applied. A sysadmin deploys a service or installs an application under a confinement policy — the service definition declares the confinement SID and capabilities; the kernel enforces them. The confined code does not write the policy and cannot read it back to change it. From the application's perspective, confinement is just "the kernel will not let me reach X".

This is the key difference from [restricted tokens](~peios/tokens/restricted-tokens). Restricted tokens are *self-imposed* — a program calls FilterToken to narrow its own authority before launching a sensitive operation. Confinement is *externally imposed* — the policy was decided before the application started and cannot be modified by the application.

The two coexist. A confined service can also internally restrict its own tokens for specific worker threads. The kernel applies both layers independently.

## The three fields on the token

Confinement state lives in three fields on the token:

| Field | Meaning |
|---|---|
| `confinement_sid` | The package or sandbox identity. If null, the token is not confined and the confinement pass is a no-op. If non-null, the token is confined and the kernel will enforce. |
| `confinement_capabilities` | An array of capability SIDs declaring what the confined application is allowed to reach. Used during the confinement intersection — entries here are the SIDs that match ACEs on objects the confined application is permitted to touch. |
| `confinement_exempt` | A boolean escape hatch. When true, the confinement pass is skipped entirely. Set very rarely, only for code that legitimately needs to step outside its own confinement (a confined application's privileged helper, in some narrow patterns). |

All three are **set at token creation** and cannot be changed at runtime. authd is responsible for putting the right values on a confined application's token; once the token is minted, the fields are immutable.

There is one rule the kernel checks at token creation: a confined token (one with a non-null `confinement_sid`) **must not** carry `ALL_APPLICATION_PACKAGES` (`S-1-15-2-1`) as one of its `confinement_capabilities`. The well-known SID would defeat the model — it matches every confined application, so granting it to one would be equivalent to no confinement at all. Tokens that violate this rule are rejected at creation.

## The model in one paragraph

A confined token's effective access is the **intersection** of:
1. What the DACL plus privileges would grant the token's full identity.
2. What the DACL would grant a "fresh" caller whose entire identity is the confinement SID plus the declared capability SIDs.

In other words: the confined application has whatever rights its real identity has, *and* its confinement identity has, on every object it touches. If either side is missing, the right is dropped. The confinement layer is what makes the second condition real — without it, the token's full identity would be all that the access check considered.

The full mechanics of the intersection — when it fires, what it intersects against, what bypasses and what does not — are in [The confinement pass](~peios/confinement/the-confinement-pass). The capability matching specifically (how the SIDs in `confinement_capabilities` are compared against ACEs in DACLs) is in [Capabilities and modes](~peios/confinement/capabilities-and-modes).

## Why privileges do not bypass confinement

The thing that makes confinement different from every other narrowing layer is its treatment of privileges. Restricted tokens preserve privilege-granted bits through the intersection. Confinement does not. A confined token with `SeBackupPrivilege` enabled and `BACKUP_INTENT` set still has its read access narrowed by the confinement intersection — the privilege grant survives steps 4 and 9 of the pipeline, then gets stripped at step 11.

The reason is the audience. A program that restricts itself is trusted to use privileges responsibly — it knows what it is doing because it wrote the restriction. A confined application is not trusted in the same way; the confinement policy came from outside, and a privilege that bypassed it would be an escape hatch for the confined code.

Confinement says: this code may run as whoever, with whatever privileges authd granted, but it cannot reach beyond the capabilities the administrator declared. Privileges are not the lever for breaking out.

## What confinement is *not*

A few things worth clarifying:

- **Confinement is not a privilege-removal mechanism.** A confined token can still carry privileges. The privileges fire normally in their kernel-standalone uses (a confined application with `SeShutdown` can shut down the system if nothing else gates the call). What confinement narrows is **AccessCheck-influencing privileges** specifically — the ones that grant bits via AccessCheck. The non-AccessCheck privileges work as usual.
- **Confinement is not a process-level firewall.** It is a token-level intersection that runs during AccessCheck. It does not block network calls, ptrace, signals, or any other kernel surface that does not go through AccessCheck. Other layers (PIP, the process SD, kernel-standalone privilege checks) handle those.
- **Confinement is not container isolation.** It runs alongside the application's normal access surface, not inside a separate namespace. A confined application sees the same filesystem, the same registry, the same processes as everyone else — it just cannot exercise rights to most of them. Container-style namespace isolation is a separate concern.
- **Confinement is not opt-in for the code.** The code does not call a "please confine me" syscall. The token arrives confined; the kernel enforces.

## When to use confinement vs other layers

A quick map of when each narrowing layer is the right tool:

| Want this | Use this |
|---|---|
| A long-running service to run with less authority than its account would imply, set by administrative policy | **Confinement** |
| A program to internally drop authority for a specific sensitive operation, set by code | **Restricted token** |
| Centrally-defined organisational policy applied across many objects | **CAAP** |
| Prevent untrusted binaries from interfering with trusted ones | **PIP** |
| Block writes from lower-integrity to higher-integrity | **MIC** |

Confinement is for *applications and services* that need to be sandboxed by administrative decision. The capability model — "this application can reach the network, but not the filesystem outside its own data" — is what confinement expresses well.

## Where to start

If you want the capability model — how confinement capabilities match ACEs, the well-known and derived capability SIDs, and the difference between normal and strict modes — read [Capabilities and modes](~peios/confinement/capabilities-and-modes).

If you want the mechanics of the confinement intersection — when it fires in the access pipeline, what does and does not bypass it, the role of `confinement_exempt`, and the isolation-boundary reservation — read [The confinement pass](~peios/confinement/the-confinement-pass).

If you want to understand the canonical Peios pattern for managing service access at scale — putting capability SIDs into a token's normal groups rather than (or in addition to) `confinement_capabilities` — read [Positive confinement](~peios/confinement/positive-confinement). The pattern is what most non-trivial deployments use, and the name is more misleading than the concept itself.
