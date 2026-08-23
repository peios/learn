---
title: Roles
description: A multi-party specification names its roles and states every requirement against a role rather than a program — and conformance follows the roles.
---

A specification with more than one party MUST name its roles in its
scope article, and MUST state every requirement against a role rather
than against a program.

A role is a position in an interaction, not a piece of software. One
program frequently occupies several — a repository operator is usually
also a package producer, and a daemon that answers one protocol may
consume another.

## Why the distinction is load-bearing

Naming a program in a requirement makes the requirement untestable
against anything else, which defeats the purpose of writing the
specification down. The whole reason a contract is published is that
somebody other than the current implementation may satisfy it.

## Enumerating roles

A chapter's scope article SHOULD present its roles as a table giving,
for each, the obligation it carries:

| Role | Obligation |
|---|---|
| Producer | Builds the artifact. Everything the artifact contains is a producer obligation. |
| Consumer | Validates and applies it. Every validation and rejection rule binds the consumer. |

Two or three roles is typical. A specification finding itself with six
has probably merged two interactions that want separate chapters.

## Conformance follows the roles

Because requirements attach to roles, a conformance article (§3.4)
states what each role must do, separately. A reader implementing one
side needs to know which requirements are theirs without reading the
other side's.
