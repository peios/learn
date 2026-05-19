---
title: SIDs
type: concept
description: A Security Identifier (SID) is the unique name for every principal in Peios. This page covers the SID format — the string form you'll see in logs and configs, the binary form on the wire, and the rules for comparing two SIDs.
related:
  - peios/identity/overview
  - peios/identity/well-known-principals
  - peios/tokens/overview
---

A **SID** (Security Identifier) is the unique name for a principal. Every user, group, service, machine, and well-known system actor has exactly one SID, and that SID is how every other part of Peios refers to them: ACEs in a security descriptor name SIDs, tokens carry SIDs, audit events log SIDs.

Two SIDs are equal only if their binary encodings match byte-for-byte. There is no normalization, no case folding, no "this matches that if you squint" rule. A SID is its bytes.

## The string form

The form you will see in logs, configuration, and almost every administrative tool is the **string form**:

```
S-1-5-21-3623811015-3361044348-30300820-1001
```

The pieces:

| Position | Meaning |
|---|---|
| `S` | Constant marker — every SID string starts with `S`. |
| `1` | Revision number. Always `1` in Peios. |
| `5` | Identifier authority. A small integer naming the SID's overall namespace. |
| `21-3623811015-3361044348-30300820` | Sub-authorities. A sequence of integers that locate this principal within the authority's namespace. |
| `1001` | Relative identifier (RID). The last sub-authority. Distinguishes individual principals within a domain. |

A SID has between 1 and 15 sub-authorities. Most have between 1 and 7. The RID is just whatever sub-authority comes last; "RID" is a name for its role in domain SIDs, not a separate field.

### When the authority is written in hex

The identifier authority is a 48-bit value. When it fits in 32 bits — which it does for every authority Peios uses — it is written in decimal. If the upper 16 bits are nonzero, the authority is instead written as a `0x`-prefixed 12-digit hexadecimal value:

```
S-1-0x000000123456-1-2-3
```

You will not see this form in practice on Peios. It exists for parity with external systems that allocate from the upper authority range.

## The binary form

On the wire (in security descriptors, in tokens, in audit events), a SID is a packed byte structure:

```
+----+----+----+----+----+----+----+----+
| 01 | NN | AA   AA   AA   AA   AA   AA |
+----+----+----+----+----+----+----+----+
| sub_1 (4 bytes, little-endian)         |
+----+----+----+----+----+----+----+----+
| sub_2 (4 bytes, little-endian)         |
+----+----+----+----+----+----+----+----+
|                  ...                   |
+----+----+----+----+----+----+----+----+
| sub_N (4 bytes, little-endian)         |
+----+----+----+----+----+----+----+----+
```

| Bytes | Field | Encoding |
|---|---|---|
| 0 | Revision | `0x01` |
| 1 | SubAuthorityCount | 0–15 |
| 2–7 | IdentifierAuthority | 6 bytes, **big-endian** |
| 8 onward | SubAuthorities | 4 bytes each, **little-endian** |

The mixed endianness — big-endian for the authority, little-endian for the sub-authorities — is the one detail worth memorising. The rest of KACS is uniformly little-endian; the SID authority is the exception, for compatibility with the way SIDs travel across federation boundaries.

A SID is between 8 bytes (no sub-authorities, very rare) and 68 bytes (15 sub-authorities) long.

## Comparison

Two SIDs are equal iff their binary representations are identical byte-for-byte. Nothing else counts.

This rule has consequences worth knowing:

- **The string form is for humans.** Two strings that look equivalent might not encode to the same bytes if one was reconstructed by hand and got a leading zero wrong, or if one used hex authority where decimal would do. Always compare in binary.
- **There is no case folding.** SIDs do not contain letters in their numeric form, so this rarely matters, but tools that print SIDs alongside resolved names — `BUILTIN\Administrators` for `S-1-5-32-544`, say — must compare the SID, not the name.
- **The kernel only compares for equality.** When KACS matches a SID in an ACE against the SIDs in a token, it tests the full encoded bytes for equality — there is no "same domain" or "prefix match" at the access-check level. Userspace tooling can of course parse SIDs and compare them structurally for its own purposes (listing all users in a domain, filtering by authority, reporting), and is expected to. That parsing is on top of the byte representation; the underlying bytes are still what define identity.

If you are writing code that handles SIDs, store them as their binary form whenever possible and convert to strings only at the UI boundary.

## SID patterns you will recognise

The sub-authorities of a SID encode meaning by convention, not by parse rule. A few patterns appear so often that you will start to recognise them by shape:

| Pattern | Meaning |
|---|---|
| `S-1-5-32-...` | A built-in alias group under the NT Authority — local administrators, users, guests, etc. |
| `S-1-5-21-W-X-Y-...` | A principal in a specific domain. The three numbers after `21` identify the domain; the last sub-authority is the RID. |
| `S-1-5-5-X-Y` | A logon SID. Created per authentication event; lets ACEs target "the specific login session that did this". |
| `S-1-16-N` | An integrity level. Used as a label in a SACL, not in a DACL. |
| `S-1-19-T-L` | A process integrity protection (PIP) trust label. Used in SACLs on objects that opt in to PIP. |
| `S-1-5-80-h1-h2-h3-h4-h5` | A service SID, derived from a service name. Lets ACEs target a specific service independent of the account it runs under. |
| `S-1-15-3-h1-...-h8` | A capability SID, derived from a capability name. Used in confinement to grant a specific capability to a sandboxed application. |

The full catalog of named SIDs is in [Well-known principals](~peios/identity/well-known-principals). The derivation rules for service SIDs and capability SIDs — where the hash values actually come from — are documented under their respective topics.

## What a SID does *not* tell you

A SID identifies a principal but says nothing else about them. From a SID alone you cannot tell:

- Which groups the principal is a member of (the token's group list does that).
- What integrity level the principal runs at (the token's `integrity_level` field).
- What privileges the principal has (the token's privilege bitmask).
- Whether the principal is currently logged in (the logon session does that).

A SID is just the name. Everything else about a principal lives somewhere else — usually on the token that carries the SID at runtime.
