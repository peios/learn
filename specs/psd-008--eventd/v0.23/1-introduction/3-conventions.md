---
title: Conventions
---

## Normative keywords

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this specification are to be interpreted as described in RFC 2119.

## Section references

Section references within this specification use the `§` addressing scheme defined in PSD-001. References to other PSDs use the `PSD-NNN §x.y.z(n)` citation format.

## Byte order

All multi-byte integers in wire formats and storage formats defined by this specification are little-endian, consistent with PSD-003.

## String encoding

All strings in wire formats and storage formats defined by this specification are UTF-8 encoded.

## Payload encoding

Structured data in the query interface and internal storage formats uses MessagePack (msgpack) as defined by the MessagePack specification, consistent with PSD-003.
