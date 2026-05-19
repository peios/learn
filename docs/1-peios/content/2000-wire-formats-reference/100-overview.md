---
title: Wire formats reference
type: reference
description: The byte-level binary formats used to pass data between userspace and kernel — token specs, session specs, security descriptors, conditional ACE bytecode, CAAP policies. This page covers the conventions every format follows and points to the per-format details.
related:
  - peios/wire-formats-reference/token-and-session-specs
  - peios/wire-formats-reference/security-descriptors
  - peios/wire-formats-reference/conditional-ace-bytecode
  - peios/wire-formats-reference/caap-format
  - peios/kernel-abi-reference/overview
---

A **wire format** in KACS is the byte-level layout of a binary payload passed across the kernel/userspace boundary. Where the [Kernel ABI reference](~peios/kernel-abi-reference/overview) covers the syscalls and struct parameters, the wire formats cover the variable-length payloads that those structs point to.

The major wire formats:

| Format | Use |
|---|---|
| **Token spec** | The wire format the caller passes to `kacs_create_token`. Defines the full token's contents. |
| **Session spec** | The wire format for `kacs_create_session`. Defines a new logon session. |
| **Security descriptor** | The self-relative binary form of an SD. Used everywhere — file SDs, registry SDs, process SDs, token self-SDs, the SDs inside CAAP rules. |
| **Conditional ACE bytecode** | The postfix expression language used in callback ACEs and CAAP applies-to expressions. |
| **CAAP policy** | The wire format for a central access policy passed to `kacs_set_caap`. |

The signature blob format (for binary signing) is also a wire format, but it is covered in [Binary signing](~peios/binary-signing/signature-format) because it sits next to the binary-signing concept material rather than being a kernel/userspace payload.

## Conventions

Several conventions are shared across most wire formats:

**Little-endian numeric encoding** on x86_64. Multi-byte integers are little-endian; the format matches the platform's native byte order.

The exception is the SID `IdentifierAuthority` field — big-endian, for cross-system compatibility. SIDs are the only place this happens; everywhere else is little-endian.

**Length-prefixed strings and arrays.** Variable-length fields typically start with a u32 length, followed by the bytes (or per-element records). The kernel can read the length before allocating; the producer can compute the length once and write it.

**Self-delimiting structures.** Where multiple records share a buffer, each carries its own length so the reader can walk the buffer without an external manifest.

**Reserved fields and padding** must be zero. Non-zero values in reserved fields return `-EINVAL`. This is the forward-compatibility hook — future versions may give reserved fields meaning.

**Version bytes.** Most wire formats start with a version byte at offset 0. v0.20 uses version byte `0x01` for every format that has one. Unknown version bytes are rejected.

**Size limits.** Every format has an enforced maximum size to prevent unbounded inputs. Most are in the 64 KB to 256 KB range; specific limits are documented per format.

**No embedded pointers.** Wire formats are self-contained. Offsets within a format are relative to the start of the format's buffer; there are no pointers to other userspace addresses. This is what makes the formats serializable.

## Common building blocks

A handful of building blocks appear across multiple formats:

### SIDs in wire format

A SID's binary form:

| Bytes | Field | Encoding |
|---|---|---|
| 0 | Revision | `0x01` |
| 1 | SubAuthorityCount | 0–15 |
| 2–7 | IdentifierAuthority | 6 bytes, **big-endian** |
| 8 onward | SubAuthorities | 4 bytes each, little-endian |

Total size: 8 + 4 × SubAuthorityCount bytes. Range: 8–68 bytes.

SIDs appear in token specs (user_sid, groups, restricted_sids, etc.), in SDs (owner, group, ACE SIDs), in conditional ACE bytecode (SID literals, attribute references), in CAAP policy SIDs.

### Length-prefixed lists

The pattern `[count:u32le][record × count]` is common. Examples:

- Token spec groups list: count + per-group records.
- Token spec privileges: count + per-privilege records.
- Object type list for AccessCheckList: count + per-entry records.

The kernel reads the count, validates it against any structural maximum, allocates appropriately, then reads the records.

### Length-prefixed byte buffers

The pattern `[length:u32le][bytes:length]` is also common. Examples:

- Token spec embedded SDs (default DACL).
- CAAP spec embedded DACL/SACL.
- Claim payloads inside resource attribute ACEs.

The buffer can hold any binary blob whose interpretation depends on context — the format is uniform; the meaning varies.

### Multi-entry claim buffers

Token claims (`user_claims`, `device_claims`) and local claims (passed to AccessCheck) use a specific multi-entry format:

```
[entry1_len:u32le][entry1 bytes]
[entry2_len:u32le][entry2 bytes]
...
```

Until the buffer is exhausted. Each entry is a single claim record (one attribute with its value or values).

The kernel walks the buffer, reading each entry's length and then the entry. Encountering a length that would extend beyond the buffer's end signals a malformed buffer; `-EINVAL` is returned.

The claim entry layout itself is documented in [Token and session specs](~peios/wire-formats-reference/token-and-session-specs).

## Validation rules

The kernel validates every wire-format input strictly. The general pattern:

1. **Top-level size check.** Is the buffer at least the minimum required for the format? Is it within the format's maximum?
2. **Version check.** If the format starts with a version byte, is it a recognised version?
3. **Structural parse.** Walk the format reading lengths, counts, fields. Check each is within bounds.
4. **Cross-reference validation.** Indices into arrays must be within range; SIDs must be well-formed; references between fields must be consistent.
5. **Semantic validation.** Are the values themselves valid? (E.g., a token can't have an unknown logon type; an SD can't have an unknown ACE type.)

A failure at any step returns `-EINVAL`. The kernel does not attempt partial parsing; either the whole input is valid, or the call fails atomically.

The specific validation rules per format are documented per format. The pattern is consistent.

## What is *not* a wire format

A few things adjacent to wire formats but not in this topic:

- **Struct layouts for syscall parameters** are in [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat). Those are the parameter records (`kacs_open_how`, `kacs_access_check_args`); the wire formats are what those records *point to* (the SD blob, the open creation SD, etc.).
- **Audit event payloads** are msgpack-encoded; covered in [Audit event reference](~peios/audit-event-reference/overview).
- **Filesystem-specific xattrs** (where SDs land on disk) have their layout determined by the SD wire format plus the xattr storage mechanism. The SD format here is what gets stored; how the filesystem stores it is a filesystem-level concern.

## Where to start

If you need to construct or parse a token or session spec for `kacs_create_token` / `kacs_create_session`, read [Token and session specs](~peios/wire-formats-reference/token-and-session-specs).

If you need to construct or parse a security descriptor — the binary layout used everywhere SDs cross the kernel boundary — read [Security descriptors](~peios/wire-formats-reference/security-descriptors).

If you need to construct or parse a conditional ACE expression (the bytecode used inside callback ACEs and CAAP applies-to expressions), read [Conditional ACE bytecode](~peios/wire-formats-reference/conditional-ace-bytecode).

If you need to construct or parse a CAAP policy for `kacs_set_caap`, read [CAAP format](~peios/wire-formats-reference/caap-format).
