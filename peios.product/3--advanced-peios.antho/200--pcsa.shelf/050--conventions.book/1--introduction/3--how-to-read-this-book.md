---
title: How to Read This Book
description: The normative keywords used here, why the specification and manual halves carry different weight, and the order to read the chapters in.
---

## Normative keywords

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this
document are to be interpreted as described in RFC 2119. Their meaning
within a specification is defined in §2.1.

Text set off as a note is informative.

## The two halves carry different weight, deliberately

Chapters 2 and 3 govern specifications and are **normative throughout**.
A specification that violates one of their requirements is malformed,
and the requirement is stated as such.

Chapter 4 governs technical reference manuals and is deliberately
**lighter**. Most of it is SHOULD and MAY, and some of it is offered as
guidance carrying no normative weight at all. A manual is a description
of software rather than a contract, so prescribing its shape tightly
would be prescribing the shape of the software.

Two rules in chapter 4 are exceptions and are stated as MUST NOT,
because they are what makes the class a class rather than a matter of
taste: a manual carries no RFC 2119 keywords (§4.2), and a manual does
not narrate the difference between itself and a specification (§4.4).

Chapters 5 and 6 apply to both classes.

## Reading order

An implementer needs §2.1 and chapter 5, and nothing else.

An author needs the chapter for the class they are writing, then
chapters 5 and 6.

A reader trying to work out which class a document belongs to, or why a
given fact is documented in one place rather than another, wants §1.2.
