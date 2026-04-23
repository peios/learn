---
title: Terminology
---

This section defines terms used throughout the specification. Terms
defined inline in later sections (path entries, tombstones, the base
layer, effective values, etc.) are not duplicated here.

- **PKM** (Peios Kernel Module): The single loadable kernel module
  (`pkm.ko`) containing all Peios kernel extensions. LCS and KACS are
  peer subsystems within PKM.

- **KACS** (Kernel-based Access Control System): The access control
  subsystem within PKM. Implements per-thread tokens, Security
  Descriptors, and AccessCheck. LCS depends on KACS for all access
  control decisions. KACS has no dependency on LCS. Specified
  separately in the KACS v0.20 specification.

- **LCS** (Layered Configuration Subsystem): The configuration
  subsystem within PKM, peer to KACS. Implements the kernel-side
  registry: syscall dispatch, hive routing, access control
  enforcement (via KACS AccessCheck), layer resolution, watch
  dispatch, transaction coordination, and enforcement of the
  Registry Source Interface. Userspace processes interact with LCS
  exclusively through syscalls. "LCS" refers specifically to the
  kernel-side code.

- **Registry**: The user-facing configuration system provided by
  LCS and its sources working together. When precision matters, use
  "LCS" for the kernel subsystem and the relevant source name (e.g.,
  "loregd") for the userspace component. When the distinction does
  not matter, "the Registry" covers the whole thing.

- **Source**: A userspace process that implements the Registry Source
  Interface (RSI) for one or more hives. Sources handle storage --
  reads, writes, enumeration, transactions. They do not make access
  control decisions, see caller identity, manage watches, or
  interpret paths beyond the key hierarchy they store. A source
  registers its hives with the kernel at startup and communicates
  via the RSI binary protocol. loregd is the first source.

- **RSI** (Registry Source Interface): The binary protocol and
  contract between LCS and its sources. Defines the operations LCS
  can request, the response format, and the error model. Any process
  implementing the RSI can back a hive -- LCS is source-agnostic.

- **Hive**: A top-level namespace in the registry. Each hive is an
  independent tree of keys and values, backed by exactly one source.
  A source may back multiple hives. Hive names are the first
  component of every registry path and are resolved by LCS's routing
  table. Examples: `Machine\`, `Users\`.

- **Key**: A node in the registry hierarchy. Keys are containers --
  they hold subkeys (forming a tree) and values (holding data). Every
  key has a GUID (its identity), a Security Descriptor (controlling
  access), and metadata. Keys are analogous to directories in a
  filesystem.

- **Value**: A named, typed datum stored within a key. Each value has
  a name (string), a type (REG_SZ, REG_DWORD, etc.), and data. A key
  can hold multiple values, each with a distinct name. One unnamed
  value per key is permitted (the default value). Values are analogous
  to files.

- **Layer**: A named, precedence-ordered collection of registry
  writes. Every write is tagged with a layer. Reads resolve across
  layers: the highest-precedence entry wins. Removing a layer removes
  its entries and lower-precedence values surface automatically.

- **SD** (Security Descriptor): A KACS structure controlling access
  to a registry key. Contains a DACL (who can access, and how) and
  optionally a SACL (audit policy). LCS retrieves a key's SD from
  the source and passes it to KACS AccessCheck at key open time.

- **AccessCheck**: The KACS evaluation function that determines
  whether a caller's token grants the requested access against an
  object's SD. LCS calls AccessCheck at key open time. Single code
  path for all access control decisions across all Peios subsystems.

- **Token**: A per-thread identity object maintained by KACS.
  Contains a user SID, group SIDs, a privilege bitmask, an integrity
  level, and metadata. When a thread makes a registry syscall, LCS
  captures the thread's effective token (including impersonation
  tokens) for AccessCheck evaluation.

- **SID** (Security Identifier): A unique principal identifier (e.g.,
  `S-1-5-18` for SYSTEM, `S-1-5-32-544` for Administrators). SIDs
  appear in tokens, in SDs, and in registry paths (`Users\<SID>\`).

- **GUID**: A 128-bit identifier assigned by the kernel at key
  creation time and persisted by the source. A key's GUID is its
  identity -- immutable, never reused. Paths are the user-facing
  interface; GUIDs are the internal identity.

- **Watch**: A persistent subscription for changes on a key fd.
  Armed via ioctl, pollable via epoll. Watches can cover a single
  key or an entire subtree. Events are delivered as structured
  records read from the fd.

- **TCB** (Trusted Computing Base): The set of components whose
  correct behaviour is necessary for security. In the registry
  context, the TCB includes the kernel, KACS, LCS, and sources.
  Sources are TCB because LCS trusts the data they return -- SDs,
  values, symlink targets, key metadata.
