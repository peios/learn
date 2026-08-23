---
title: Overview
description: What the Peios kernel is — a Linux kernel with a patch series, the PKM module and a uapi header set compiled into it — and what this manual covers.
---

The Peios kernel is a Linux kernel with Peios compiled into it. Peios
contributes three things to the tree it is built from: a patch series
of around fifty patches against existing kernel files, a new
`security/pkm` subtree, and a new `fs/stratafs` subtree. None of it is
loadable. `CONFIG_SECURITY_PKM` and `CONFIG_STRATAFS_FS` are both
boolean options, so what they build is linked into `vmlinux`; there is
no module to insert and none to unload.

`security/pkm` builds as **PKM**, the Peios Kernel Module — the name
predates the decision to build in, and the subsystem still carries it.
PKM registers as a Linux Security Module, provides the syscalls in the
PKM range, and holds three of the four subsystems described here. The
fourth, stratafs, is an ordinary in-tree filesystem that sits beside
PKM rather than inside it, and reaches PKM through a kernel-private
header that exports no symbols to modules.

The four subsystems are peers.

**KMES**, the Kernel Mediated Event Subsystem, is the sole event
emission path in Peios. Kernel subsystems and userspace processes alike
emit events exclusively through KMES; it stamps each event with trusted
metadata, buffers it in per-CPU ring buffers, and delivers it to
userspace consumers through shared memory.

**KACS**, the Kernel Access Control System, is the security core: SIDs,
tokens, security descriptors, privileges, impersonation, process
protection, binary signature verification, and the AccessCheck
algorithm that ties them together. KACS also projects Peios identities
onto Linux credentials so that unmodified Linux subsystems make
decisions consistent with Peios policy.

**stratafs** is the layered filesystem. It composes an ordered stack of
strata — ordinary directories, independently owned — into a single
mounted tree, resolving each name in the highest-precedence stratum
that holds it, routing each modification to the stratum that will
accept it, and copying an object up into the designated create stratum
when its own stratum will not. It stores nothing of its own, and
delegates every access decision to KACS.

**LCS**, the Layered Configuration Subsystem, is the kernel half of the
Peios registry. It owns the data model — hives, keys, values, and the
precedence-ordered layers the name refers to — along with access
control, watches, transactions, and the syscall and ioctl surface
through which processes read and write configuration. It holds no
storage of its own, delegating that to userspace sources over the
Registry Source Interface.

This manual describes each subsystem in its own chapter, in the order
above. They are peers, but not independent: KMES stamps
events with identities it obtains from KACS, KACS emits its audit
trail through KMES, LCS enforces access with KACS security
descriptors, and stratafs consults KACS for every delegation decision.
Cross-references between chapters mark these seams.

## What this manual is

This is a technical reference manual: an exhaustive description of the
kernel as it is actually built. It documents observed behaviour —
formats, algorithms, limits, failure modes — in plain indicative prose.
It is not a standard, and it makes no conformance demands.

The contracts the kernel shares with other parties are specified
elsewhere, in the Peios Core Specification Anthology: the binary
structures that cross subsystem boundaries (GUIDs, SIDs, security
descriptors) in PCDS, and the protocols the kernel speaks with
userspace services and the formats they exchange — the registry source
interface, the registry backup format, the event stream consumer
protocol — in PSPK. Where a chapter touches one of those
contracts, it references the specification rather than restating it,
and describes only what this kernel adds: how the contract is
implemented, and the behaviour on this side of the boundary.

Constants, ABI tables, and catalogues are collected in appendices at
the end of the chapter they belong to, so that a chapter's reference
material sits beside the prose that explains it.
