---
title: The PIP Contract
description: What a verified signature confers — a PIP type and trust level — how dominance is decided, and what may and may not be relied on.
---

A verified signature confers a **PIP identity**: a `pip_type` and a
`pip_trust`, both 32-bit unsigned integers, taken from the key that
verified. An unsigned, unverifiable or unrecognised binary confers
type 0 and trust 0, which means no protection.

This chapter states what that identity means to a party outside the
kernel — what a signer is asserting by obtaining one, what an object
owner is asserting by labelling an object, and what may and may not be
relied upon.

## Dominance

All PIP enforcement reduces to one comparison:

```
dominates(caller, target):
    if target.pip_type == 0:
        return true
    return caller.pip_type  >= target.pip_type
       and caller.pip_trust >= target.pip_trust
```

Both axes are compared numerically. Neither is a closed enumeration:
a value carries no meaning beyond its ordering.

Three type values are conventional — 0 for None, 512 for Protected,
1024 for Isolated — but a specification MUST NOT assume they are the
only ones, and a party evaluating dominance MUST compare numerically
rather than switching on known values.

An unprotected target is dominated by everyone. This is what keeps
ordinary processes universally accessible whatever trust values a
caller carries, and it means PIP restricts access **to** protected
things rather than granting access to trusted callers.

Dominance is binary. A caller either dominates or does not; there is
no partial ordering and no per-operation granularity in PIP itself.

## What a signer asserts

Obtaining a tier is an assertion about the **binary**, not about what
it will do. Specifically, a signer with a key at some tier asserts
that the signed file is fit to run at that tier, that its contents are
what the signer intended, and that the signer accepts the file being
treated as trusted by every dominance comparison on every system
carrying that key.

A signer MUST NOT treat a tier as a capability grant. A high tier
confers no privilege, no access right and no identity. It protects the
process from lower-tier processes and permits it to reach
higher-protected objects; it grants nothing on its own.

A signer SHOULD understand that a tier is inherited by children at
fork and re-derived at their exec. A protected process that execs an
unsigned binary loses protection entirely — protection follows the
binary, not the lineage.

## What an object owner asserts

An object opts into PIP protection by carrying a process trust label
in its SACL, whose SID has the form `S-1-19-{type}-{trust}` — the
Process Trust authority with exactly two sub-authorities. A SID of any
other shape makes the descriptor malformed, and an evaluator MUST
reject it rather than guess.

The label's access mask names exactly the rights a **non-dominant**
caller may still receive. A dominant caller is unrestricted by the
label.

Two properties matter to anyone authoring one.

**There is no default.** An object with no trust label is unrestricted
by PIP, reachable by any process whatever its identity. Protection is
opt-in per object.

**Privileges do not compensate.** PIP revokes rights that privileges
granted, including `ACCESS_SYSTEM_SECURITY`. There is no relabel
equivalent, no administrative override, and no privilege that
substitutes for insufficient trust. An object owner labelling an
object may rely on this: a non-dominant caller cannot reach the
object's SACL to remove the label, which is what makes the protection
self-sustaining rather than trivially removable.

## What may be relied upon

A party may rely on the following.

A tier is derived from the signature alone. No parent process, no
privilege, no runtime interface and no environment can confer,
elevate, or forge one — a compromised process running as SYSTEM cannot
grant PIP to an unsigned binary.

Impersonation does not alter it. PIP is read from per-process state
rather than from a token, so a service impersonating a client still
evaluates its own tier, and a process impersonating a token created
for a protected process gains nothing.

A verified file is pinned against in-place modification for as long as
its inode remains live. Ordinary, positioned and append writes,
truncation by descriptor or pathname, every `fallocate` mode, and
content-mutating and unrecognised ioctls are all refused on it, as is
mutation or removal of the signature attribute.

**A binary the kernel execs on its own behalf carries at least
PeiosTcb trust.** Where the kernel spawns a userspace helper for its
own purposes rather than at a process's request — resolving a module
name, and any comparable kernel-initiated exec — the implementation
MUST refuse the exec unless the binary's `pip_trust` is at least the
PeiosTcb level. A party may therefore rely on such a helper being
TCB-signed, and on the exec failing rather than proceeding at a lower
tier.

The refusal MUST apply equally when no tier could be derived at all.
"Could not establish trust" and "is not trusted" reach the same
outcome here, so that the requirement cannot be evaded by preventing
the derivation from running.

## What may not be relied upon

A party MUST NOT rely on the following.

**Execution is not gated, with one exception.** A bad, tampered or
absent signature costs a binary its tier; it does not prevent
execution. PIP determines trust level, not permission to run.
Permission to run is the file's own security descriptor.

The exception is the kernel-initiated exec described above, where a
tier below PeiosTcb refuses the exec outright. It is confined to that
case for a reason: everywhere else there is a requesting process whose
own authority bounds what the exec can do, so an untrusted binary can
be allowed to run and simply carry no tier. A kernel-initiated exec has
no such process behind it — the kernel is acting on its own behalf, at
its own authority — so there is no lesser authority to fall back to and
nothing to bound the result. A party MUST NOT generalise the exception
to ordinary execs.

**Absence of a tier is not observable as an error.** There is no
diagnostic distinguishing "this binary is unsigned", "this signature
is malformed" and "this key is not in the table". All three produce a
process at type 0 and trust 0 with no indication.

**There is no revocation.** A signed binary later found to be
malicious cannot be invalidated. There is no hash blocklist and no
key-scoped revocation. The remedies are removing the file or replacing
the verifier's key table.

**A tier is not a container boundary.** PIP operates inside the
kernel's trust boundary. Kernel compromise voids it, DMA-capable
hardware bypasses it, and it offers nothing equivalent to
hypervisor-based isolation.

**Library trust is compared, not merely required.** Where a process
enables library signature verification, a library has to dominate the
loading process, so raising a process's tier narrows the set of
libraries it can load. A signer distributing libraries alongside a
high-tier program has to sign them at a tier that dominates it.

**Scripts take their interpreter's tier.** A script executed through a
`#!` line contributes nothing; the tier comes from the interpreter
binary. A signer MUST NOT expect signing a script to affect anything,
and an object owner MUST NOT treat "runs at a high tier" as evidence
that the code being run was signed.
