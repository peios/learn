---
title: Normative References
description: The external standards this corpus depends on, and the citation format for referring to them.
---

The external standards this corpus depends on. A book MUST NOT restate
this list; it cites into it.

## Deferral

Where a document defers to an external standard, that standard's
requirements apply as though written out. A document citing one MUST
name the specific part it relies on where the whole would be ambiguous.

## Citation format

| Form | Means |
|---|---|
| `RFC 2119` | The whole document |
| `RFC 8259 §7` | A specific section |
| `Unicode 16.0` | A version of a standard |
| `MS-DTYP §2.4.2` | A section of a Microsoft Open Specification |

## IETF

| Reference | Title | Used for |
|---|---|---|
| RFC 2119 | Key words for use in RFCs | Normative keywords (§2.1) |
| RFC 3339 | Date and Time on the Internet | Timestamps (§3.3) |
| RFC 3629 | UTF-8 | String encoding (§3.3) |
| RFC 3986 | Uniform Resource Identifier | URL syntax |
| RFC 4648 | Base16, Base32, Base64 Encodings | Base64, §4 alphabet |
| RFC 7468 | Textual Encodings of PKIX Structures | PEM key files |
| RFC 8032 | EdDSA | Ed25519 signing and verification |
| RFC 8259 | JSON | JSON documents |
| RFC 8478 | Zstandard | Compression |
| RFC 8915 | Network Time Security | Authenticated time |

## Microsoft Open Specifications

The Windows security model is the design source for several Peios
subsystems, and its documents are cited for parity mappings.

| Identifier | Title |
|---|---|
| MS-DTYP | Windows Data Types |
| MS-ERREF | Windows Error Codes |
| MS-LSAD | Local Security Authority (Domain Policy) Remote Protocol |
| MS-SAMR | Security Account Manager Remote Protocol |
| MS-ADTS | Active Directory Technical Specification |
| MS-GPOL | Group Policy: Core Protocol |
| MS-GPREG | Group Policy: Registry Extension Encoding |

## Unicode

| Reference | Used for |
|---|---|
| Unicode 16.0 | Normalization forms, case folding |
| `CaseFolding.txt`, status `S` and `C` entries | Case-insensitive comparison |

## POSIX and other standards

| Reference | Used for |
|---|---|
| IEEE Std 1003.1-2017, Chapter 14 | The pax interchange format |
| MessagePack specification | Event payload encoding |
| SPDX License List | License identifiers |

## External conventions

Some documents describe interoperation with conventions that have no
formal specification — the `sd_notify` readiness protocol and the
freedesktop `os-release` file among them. Where a document relies on
one, it MUST describe the behaviour it depends on rather than citing the
convention alone, because there is no normative text at the other end of
the citation.
