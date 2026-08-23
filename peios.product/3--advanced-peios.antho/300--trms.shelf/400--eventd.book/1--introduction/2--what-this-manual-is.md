---
title: What This Manual Is
description: A TRM proposal for software that has not been written — what in it is a contract, and how versions and constants are treated.
---

This is a **Technical Reference Manual Proposal**. eventd has not been
written.

Everything in this manual is therefore a description of a design rather
than of an artifact: the schemas, the thread structure, the algorithms,
the constants and the failure behaviour are what eventd is specified to
do, not observations of what it does. Nothing here has been checked
against an implementation, because there is none to check against.

It is written in the indicative mood, exactly as a reference manual for
existing software would be, and it makes no conformance demands. When
the code lands, this document becomes eventd's Technical Reference
Manual — corrected wherever the implementation and the design turn out
to disagree, and with no change in kind. That is the whole reason for
the proposal form: a design document that will be read as a manual is
better written as one from the start.

The distinction a reader needs to keep is that **a TRM's authority comes
from the software and this one has none of that yet**. Where a statement
here is surprising, it is a design decision that has not survived
contact with an implementation.

## What is a contract and what is not

eventd's three external interfaces are specified separately, in PSPU §3:
the log ingestion channel, the metric ingestion channel, and the query
channel with its query language. Those are contracts, binding on
anything that speaks them, and they are normative where this manual is
not.

This manual covers the other side of that boundary — how eventd fulfils
them:

- how it consumes KMES and what it does when it falls behind (§2)
- what it stores, in what schema, and how it accelerates and expires it
  (§3, §4, §5)
- how a query in the language of PSPU §3 becomes an answer (§6)
- how access decisions are reached (§7)
- how it starts, stops, and behaves when something breaks (§8, §9)

Where a chapter touches the contract, it references PSPU §3 rather than
restating it, and describes only what eventd adds.

The access control **mechanism** is here rather than in PSPU because it
is behind the abstraction: a client sees only which records and fields
it received (PSPU §3.28). The field GUID derivation in §7.3 is the one
part of it that a third party may need to reproduce — an administrator
writing a Security Descriptor computes the same GUIDs — and it is a
candidate for promotion into a specification if that turns out to be a
common thing to do.

## Versions and constants

Constants, configuration keys and catalogues are collected in the
appendices at the end of the manual, so that a chapter's reference
material does not interrupt the prose that explains it. Where an
appendix defines a value, the body references it rather than repeating
it.
