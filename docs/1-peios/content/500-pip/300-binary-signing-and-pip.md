---
title: How Binary Signing Determines PIP Level
type: concept
description: How a process's PIP level is determined by its binary's cryptographic signature, not its token or user identity.
---

A process's PIP level is not determined by its token or its user. It is determined by the **cryptographic signature on the binary** that the process is running. PIP trust is about what code is executing, not who asked it to execute.

## Set at exec time

When a process calls `exec` to run a binary, the kernel verifies the binary's signature and assigns a PIP type and trust level based on the signer:

| Signer | PIP type | Trust level | Example |
|---|---|---|---|
| Peios system signing key | Isolated or Protected | Highest | peinit, authd, loregd |
| Peios component signing key | Protected | High | Core system services |
| Third-party signing key | Protected | Lower | Signed third-party services |
| Unsigned | None | None | User applications, scripts |

The specific type and trust level assignments are a matter of system policy — the signing key hierarchy determines the mapping.

## Immutable at runtime

Once set at exec time, a process's PIP level **cannot change**. The process cannot raise its own PIP level, and no privilege allows it. The only way to get a different PIP level is to exec a different binary with a different signature.

This immutability is a security property. If a PIP-protected process is somehow tricked into executing attacker-controlled code (via a vulnerability), the code runs within the existing process and retains the existing PIP level — but it cannot spawn a new PIP-protected process without a signed binary.

## Why signing, not identity

Tying PIP to binary signatures rather than token identity prevents a critical attack: an administrator running a compromised tool.

If PIP were based on the token, an administrator's processes would always receive high PIP trust — including malware running in the administrator's session. By tying PIP to the binary signature, a compromised unsigned tool running as an administrator gets **no PIP protection** and cannot access PIP-protected processes or objects.

The administrator's identity (their token) determines what the DACL grants them. The binary's signature determines what PIP trust they carry. These are independent checks — both must pass for access to PIP-protected resources.

## The signing chain

Binary signatures are verified against a chain of trust rooted in keys embedded in the kernel at build time. This means:

- The trust anchor is the built kernel image itself
- Signing keys cannot be added at runtime without kernel modification
- A compromised userspace process cannot forge signatures or introduce new trusted signers

This is the same trust model used for kernel module signing — extended to userspace binaries that need PIP protection.
