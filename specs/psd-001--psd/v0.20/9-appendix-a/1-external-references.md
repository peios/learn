---
title: External Reference Conventions
---

PSDs frequently reference external specifications, standards, and documentation. This appendix defines the citation conventions for commonly referenced sources and the general rules for referencing any external document.

## Normative deferral

An external specification SHOULD only be referenced as a normative implementation dependency when the implementation would genuinely be delegated to a third-party library. If Peios owns the implementation, the PSD MUST be self-contained -- an implementer MUST be able to build the feature from the PSD alone, without reading the external source.

External sources SHOULD be cited as prior art, parity references, or format compatibility targets. They MUST NOT be the sole definition of behavior that Peios implements directly.

> [!INFORMATIVE]
> Example: KACS explicitly specifies SID binary format rather than deferring to MS-DTYP §2.4.2. MS-DTYP is cited as the parity target ("byte-compatible with MS-DTYP"), but the KACS spec contains every detail an implementer needs. An implementer reads the KACS spec, not MS-DTYP.
>
> By contrast, a userspace Go daemon that encodes msgpack payloads can legitimately defer to the MessagePack specification, because the implementation is a library call (`encoding/msgpack`). The external spec is the library's contract, not yours.

The boundary between "explicitly specify" and "defer to external" is whether the code is written by the Peios project:

- **Kernel code**: Almost always explicitly specify. There are no third-party libraries in the kernel. Even well-known formats (msgpack, CBOR, protobuf) must be specified in the PSD if they appear in kernel paths, because someone has to write or embed the implementation.
- **Userspace code with library support**: Deferral is acceptable when a well-maintained library exists and the specification would simply restate the library's contract. The PSD SHOULD still specify which subset of the external format is used and any constraints beyond what the library enforces.
- **Userspace code without library support**: Treat as kernel code -- explicitly specify.

A PSD that defers to an external specification MUST identify the deferral explicitly:

```markdown
Event payloads are encoded using MessagePack as defined by the
MessagePack specification. KMES does not interpret or validate
payload contents; encoding and decoding are a userspace concern.
```

A PSD that re-specifies behavior from an external source MUST identify the external source as prior art and document any divergences:

```markdown
SIDs use the binary format defined in this specification. The
format is byte-compatible with MS-DTYP §2.4.2. See §1.4 for
divergences.
```

## Citation format

External references MUST use the document's canonical short identifier where one exists (e.g., `RFC 2119`, `MS-DTYP`). The full title SHOULD appear at first use or in the prior art section (§1.4).

When referencing a specific location within an external document, the section number MUST be included: `MS-DTYP §2.4.2`, `RFC 7230 §3.2.6`. Use the section numbering convention native to the referenced document.

External references MUST NOT use URLs as the primary citation form. URLs are unstable. The canonical identifier and section number are the durable reference; a URL MAY be included parenthetically or in the prior art section for convenience.

## IETF RFCs

Format: `RFC NNNN` or `RFC NNNN §N.N`.

RFCs are cited by number. No zero-padding.

| Example | Meaning |
|---|---|
| `RFC 2119` | The whole RFC |
| `RFC 7230 §3.2.6` | A specific section |

First use within a PSD SHOULD include the title:

```markdown
... as described in RFC 2119 ("Key words for use in RFCs to
Indicate Requirement Levels").
```

## Microsoft Open Specifications

Format: `MS-XXXX` or `MS-XXXX §N.N.N`.

Microsoft protocol specifications are published under the Open Specifications program. They are cited by their short identifier (the `[MS-XXXX]` document code).

| Identifier | Full Title |
|---|---|
| `MS-DTYP` | Windows Data Types |
| `MS-ERREF` | Windows Error Codes |
| `MS-LSAD` | Local Security Authority (Domain Policy) Remote Protocol |
| `MS-SAMR` | Security Account Manager (SAM) Remote Protocol |
| `MS-ADTS` | Active Directory Technical Specification |
| `MS-GPOL` | Group Policy: Core Protocol |
| `MS-GPREG` | Group Policy: Registry Extension Encoding |

Section references use the document's own numbering:

```markdown
SIDs use the binary format defined in MS-DTYP §2.4.2.

Conditional ACE bytecodes are specified in MS-DTYP §2.4.4.17.4
and MUST be byte-compatible.
```

> [!INFORMATIVE]
> Microsoft Open Specifications documents are available at `https://learn.microsoft.com/en-us/openspecs/`. The section numbers are generally stable across revisions, but the publication dates change. Cite the section number, not the URL or revision date.

## Unicode Standard

Format: `Unicode N.N` for the standard itself, or the filename for normative data files.

| Example | Meaning |
|---|---|
| `Unicode 16.0` | Version 16.0 of the Unicode Standard |
| `CaseFolding.txt` | The Unicode case folding data file |
| `Unicode 16.0 CaseFolding.txt, status S and C entries` | Specific entries used for case folding |

When a PSD references Unicode data files, it MUST specify the version and which entries are used:

```markdown
Case-insensitive comparison uses Unicode Simple Case Folding
(CaseFolding.txt, status S and C entries, Unicode 16.0).
```

## MessagePack

Format: `MessagePack` or `msgpack`.

```markdown
Event payloads are encoded using MessagePack (msgpack) as defined
by the MessagePack specification.
```

First use SHOULD include both the full name and the common abbreviation.

## systemd / sd_notify

Format: `sd_notify` (code-formatted as an API identifier).

References to systemd compatibility interfaces use the API name directly. No document citation is needed -- `sd_notify` is a well-known Linux API.

```markdown
Services signal readiness via `READY=1` sent through sd_notify.
```

## Other external sources

For external sources not listed above, the following rules apply:

1. Use the document's canonical short identifier if one exists.
2. Include the full title at first use.
3. Include section numbers when referencing specific content.
4. Do not rely on URLs as the primary identifier.

> [!INFORMATIVE]
> If a PSD references an external source frequently, consider adding it to this appendix in a future revision of PSD-001 for consistency across the corpus.
