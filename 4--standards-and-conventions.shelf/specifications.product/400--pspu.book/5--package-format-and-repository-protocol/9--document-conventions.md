---
title: Document Conventions
description: The rules every JSON artifact in this chapter obeys — parser hardening, hashes, signatures, strings, URLs and compression.
---

Every artifact this chapter defines — the manifest, the files manifest,
the signature envelope, the repository descriptor, and both indexes — is
a JSON document. The rules below apply to all of them.

## JSON

Documents conform to RFC 8259 and are UTF-8 encoded (RFC 3629). Field
names are lowercase with underscores between words: `schema_version`,
never `schemaVersion`. Field order is not significant.

Unknown fields MUST be ignored on parse, so that the format can be
extended compatibly (§5.38). The signature envelope (§5.28) is the one
exception, and mandates strict parsing.

## Parser hardening

A consumer's JSON parser processes attacker-supplied input. It MUST
therefore enforce the following, on every document defined in this
chapter:

- **Duplicate keys in any object MUST cause the document to be
  rejected.** A parser that silently takes first-wins or last-wins is
  not conformant.
- Integer fields MUST fit in the unsigned 64-bit range and MUST NOT use
  exponent notation.
- Nesting depth MUST be capped at 64; a document exceeding that depth
  MUST be rejected.
- A string value MUST NOT exceed the document size limit applicable to
  its containing artifact (§5.A).
- A Unicode escape within a string MUST resolve to a valid code point
  per RFC 8259 §7.

> [!NOTE]
> Duplicate-key rejection is the load-bearing rule of the list. A parser
> that takes last-wins and a parser that takes first-wins disagree about
> what a document says, which means the bytes a producer signed and the
> bytes a consumer acts on can differ while every signature still
> verifies. Several widely used JSON libraries take last-wins silently;
> conformance requires the rejection to be added deliberately.

## Hashes

Hash values are encoded in lowercase hexadecimal unless stated
otherwise. Hash algorithms are identified by their IANA-registered names
(`sha256`, `blake3`).

## Signatures

Signatures use Ed25519 as defined in RFC 8032 unless stated otherwise.
Signature values are encoded in base64 (RFC 4648 §4) **without padding**.
A base64 value carrying padding MUST be rejected.

## Strings

String comparison uses byte-for-byte equality unless stated otherwise.

## URLs

URLs follow RFC 3986. Relative URLs in a repository index are resolved
against the repository descriptor's URL (§5.36).

## Compression

Compression uses the Zstandard format (RFC 8478). This specification
does not constrain the compression level.
