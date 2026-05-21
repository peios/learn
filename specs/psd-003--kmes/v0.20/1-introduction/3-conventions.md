---
title: Conventions
---

## Normative keywords

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this specification are to be interpreted as described in RFC 2119.

## Byte order

All multi-byte integers in the event header and ring buffer metadata page are little-endian. The ring buffer magic field is a fixed byte sequence compared byte-by-byte, not an integer.

## String encoding

Event type strings are UTF-8 encoded. No case folding or normalization is applied -- event types are compared as raw byte sequences.

## GUID encoding

Identity GUIDs in the event header use the Microsoft GUID binary format (16 bytes): a 4-byte little-endian `Data1`, a 2-byte little-endian `Data2`, a 2-byte little-endian `Data3`, and an 8-byte `Data4` array. The format is defined in PSD-002. KMES treats GUIDs as opaque 16-byte values -- it copies them from KACS accessors without interpreting the internal structure.

## Payload encoding

Event payloads are encoded using MessagePack (msgpack) as defined by the MessagePack specification. KMES does not interpret payload contents.
