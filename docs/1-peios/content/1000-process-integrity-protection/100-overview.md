---
title: Process integrity protection
type: concept
description: PIP is the layer of access control that gates operations between processes based on the trust level of their binaries, not the identity of their callers. Each process carries a two-dimensional trust label set by the kernel at exec from the binary's signature. The label is what decides who can signal, inspect, or interfere with the process.
related:
  - peios/process-integrity-protection/the-process-security-descriptor
  - peios/process-integrity-protection/the-two-check-rule
  - peios/process-integrity-protection/pip-in-practice
  - peios/binary-signing/overview
  - peios/tokens/overview
---

**Process integrity protection** — PIP — is the access-control layer that gates one process's ability to operate on another. Where the DACL and tokens decide "is this principal allowed?", PIP decides "is the calling binary trusted enough?". A PIP-protected process — peinit, authd, the kernel's own helpers — cannot be debugged, signalled, suspended, or read from by code running at lower trust. Even root cannot.

The protection is rooted in the binary's signature. At exec, the kernel verifies the new program against its public-key catalogue and assigns the resulting process a two-dimensional trust label — `pip_type` and `pip_trust` — that records what kind of trust the binary established and at what level. From then on, every cross-process operation against this process compares the caller's label to this one.

This is **not** the same axis as identity. Two processes running as the same user can have different PIP labels because they are running different binaries. A user-mode process and a TCB daemon running as SYSTEM are at different PIP levels; the user-mode process cannot interfere with the daemon even though both run as the same principal. The barrier is not who, it is what.

## Where PIP lives

Each process has a **Process Security Block** — the PSB — attached by the kernel. The PSB carries:

| Field | Meaning |
|---|---|
| `pip_type` | The PIP type. One of None, Protected, Isolated. |
| `pip_trust` | The PIP trust level. A numeric tier within the type. |
| `security_descriptor` | The process SD — see [The process security descriptor](~peios/process-integrity-protection/the-process-security-descriptor). |
| Mitigation flags | The process's enabled security mitigations — see [Process mitigations](~peios/process-mitigations/overview). |
| `no_child_process` | Whether the process is allowed to fork. |

The PSB is **not** the token. The token says who the process is acting as; the PSB says what kind of process it is. The two have different lifecycles, different fields, and are read by different parts of the access pipeline. A thread impersonating a user changes its effective token but not its process's PSB. The PSB is fixed once the binary execs.

## The 2D trust model

PIP's trust is encoded as two numbers, deliberately not collapsed into a single ordering:

| Axis | Range | What it means |
|---|---|---|
| `pip_type` | 0 (None), 512 (Protected), 1024 (Isolated) | The *kind* of trust. None = unprotected; Protected = the standard PIP-protected process; Isolated = reserved for future use. |
| `pip_trust` | numeric (0, 1024, 1536, 2048, 4096, 8192 in v0.20) | The *tier* of trust within a type. Higher numbers are more trusted within the same type. |

The 2D model exists because trust is not a single line. A signed application from a third-party developer is trusted *for what it is* — its publisher attested to it — but is not at the same trust as a Peios TCB binary that has been signed by the OS itself. They have different *types* of trust, and within each type, there can be tiers.

In v0.20 the catalogue is small:

| SID | type | trust | What it represents |
|---|---|---|---|
| `S-1-19-0-0` | None (0) | 0 | Unprotected. Default for unsigned processes. |
| `S-1-19-512-1024` | Protected (512) | 1024 | Authenticode-style third-party signed. |
| `S-1-19-512-1536` | Protected (512) | 1536 | Antimalware tooling. |
| `S-1-19-512-2048` | Protected (512) | 2048 | Peios-distributed applications. |
| `S-1-19-512-4096` | Protected (512) | 4096 | Core Peios components. |
| `S-1-19-512-8192` | Protected (512) | 8192 | Peios TCB (peinit, authd, loregd, lpsd, eventd). |
| `S-1-19-1024-8192` | Isolated (1024) | 8192 | Reserved — no v0.20 signing key targets this type. |

The Isolated type exists for a future where some processes need to be protected from even the rest of the TCB. In v0.20 it is documented for forward compatibility; no binary will receive this type.

Most processes on a running system have `pip_type = None`. PIP protection is opt-in via signing — most user-mode applications run unsigned and unprotected. The PIP-protected processes are the kernel's specifically-signed daemons.

## How PIP gets assigned

The kernel sets `pip_type` and `pip_trust` at exec time and never changes them afterwards:

1. The kernel reads the binary about to be exec'd.
2. It looks for a signature — an ELF `.peios.sig` section or a `security.peios.sig` xattr.
3. It verifies the signature against its compiled-in public key catalogue.
4. On a valid signature, the PIP fields are set to whatever level the catalogue says the signing key represents.
5. On no signature, invalid signature, or any verification failure, `pip_type` is set to None (0) and `pip_trust` to 0. The exec **still succeeds** — bad signatures do not block execution, they only fail to grant PIP protection.

Once exec completes, the fields are immutable for the lifetime of that process. fork() inherits the parent's PIP fields. exec() recomputes them from the new binary.

The signing and verification mechanics — what the signature format is, how the catalogue works, why bad signatures do not block exec — are in [Binary signing](~peios/binary-signing/overview).

## What PIP gates

PIP fires on every cross-process operation that requires the caller to inspect or affect another process:

- Signals (kill, signal delivery).
- ptrace and its kin (memory read/write, attach, single-step).
- pidfd_open, pidfd_getfd, pidfd_send_signal.
- Reading or writing `/proc/<pid>/*` for processes other than oneself.
- Opening another process's tokens (`kacs_open_process_token`, `kacs_open_thread_token`).
- Setting process attributes (priority, affinity, rlimits).
- Profiling another process (`perf_event_open`).

In every case, the kernel runs the **two-check rule**: the calling process must pass both an SD check (the target's process SD must grant the requested right to the caller's token) **and** a PIP dominance check (the caller's PIP label must dominate the target's). Both must succeed. Neither alone is enough.

The full mechanism is in [The two-check rule](~peios/process-integrity-protection/the-two-check-rule). What matters for the overview: PIP does not replace identity-based access control, it sits *alongside* it. A PIP-protected process can still be administered by an SD that grants the rights; the SD just is not the whole story.

## What PIP does *not* do

A few clarifications that come up:

- **PIP is not encryption.** A PIP-protected process's memory is in plaintext. The kernel does not encrypt it or seal it; it just refuses ordinary access channels to it. A compromised kernel or a hardware-DMA attack bypasses PIP entirely.
- **PIP is not capability isolation.** Two PIP-protected processes at the same level can interfere with each other freely. The level is the boundary, not the identity.
- **PIP is not a sandbox.** A PIP-protected process is not contained — it is *protected from* containment-bypassing code. PIP protects high-trust processes from low-trust ones, not the other way around.
- **PIP is not user-configurable.** There is no API to upgrade a process's PIP level at runtime. The signature catalogue is in the kernel; only re-execing a different binary changes the level.
- **PIP does not require the binary to be running as a particular user.** A user-mode app run by an administrator and signed at TCB level would still be a TCB-level process from PIP's perspective. The signature is what matters, not who started it.

The cleanest mental model: PIP is "what kind of program is this, and who is allowed to mess with it?". The token is "who is this program acting as, and what can they reach?". Each answers a different question. Both run.

## Where to start

If you want the process SD specifically — the SD that lives on the PSB and gates operations on the process — read [The process security descriptor](~peios/process-integrity-protection/the-process-security-descriptor).

If you want the dominance comparison and the two-check rule — the rule that every cross-process operation runs both an SD check and a PIP dominance check — read [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).

If you want the edge cases — how PIP interacts with impersonation, how it differs from MIC, why peinit ends up being the lifecycle manager for PIP-protected processes, and what the model does not cover — read [PIP in practice](~peios/process-integrity-protection/pip-in-practice).
