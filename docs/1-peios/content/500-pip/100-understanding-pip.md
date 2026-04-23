---
title: Understanding Process Integrity Protection (PIP)
type: concept
description: A protection mechanism that shields critical processes and objects even from administrators.
related:
  - peios/integrity/understanding-mic
  - peios/pip/pip-object-protection
  - peios/pip/binary-signing-and-pip
  - peios/process-security/process-mitigations
---

**Process Integrity Protection (PIP)** protects critical processes and their objects from tampering — even by administrators with full privileges.

MIC prevents lower-trust processes from writing to higher-trust objects. But MIC is a single linear hierarchy with administrators near the top. If an attacker compromises an administrative process, MIC offers no resistance — the attacker is already above most objects in the hierarchy.

PIP addresses this by defining a protection model where **administrators are not at the top**. A PIP-protected process cannot be debugged, signaled, or have its memory read by any process that doesn't meet the right protection criteria — regardless of that process's privileges.

## How PIP differs from MIC

| | MIC | PIP |
|---|---|---|
| **Protects** | Objects from lower-trust writers | Processes and their objects from non-dominant processes |
| **Dimensions** | One (integrity level) | Two (type and trust level) |
| **Privileges can bypass** | Yes (SeBackupPrivilege, etc.) | No |
| **Ordering** | Total — every level is comparable | Partial — some levels are incomparable |

The key difference: privileges like `SeDebugPrivilege` and `SeBackupPrivilege` can bypass the DACL and MIC, but they **cannot bypass PIP**. A process needs PIP dominance to access a PIP-protected target, and no privilege substitutes for it.

## The two dimensions

PIP evaluates protection along two independent dimensions:

### Type — how isolated the process is

| Type | Meaning |
|---|---|
| **Isolated** | Maximum isolation. The process's memory, signals, and metadata are inaccessible to anything that isn't also Isolated with sufficient trust |
| **Protected** | Standard protection. Shielded from unprotected processes, but accessible to Isolated processes |
| **None** | No PIP protection. The default for all normal processes |

### Trust level — how trusted the process is within its type

A numeric level where higher means more trusted. Trust level is determined by **who signed the binary** — core Peios components receive higher trust than third-party plugins. The specific assignments are a matter of system policy.

## Dominance

One process can access another only if it **dominates** it. Dominance requires meeting or exceeding the target on **both** dimensions:

```
dominates = (caller.type >= target.type) AND (caller.trust >= target.trust)
```

This creates a **partial order**. Some processes are incomparable — neither dominates the other:

- A Protected process with high trust does **not** dominate an Isolated process with low trust (lower type)
- An Isolated process with low trust does **not** dominate a Protected process with high trust (lower trust)
- Neither can access the other

This is the key property. The authentication service (high trust, needs to be relied upon) and a cryptographic key daemon (maximum isolation, holds secrets) can both be PIP-protected in ways that prevent either from accessing the other. A single linear hierarchy would force one to be ranked above the other — PIP's two dimensions avoid this false tradeoff.

## What PIP protects

**Processes.** A non-dominant process cannot:
- Attach a debugger or read process memory
- Send signals (including termination)
- Read process metadata from `/proc`

Process protection is binary — if you dominate, you have full access. If you don't, you have none. There is no "you can signal but not debug" granularity, because partial process access is not a meaningful security boundary.

**Objects.** PIP-protected objects carry a trust label ACE in their SACL. AccessCheck evaluates the caller's PIP level against the trust label. A non-dominant process is denied access regardless of the DACL and regardless of privileges.

## Why privileges cannot bypass PIP

This is deliberate. PIP exists precisely for scenarios where the attacker has administrative privileges. If `SeDebugPrivilege` could bypass PIP, then a compromised administrator could debug the authentication service and extract tokens. If `SeBackupPrivilege` could bypass PIP trust labels, a compromised administrator could read the key daemon's private keys.

A process needs both the relevant privilege (to satisfy the DACL) **and** PIP dominance (to satisfy the trust boundary). One without the other grants nothing.

## How PIP level is determined

A process's PIP level is set at `exec` time based on the **cryptographic signature of the binary**. Core Peios binaries signed with the system signing key receive high trust. Third-party signed binaries receive lower trust. Unsigned binaries receive no PIP protection.

This means PIP protection is tied to what code is running, not who is running it. An administrator running an unsigned binary gets no PIP protection — the binary determines the level, not the token.
