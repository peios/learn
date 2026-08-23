---
title: Structure
description: How a manual is shaped — the introduction, body chapters, a failure-modes chapter and appendices — as guidance rather than a template.
---

A TRM's chapter structure follows the component rather than a template.
The conventions below are what has worked, offered as guidance.

## The introduction

A manual SHOULD open with an introduction containing:

| Article | Purpose |
|---|---|
| Overview | What the component is, and what is unusual about it |
| What This Manual Covers | And what is covered elsewhere, naming where |
| Terminology | Terms specific to the component, delegating the rest |
| Compatibility | Versions, architectures, and what interoperates |

The overview article is the most valuable page in the book and the one
most often written last and least. It SHOULD say what is *surprising*
about the component — the two or three decisions that would not be
guessed from the name — rather than restating the component's purpose in
a paragraph.

## Body chapters

Ordered so that a reader following the component's own flow reads them
in order: what it is made of, what it does, in the sequence it does it.

## A failure-modes chapter

A manual SHOULD close with a chapter describing what goes wrong: the
common failures, what each looks like from outside, what signal is
available, and how to get back to a known state.

This is the chapter readers arrive at from a search engine at two in the
morning, and it is the one most often omitted. A manual that documents
every success path and no failure path has documented the easy half.

## Appendices

Consolidated reference material: constants, paths, on-disk state,
configuration keys, event types. See §6.1.

## Length is not a virtue, but exhaustiveness is

A manual SHOULD document the edge cases. The odd interaction, the
counter-intuitive default, the thing that happens only when two features
meet — those are why the manual exists. A summary of the happy path is
already in the component's README.
