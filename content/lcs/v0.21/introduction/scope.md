---
title: Scope
order: 1
---

This specification defines the Layered Configuration Subsystem (LCS) for
the Peios operating system. LCS is the configuration subsystem within the
Peios Kernel Module (PKM), peer to KACS. It provides a kernel-mediated,
access-controlled, hierarchical configuration store modelled on the
Windows registry.

LCS is the primary structured configuration authority in Peios. All
registry operations -- opening keys, reading values, writing
configuration, watching for changes -- pass through LCS syscalls.
Userspace processes never communicate with backing stores directly.

This specification covers:

- The data model -- hives, keys, values, layers, path entries, and their
  relationships
- The syscall and ioctl interface exposed to userspace
- The Registry Source Interface (RSI) -- the binary protocol and contract
  between LCS and its backing stores
- The security model -- KACS AccessCheck integration, SD inheritance
  delegation, per-key access control, and registry-specific access rights
- Watches -- persistent change observation with subtree semantics, event
  types, dispatch, and queue management
- Transactions -- source-scoped atomic multi-key writes
- The layer system -- precedence-ordered configuration overlays with
  tombstones, key hiding, and layer resolution
- The backup format -- binary stream format for bulk subtree
  export/import
- LCS bootstrap behaviour -- compiled-in defaults, self-configuration,
  and hot-swap sequencing
- Self-configuration -- operational parameters read from the registry
  with validated hot-swap
- Failure modes -- source crash, request timeout, transaction timeout,
  data validation

This specification does not cover:

- loregd internals (SQLite schema, storage engine, caching, connection
  management)
- Specific registry key schemas (those belong to the subsystems that own
  them)
- KACS (covered by the KACS v0.20 specification)
- peinit boot decisions (first-boot detection, seed restore triggering,
  service start ordering)
- authd, lpsd, eventd, or any other userspace daemon
- Future GOQL query language
- Network-level registry access or replication
