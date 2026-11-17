---
title: Resolution
description: Choosing a version of each package that requests need, the order needs are settled in, index requests, yanked and deleted versions, and what makes an error.
---

**Resolution** chooses one version of each package that a set of requests
needs, from one or more artifact directories, for one architecture (§5.8).

## Requests

A request asks for a package by name, or for a capability (§5.4), with a
constraint (§5.7). It MAY also name an index or channel of a repository
(§5.30), written after the name with `#`:

```text
se.curl.curl
se.curl.curl >= 8.20
se.curl.curl#stable
se.curl.curl#stable >= 8
libc.so.6 >= 2.34
```

An exact package ID, `name@version`, asks for exactly that version and its
spelling, and is settled before any other request. It can't name an index.

## Order

Each need, a request or a dependency or requirement of a package chosen, is
settled once, in order:

1. Needs for packages by name are settled before needs for capabilities, at
   every step: first the requests, then the dependencies of what they chose,
   and only when no dependency is left, the first capability waiting.
2. Within each kind, needs are settled in the order of the requests, then
   in the order of each manifest's tables.

A package not chosen yet is chosen at the newest version that satisfies the
need (§5.6). A capability that a chosen package provides at a satisfying
version needs nothing more. Otherwise the one package name that provides it
is chosen, at its newest satisfying version.

Nothing chosen is reconsidered. The same requests against the same packages
MUST always give the same choice.

## Errors

A consumer MUST refuse a resolution, naming the need and what it met, when:

- nothing satisfies a need;
- a package already chosen doesn't satisfy a later need, which is a
  conflict: the error says what was chosen and why, and whether another
  version would have satisfied both;
- several package names provide a capability that none chosen does, since
  the request must choose one by name;
- the version chosen is spelt two ways, such as `1.0~a-1` and
  `1.0~alpha-1`, which no constraint can tell apart.

## Index requests

A need from an index is satisfied only by a version that index holds, for
the resolution's architecture. A package chosen for it passes the index on:
its dependencies and requirements are settled from the same index too. A
request for an exact version, or for another index, is an exception, and
MUST still satisfy every need on its package.

A request naming an index that no artifact directory among those given
publishes MUST be refused.

The closure's inventory records the index of each request that names one,
but not the index a dependency or requirement inherited (§5.25).

## Yanked and deleted versions

A version a repository has yanked (§5.36) satisfies only a need for exactly
that version. A request that only a deleted version would have satisfied
MUST be refused, giving the deletion's reason from the repository's
catalog.

## Signed repositories

When a repository's identity is configured (§5.35), its packages are
candidates
only if its catalog, reached from its signed pointer file (§5.33), lists
them, and only at the identity the catalog gives. A ref that names another
identity MUST be refused. The refs of a repository without a configured
identity are taken as they are.

A repository served over HTTP has no refs a consumer can list. Its packages
are those its catalog lists, at the identity the catalog gives, with or
without a configured identity (§5.34).

## Resolving from summaries

A consumer resolving from a repository served over HTTP MUST NOT read a
manifest to do so. It reads only what resolution reaches: for a package
name, its node in the catalog and the summary of each of its versions
(§5.31); for a capability, its node in the provides tree, and each package
name there in the same way. What a summary says replaces what the manifest
would. A version a name's node gives as yanked or deleted is treated as
§5.36 says, whatever the provides tree lists. The manifests are read when
the packages chosen are fetched, and each is checked against the summary
it was chosen by.

The packages chosen are the same as resolving from the manifests would
choose.
