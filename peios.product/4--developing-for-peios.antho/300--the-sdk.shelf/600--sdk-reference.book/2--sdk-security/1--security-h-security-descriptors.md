---
title: security.h — Security descriptors
description: What security.h covers — SIDs, access masks, ACLs, descriptors, views, the SDDL codec and inheritance — and the conventions it assumes.
---

`<peios/security.h>` is the shared vocabulary of the whole access-control surface. SIDs, security descriptors, ACLs, and ACEs are the currency every KACS interface trades in — tokens carry them, files are protected by them, access checks evaluate them, and the registry secures keys with them. They cross the kernel boundary as variable-length, self-relative byte buffers in the MS-DTYP wire formats, and this module is the one place libpeios lifts that raw wire form into something safe to handle from C.

Everything here assumes the [library conventions](~peios/sdk-conventions/library-conventions): `ssize_t` returns are byte lengths using the two-call protocol, builders are heap-backed and sticky-error, and views borrow the buffer they parse. This page does not repeat those rules per function — read that page first.

The module has four parts:

- **[SIDs](~peios/sdk-security/sids)** — build, parse, format, and compare security identifiers.
- **[ACLs and security descriptors](~peios/sdk-security/building-acls)** — assemble them with builders.
- **[Parsing](~peios/sdk-security/parsing-views)** — read them back with zero-copy views.
- **[SDDL and inheritance](~peios/sdk-security/sddl-text-codec)** — the text form and the userspace-only inheritance helpers.

The wire constants (`KACS_SID_*`, `KACS_SD_*`, `KACS_ACE_*`, and `struct kacs_generic_mapping`) come straight from `<pkm/sid.h>` and `<pkm/sd.h>`. libpeios does not re-alias them — you use the published ABI names directly.

## Go descriptor selectors

The independent Go SDK exposes the same component selection through
`github.com/peios/peios-go/security.SecurityInformation`: `InfoOwner`,
`InfoGroup`, `InfoDACL`, `InfoSACL`, and `InfoLabel`. `InfoLabel` is the
`KACS_SECINFO_LABEL` / `LABEL_SECURITY_INFORMATION` bit (`0x10`); it selects
only the mandatory-integrity label carried in the descriptor's SACL.

Pass `security.InfoLabel` to `file.GetDescriptor` / `file.SetDescriptor`,
their `At` variants, or `registry.Key.GetDescriptor` / `SetDescriptor` to
read or update that label while preserving unselected components. It can
be combined with `InfoOwner`, `InfoGroup`, or `InfoDACL`, but combining it
with `InfoSACL` is invalid. A label-only query needs `READ_CONTROL`; an
update needs `WRITE_OWNER`, and raising the label above the caller's
integrity also needs `SeRelabelPrivilege`. The descriptor bytes still use
the ordinary self-relative format: selecting a label does not make it a
standalone SID buffer.

## See also

- **[Library conventions](~peios/sdk-conventions/library-conventions)** — the error, buffer, builder, and view rules this page builds on.
- **[SIDs](~peios/identity/sids)** and **[Security descriptors](~peios/security-descriptors/overview)** — the operator-side concepts behind this vocabulary.
- **[`<peios/token.h>`](~peios/sdk-tokens/token-h-tokens-and-sessions)**, **[`<peios/file.h>`](~peios/sdk-files/file-h-file-security)**, **[`<peios/access.h>`](~peios/sdk-access/access-h-access-checks)** — the KACS interfaces that consume this vocabulary, including the generic-mapping tables `peios_access_map_generic` expects.
