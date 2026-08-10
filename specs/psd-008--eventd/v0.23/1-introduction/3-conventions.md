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

## Timestamps

Unless a section explicitly says otherwise, timestamps are wall-clock time as
nanoseconds since the Unix epoch, in UTC. The v0.23 timestamp domain is the
range `0..=9223372036854775807` so every stored timestamp fits in a SQLite
`INTEGER` column. Sender-provided timestamps outside this range are invalid.
Query time literals that evaluate outside this range MUST produce an error.
Timestamp values in query results are encoded as msgpack integers in this same
nanosecond representation.

## Payload encoding

Structured data in the query interface and internal storage formats uses MessagePack (msgpack) as defined by the MessagePack specification, consistent with PSD-003.

## Canonical msgpack

Where this specification requires canonical msgpack byte encoding, eventd MUST
encode the decoded value as follows:

- Nil and booleans use the fixed msgpack singleton encodings.
- Integers use the shortest msgpack integer encoding that preserves signedness:
  non-negative values use positive fixint/`uint8`/`uint16`/`uint32`/`uint64`;
  negative values use negative fixint/`int8`/`int16`/`int32`/`int64`.
- Floats are encoded as msgpack `float64`. Finite values use their IEEE-754
  binary64 representation. Positive and negative infinity use the normal
  binary64 infinity encodings. Any NaN value is encoded as the single quiet NaN
  bit pattern `0x7ff8000000000000`.
- Strings, binary values, arrays, and maps use the shortest length-prefix form
  capable of representing the value length.
- Arrays encode each element recursively in order.
- Maps encode keys and values recursively. Map entries are sorted by the
  canonical encoded key bytes; ties are sorted by canonical encoded value bytes.

Canonical msgpack is used only where explicitly required for deterministic
storage or ordering. It does not change the accepted input encoding for KMES
payloads or ingestion datagrams.
