---
title: Clause Numbering
---

## Definition

A clause is a specific normative statement within a PSD. Clauses are the fundamental unit of traceability -- they are what code implements, tests verify, and coverage matrices track.

## Which statements are clauses

Every statement using a normative keyword (MUST, MUST NOT, SHALL, SHALL NOT, SHOULD, SHOULD NOT, REQUIRED) in its RFC 2119 sense is a clause.

Statements using MAY or OPTIONAL are clauses if the behavior they describe needs to be tested or referenced. They MAY be excluded from clause counting if the behavior is trivial.

Informative text (see §5.2) is never a clause.

## Numbering

Clause numbers are positional and implicit. They MUST NOT be written inline in the specification text. A clause's number is derived by counting normative statements sequentially within the most specific section (the deepest heading level that contains them).

> [!INFORMATIVE]
> Example: if §3.2.1 contains three normative statements, they are clauses (1), (2), and (3). A reader or tool determines the number by counting from the top of that subsection. The author does not write "(1)" in the text.

If a section has subsection headings, clause numbering restarts in each subsection.

> [!INFORMATIVE]
> Example:
>
> ```markdown
> ## Overview
>
> An ACL MUST contain at least one ACE.
>
> ## Ordering
>
> ACEs MUST be sorted by type before evaluation.
>
> The sort order MUST place deny ACEs before allow ACEs.
> ```
>
> The first statement under "Overview" is `§N.M.1(1)`. The two statements under "Ordering" are `§N.M.2(1)` and `§N.M.2(2)`. Numbering restarts because they are in different subsections.

## When to cite at clause granularity

Most references SHOULD cite at the section or subsection level (`§3.2` or `§3.2.1`). Clause-level citations (`§3.2.1(3)`) SHOULD be reserved for cases where a subsection contains multiple normative statements and the reference needs to identify one specifically.

## Stability

Within a `final` version, the document structure MUST NOT change. Clause numbers are frozen because the text they derive from is frozen.

When a new version restructures content, clause numbering shifts naturally with the text. The changelog (see §7.1) MUST document clause changes between versions so that consumers of the previous version's citations can update their references.
