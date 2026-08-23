---
title: Validating a Log Record
description: The three scopes of silent failure — the whole datagram, one record, or one field — and what a collector adds on the way in.
---

Every failure on this channel is silent (§3.4). What differs between
failures is *how much* is lost: the whole datagram, one record, or only
one field.

## The three scopes of failure

**The datagram is discarded** when it cannot be resolved into records at
all:

- it is not valid MessagePack
- it decodes to something that is neither a map nor an array of maps
- the kernel reported it truncated (§3.6)

**One record is discarded**, and the others in the same datagram are
still processed, when the record itself is unusable:

- a required field is absent
- a required field has the wrong type — `origin` an integer, say
- `origin` is the empty string
- the map contains a duplicate top-level key

**One field is ignored**, and the record is still stored, when an
optional field is unusable:

- `timestamp` is not an integer, is negative, or is outside the
  timestamp domain (§3.5)
- `job_id` is not binary, or is binary of a length other than 16

A collector MUST implement all three scopes as stated. In particular it
MUST NOT discard a record because an optional field was malformed: a
producer with a broken clock or a mangled correlation key still has a
log line worth keeping, and the field it got wrong is the field of least
value in the record.

## Duplicate keys

A record map carrying the same top-level key twice MUST be discarded.

A collector MUST NOT resolve the duplicate by taking the first or the
last. MessagePack decoders differ on which they keep, and the fields
here are entirely producer-controlled, so a rule that depended on
decoder behaviour would let a producer choose which of two `origin`
values a given collector saw. Discarding is the only answer that is the
same everywhere.

## Batches

A batch is validated **per record**. A malformed record in a batch MUST
NOT cost the valid records beside it.

A producer SHOULD batch under sustained load. Batching amortises the
syscall over many records, and the ceiling (§3.6) is per datagram, so a
batch is also the only way to use the channel's capacity efficiently.

The encoded datagram, batched or not, MUST NOT exceed the ceiling. A
producer that batches without bounding the encoded size will eventually
build a datagram that is discarded whole — which is the one case where
batching loses more than sending singly would have.

## What a collector adds

A collector supplies the boot ID (§3.2) and, when the record omitted
`timestamp`, its own clock reading at receipt. It MUST NOT alter any
other field, and MUST store `message` byte-for-byte as given.

A collector MUST NOT parse `message`. If the text happens to be JSON, or
logfmt, or anything else structured, that is the producer's business:
this interface carries lines, and a producer with structured data to
record emits an event instead (§3.4).
