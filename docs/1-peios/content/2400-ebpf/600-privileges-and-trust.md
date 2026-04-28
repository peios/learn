---
title: Privileges and Trust
type: concept
description: The privilege model gating BPF program loading and attachment, signing, the bpffs filesystem, BPF tokens, audit posture, and the deferred federation story.
related:
  - peios/ebpf/overview-and-design
  - peios/privileges/load-driver
  - peios/auditing
  - peios/kernel-modules/signing-and-trust
---

eBPF's safety model rests on the verifier (which proves runtime safety properties) and the **privilege model** (which gates who can load and attach programs in the first place). The verifier is a defense against bugs and limited-blast-radius mistakes; the privilege gate is the defense against an actor with intent.

## The two-privilege model

Peios collapses BPF privilege into two privileges, sized to blast radius:

| Privilege | Gates | Blast radius |
|---|---|---|
| **`SeLoadDriverPrivilege`** | BPF program loading and attachment for tracing, networking, policy (BPF LSM, KACS attach), KMES filtering, struct_ops (non-scheduler), and all map operations | Kernel code injection — same tier as kernel module loading |
| **`SeLoadSchedulerPrivilege`** | `sched_ext` program loading and attachment | Whole-system scheduling correctness — bugs can deadlock the system |

Linux exposes more granular capabilities (`CAP_BPF` for general BPF, `CAP_PERFMON` for tracing, `CAP_NET_ADMIN` for networking, `CAP_SYS_ADMIN` for the rest). Peios maps these onto the two privileges above. The reasoning: once an actor has any tier of BPF attach, they can read kernel memory via tracing kfuncs, leak credentials, and DoS the box. Per-attach-point granularity adds privilege-management complexity without proportional security benefit. The exception is `sched_ext`, whose blast radius is qualitatively different.

`SeLoadDriverPrivilege` is granted to `Administrators` and `LocalSystem` by default, with the same posture as kernel module loading. `SeLoadSchedulerPrivilege` is granted to `LocalSystem` only by default; administrators may grant it to specific service principals through the standard privilege-grant mechanism.

## Linux capability mapping

Peios continues to honour the Linux capability ABI for compatibility — programs that check `CAP_BPF` see the result of mapping from the Peios privilege state. The mapping:

| Linux capability | Peios mapping |
|---|---|
| `CAP_BPF` | Granted iff `SeLoadDriverPrivilege` is held |
| `CAP_PERFMON` | Granted iff `SeLoadDriverPrivilege` is held |
| `CAP_NET_ADMIN` (for BPF networking) | Granted iff `SeLoadDriverPrivilege` is held |
| `CAP_SYS_ADMIN` (for BPF) | Granted iff `SeLoadDriverPrivilege` is held |

`SeLoadSchedulerPrivilege` does not have a Linux capability counterpart — it gates a Peios-specific privilege. `sched_ext` attempts that pass Linux capability checks but fail the Peios privilege check are rejected with `EPERM`.

## Unprivileged BPF

Linux allows certain BPF operations (specifically, classic `SOCK_FILTER` setsockopt) without privilege; this is the historical origin of BPF and predates the verifier's modern guarantees. Whether broader unprivileged BPF is allowed is gated by `kernel.unprivileged_bpf_disabled`:

- `0` — unprivileged BPF allowed (legacy)
- `1` — unprivileged BPF disabled (programs require privilege)
- `2` — unprivileged BPF disabled and the setting cannot be cleared at runtime

Standard Peios server builds set this to **`2`** by default. The general-purpose BPF surface is privileged-only; legacy `SOCK_FILTER` continues to work because it predates the relevant verifier extensions and has independent justification.

## bpffs

The BPF filesystem (`bpffs`) is mounted at `/sys/fs/bpf/` and provides a path-based namespace for **pinned** BPF objects (programs and maps that outlive the process that loaded them). Pinning is how a daemon makes its programs survive its restart.

bpffs uses standard Peios FACS handle semantics — pinned objects have a security descriptor inherited from the directory, and access is gated by the SD. Default DACLs:

- `/sys/fs/bpf/` — `LocalSystem` and `Administrators`: full; others: read for the directory listing only
- Pinned objects — inherited from parent directory unless overridden

Pinning a program does not bypass `SeLoadDriverPrivilege` — the privilege check happens at load time, before pinning is even possible.

## BPF tokens

As of kernel 6.9, **BPF tokens** allow privileged processes to delegate a subset of BPF capabilities to less-privileged processes through a per-token policy. A privileged process creates a token (`BPF_TOKEN_CREATE`), passes it to an unprivileged process, and the unprivileged process can perform BPF operations within the token's scope.

On Peios, BPF token creation is itself gated by `SeLoadDriverPrivilege`. The token's policy is a subset of what the creating principal could have done directly. This is useful for, e.g., a BPF supervisor service that holds the privilege and delegates limited program-load capability to specific subordinate services.

## BPF program signing

As of kernel 6.18, BPF programs can be cryptographically signed and the kernel can verify signatures at load. Standard Peios server builds enforce **signed BPF programs** for production-tier programs, mirroring the kernel module signing posture:

- **Build floor**: `CONFIG_PEIOS_BPF_SIG_FLOOR={enforce|warn|permissive}` set at kernel build. Standard server builds default to `warn` (matching module signing default).
- **Runtime knob**: `\System\BPF\SigningPolicy` raises strictness above the floor; cannot lower below it.
- **One-way ratchet**: Once `enforce`, stays `enforce` until reboot. Same semantics as module signing.
- **Trust roots**: BPF programs are verified against the same keyring set as kernel modules (`.builtin_trusted_keys`, `.secondary_trusted_keys`, MOK if Secure Boot is on). See [Module signing and trust](../kernel-modules/signing-and-trust).

Programs signed by a trusted key load even under `enforce`; unsigned programs taint the kernel under `warn` and are rejected under `enforce`. The `SigningPolicy` key is a candidate for Superlock protection.

## Audit posture

Every BPF program load and attachment emits a security event:

| Event | When | Always-on? |
|---|---|---|
| `bpf.program.load` | After verification, before the program fd is returned | Always-on under `enforce` policy; default-on otherwise |
| `bpf.program.attach` | When `BPF_PROG_ATTACH` or `BPF_LINK_CREATE` completes successfully | Always-on |
| `bpf.program.detach` | When a program is detached or its link closed | Default-on |
| `bpf.program.load_rejected` | When verification fails or signature is invalid | Always-on |

Each event includes the loading principal (effective token GUID), program type, attach point (where applicable), program identifier (BTF hash if available), and signature status. This is the visibility-of-intent guarantee — a program cannot be attached "quietly" even by a privileged principal.

There is **no audit-class bypass invariant for filtered events** within BPF programs. The privilege gate plus the audit-the-attach event are the protection model. Once an operator has `SeLoadDriverPrivilege`, they can attach programs that filter out subsequent audit events; the act of attaching is itself logged, and the operator's deliberate disable of audit-class filtering is visible through the attach audit trail. See [Peios integration](peios-integration) for the KMES filter design's two-tier model.

## Distribution and federation

BPF programs are deployable artifacts — bytecode plus metadata. v1 ships **operator-loads-locally**: a privileged principal loads programs through `bpf()` (or via standard tools like `bpftool`) on the local machine.

Domain-managed BPF program distribution — pushing programs to all machines in a domain through Group Policy — is **deferred to post-v1**. The eventual mechanism is expected to share infrastructure with kernel updates, livepatch, and module distribution: a signed-artifact format, a GPO-pushable enrollment, and a per-machine apply-on-reboot or apply-immediately model. This is a federation question, not a kernel question, and it can be added without redesigning the BPF subsystem.

## See also

- [Overview and design](overview-and-design) — the design posture for eBPF as a Peios extension mechanism.
- [SeLoadDriverPrivilege](../privileges/load-driver) — privilege details.
- [Peios integration](peios-integration) — the helpers and attach points the privilege gates access to.
- [Module signing and trust](../kernel-modules/signing-and-trust) — the signing infrastructure shared with BPF program signing.
- [Auditing](../auditing) — KMES origin classes and the audit pipeline.
