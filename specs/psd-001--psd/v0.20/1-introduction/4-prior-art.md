---
title: Prior Art
---

The PSD conventions draw on established practices from several specification ecosystems.

## IETF RFCs

The RFC series provides the model for permanent numeric identifiers (RFC 2119, RFC 7230) and the use of normative keywords. PSDs adopt RFC 2119 keywords directly.

PSD numbering differs from RFC numbering in that PSD numbers identify specifications across versions, while RFC numbers identify individual documents (a revision of an RFC receives a new number). This reflects the Peios versioning model where versions are refinements, not replacements.

## ISO and W3C standards

The hierarchical section addressing scheme (`§chapter.section.subsection`) and the separation of clause numbering from section numbering follow conventions used in ISO standards and W3C recommendations.

## Microsoft specifications

The Peios spec corpus is heavily influenced by Microsoft protocol and platform specifications (MS-DTYP, the Windows SDK documentation). The compatibility/parity sections in existing Peios specs follow the pattern of documenting intentional divergences from a reference implementation, which is standard practice in the Microsoft Open Specifications program.

## Existing Peios conventions

Many of the conventions formalised here were already in use across the KACS, LCS, loregd, peinit, and KMES specs before this specification was written. This specification codifies those conventions rather than inventing new ones, and extends them with PSD numbering, clause addressing, changelogs, and lifecycle states that were previously absent.
