---
title: Overview
description: loregd is the local registry source — it holds hives in SQLite and serves them to the kernel over RSI. Where it sits, and what this manual covers.
---

**loregd** — the Local Registry Daemon — is the primary registry source
for Peios. It holds one or more registry hives in SQLite databases and
serves them to the kernel's registry subsystem over the Registry Source
Interface (RSI).

loregd is not architecturally special. Any process that implements the
RSI contract can serve as a registry source, and the kernel is
source-agnostic: it does not know or care that the process answering for
a hive keeps its data in SQLite. What makes loregd special is
operational. It is the source that provides the `Machine\` and `Users\`
hives at boot, which puts it on the critical path to a running system —
if loregd does not come up, very little else does.

## Where loregd sits

The registry is split across a trust boundary. The kernel side owns the
namespace, the layer model, access checks, watches, and transactions; it
holds no storage of its own. The source side owns bytes on disk and
answers questions about them. loregd is a source, and everything in this
manual describes the lower half of that split.

Three consequences run through the whole design:

- **loregd stores; it does not decide.** It never resolves layers, never
  filters results by visibility, and never applies a security descriptor.
  It returns every layer entry it holds and lets the kernel work out
  which one wins. The security descriptors in its tables are opaque
  payload to it.
- **GUIDs come from the kernel.** loregd does not mint key identities. It
  records the GUID it is given, and uses it as the primary key.
- **Sequence numbers come from the kernel.** loregd stores them and
  reports the maximum it holds at registration, but never allocates one.

## What this manual covers

The command line and startup sequence; the SQLite schema backing a hive
and the in-memory store backing volatile keys; the connection model,
write serialisation, and how requests are dispatched; and the handling of
each RSI operation, including transactions and enumeration ordering.

The kernel half of the registry — the namespace, layers, watches, access
control — is [chapter 5 of the Peios Kernel TRM](~peios/lcs/overview),
and the RSI wire protocol itself is
[specified in PSPK](~peios/registry-source-interface/scope). Key schemas
belong to the subsystems that own them, and loregd's supervision as a
service belongs to the init system's manual.
