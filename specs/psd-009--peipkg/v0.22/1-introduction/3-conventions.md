---
title: Conventions
---

This specification conforms to PSD-001.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in
this specification are to be interpreted as described in
RFC 2119.

JSON documents specified herein conform to RFC 8259. Field
names are lowercase with underscores between words
(`schema_version`, not `schemaVersion`). Unknown fields MUST be
ignored on parse to permit forward-compatible extension (with
the explicit exception of the signature envelope, §5.1.3,
which mandates strict parsing). Field order is not significant.

JSON consumers in this specification MUST harden their
parsers against malformed and adversarial input:

- Duplicate keys in any object MUST cause the document
  to be rejected. Parsers that silently take first-wins or
  last-wins are not compliant.
- Integer fields MUST fit in unsigned 64-bit range and
  MUST NOT use exponent notation.
- JSON nesting depth MUST be capped at 64; documents
  exceeding this depth MUST be rejected.
- String values MUST NOT exceed the document size limit
  applicable to their containing artifact (per the
  resource-limit table where one applies).
- Unicode escapes within strings MUST resolve to a valid
  Unicode code point per RFC 8259 §7.

Hash values are encoded in lowercase hexadecimal unless
otherwise stated. Hash algorithms are identified by their
IANA-registered names (SHA-256, BLAKE3).

Signatures use Ed25519 as defined in RFC 8032 unless otherwise
stated. Signature values are encoded in base64 (RFC 4648 §4)
without padding.

Strings are UTF-8 encoded (RFC 3629). String comparisons in
this specification use byte-for-byte equality unless otherwise
stated.

URLs follow RFC 3986. Relative URLs in repository indexes are
resolved against the repository descriptor URL.

Compression uses the Zstandard format (RFC 8478). The
specification does not constrain compression level; producers
SHOULD use a level that yields reproducible output for a given
input.
