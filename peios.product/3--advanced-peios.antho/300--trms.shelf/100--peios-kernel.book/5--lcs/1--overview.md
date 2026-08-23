---
title: Overview
description: LCS is the kernel half of the Peios registry — where it sits, its semantic core, what is layered and what is not, and where the model diverges.
---

LCS — the Layered Configuration Subsystem — is the kernel half of the
Peios registry: a hierarchical, access-controlled configuration store
modelled on the Windows registry. It owns the namespace, the security
model, change observation, transactions, and the layer system that
gives the registry its name. It owns no storage at all.

Storage belongs to **sources**: userspace processes that hold registry
data and answer questions about it over the Registry Source Interface.
A source stores what it is told and returns everything it holds; it
never resolves layers, never filters by visibility, never sees the
identity of a caller, and never interprets a path beyond the parent and
child names it is given. Every decision about what a caller may see or
do is made in the kernel. loregd is the first source, and the one that
provides `Machine\` and `Users\` at boot, but nothing in LCS knows that:
hive routing is built entirely from what registers.

Userspace never talks to a source. Processes reach the registry through
three syscalls and eighteen ioctls, and the fd those syscalls return is
a capability — an open key carries the access mask it was granted, and
carries it wherever the fd goes.

## Where it sits

LCS is a subsystem of PKM, peer to KACS and KMES, staged into the
kernel tree as `security/pkm/lcs` and built by `CONFIG_SECURITY_PKM` — a
boolean option, so it is linked into `vmlinux` rather than loaded. Its
three syscalls occupy 1100–1102 in the PKM range, added to the syscall
table by a patch against `arch/x86/entry/syscalls/syscall_64.tbl`.

It depends on KACS and KACS does not depend on it. Every access
decision LCS makes is a call into the KACS AccessCheck function against
a Security Descriptor the source returned; LCS defines no access
control mechanism of its own. Security Descriptor inheritance at key
creation is likewise KACS's computation, not LCS's. Audit events go to
KMES.

A substantial part of LCS is Rust. The crate `lcs-core` is staged
alongside PKM's other cores as `security/pkm/lcs/lcs_core` and holds
the parts where correctness is a matter of pure decision rather than
kernel plumbing: layer resolution, the RSI wire codec, the backup
stream serialiser, the transaction mutation log, watch dispatch, case
folding, and configuration validation. The C half owns fds, the char
device, memory, locking, and the syscall boundary.

## The semantic core

Six rules generate the rest of the model. Every behaviour described in
this chapter is a consequence of one of them.

1. **Names are layered.** A key's presence at a path is per-layer.
   Different layers can name different keys at the same path, and
   removing a layer removes its names.
2. **Values are layered.** Every write is tagged with a layer; the
   effective value is the highest-precedence entry. Tombstones can
   actively mask lower layers.
3. **Key identity is not layered.** A key's GUID, Security Descriptor,
   volatile flag, symlink flag and last write time belong to the key
   object, not to any layer, and are never automatically reverted.
4. **Security is key-bound, not layer-bound.** Modifying a Security
   Descriptor is a permanent change to the key. Removing a layer does
   not revert it. Security policy is operational state, not
   configuration overlay.
5. **Handles are capabilities granted at open.** An open key fd carries
   an access mask computed once, by AccessCheck, at open time. Later
   operations test the mask, not the descriptor. Changing a descriptor
   does not affect an fd that already exists.
6. **Sources persist, the kernel decides meaning.** A source stores
   path entries, key records and value entries and returns all of them.
   Everything else is the kernel's.

The consequence that surprises people most often is the fourth. A
layer is a configuration overlay and reverts cleanly; an access control
change is not configuration and does not.

## What is layered and what is not

| Property | Layered | Resolved by | Survives layer deletion |
|---|---|---|---|
| Path existence | Yes | Highest precedence, then highest sequence | No |
| Values | Yes | Highest precedence, then highest sequence | No |
| Value tombstones | Yes | Masking lower precedence | No |
| Blanket tombstones | Yes | Masking all lower-precedence values on the key | No |
| Key hiding | Yes | Masking lower precedence | No |
| Key GUID | No | Direct on the key object | Yes |
| Security Descriptor | No | Direct on the key object | Yes |
| Volatile flag | No | Direct on the key object | Yes |
| Symlink flag | No | Direct on the key object | Yes |
| Last write time | No | Direct on the key object | Yes |

A watch is bound to the key object rather than to either, and stays on
that object whatever happens to the name (§5.6.3).

## registry.pol

One external format constrains the design. `registry.pol` is the binary
format Active Directory Group Policy uses to deliver configuration to
domain-joined machines, and the registry exists so that Peios can
consume it without loss. Everything `registry.pol` can express, the
registry can represent.

Three consequences run all the way through:

- The **full Windows value type set** is supported, including the three
  hardware-resource types that carry no Peios semantics at all. They
  behave exactly as `REG_BINARY`; they exist so a value copied from a
  Windows hive round-trips with its type tag intact (§5.2.6).
- **Paths are backslash-separated, case-preserving and
  case-insensitive.** This is not negotiable and it is the reason case
  folding appears in the kernel at all (§5.2.8).
- **Registry access rights occupy the Windows bit positions**, so a
  Security Descriptor containing registry ACEs is binary-compatible
  (§5.4.2).

Tombstones and blanket tombstones exist for the same reason: the
`**Del.ValueName` and `**DelVals` directives express *absence*, which a
purely additive overlay cannot (§5.2.7).

LCS does not parse `registry.pol`. Parsing is a userspace concern; LCS
provides the model that makes a faithful translation possible.

No other parity with Windows is claimed. The binary compatibility of a
Security Descriptor is a KACS guarantee, not an LCS one.

## Where the model diverges from Windows

LCS is modelled on the Windows Configuration Manager, and departs from
it in seven places. All seven are decisions rather than gaps.

| | Windows | LCS |
|---|---|---|
| Backing store | Kernel-internal hive files | Userspace sources over the RSI, so a storage backend is not a kernel change |
| Hive routing | A fixed set of predefined hives | Any source may register any name at runtime |
| Layers | None; `registry.pol` is applied by flattening values | Precedence-ordered layers with tombstones, resolved at query time, so removal reverts rather than tattoos |
| Change observation | `RegNotifyChangeKeyValue`, single-shot | Persistent watches, closing the re-registration race |
| Key identity | Hive cell offsets | GUIDs, stable across storage reorganisation |
| Forward slash | Not accepted | Accepted on input, normalised to backslash |
| Case comparison | `RtlCompareUnicodeString` | Unicode Simple Case Folding, pinned to a version |

## Windows features that are absent

Four have been evaluated and deliberately excluded.

**Key classes.** The `class` parameter of `RegCreateKeyEx` is
documented by Microsoft as reserved, and no consumer of it is known.

**`RegOverridePredefKey`.** Per-process key redirection, and specific
to COM. It would require unbounded per-process state in the kernel, and
private hives and private layers cover the uses that are legitimate.

**WoW64 redirection.** Splitting keys by pointer width. Peios has no
32-bit compatibility concern to split for.

**The `HKEY_CLASSES_ROOT` merged overlay.** A merge of `HKLM` and
`HKCU` `Software\Classes`, again COM-specific, with no Peios
equivalent.

## This chapter

§5.2 covers the data model — hives, keys, path entries, values,
tombstones, names, and what happens to a key that loses its last name.
§5.3 covers layers: the model, the base layer, where layer metadata
lives and the circularity that implies, who may write into a layer, and
the resolution algorithm and the sequence counter that drives it. §5.4
covers security: the access flow, the rights, inheritance, and the audit
events LCS emits. §5.5 covers the syscall and ioctl interface and the
error model. §5.6 covers watches, §5.7 transactions, and §5.8 the source
model — registration, dispatch, validation, and the intricate business
of what a late response means. §5.9 covers backup and restore, §5.10 how
LCS configures itself out of the registry it is serving, and §5.A the
ABI.

Two contracts extracted from LCS are specified rather than described,
because a third party implements the other side of each: the Registry
Source Interface and the registry backup format. Both are chapters of
PSPK.
