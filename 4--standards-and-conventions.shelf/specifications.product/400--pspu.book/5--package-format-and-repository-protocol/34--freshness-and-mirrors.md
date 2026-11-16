---
title: Freshness and Mirrors
description: What a mirror is trusted for and what it isn't, why a sequence can't go backwards, why nothing expires, how a repository is served over HTTP, and how a consumer tries several base URLs in order.
---

## Mirrors

A **mirror** serves a copy of a repository. It is never trusted for
authenticity: everything it serves is signed or named by its hash. It is
trusted for freshness: a mirror MAY hold back a newer publication, as a
company testing updates before it rolls them out might want to.

## Going backwards

A consumer MUST keep, for each repository it fetches from, the highest
sequence (§5.32) it has seen, and MUST refuse a pointer file with a lower
one. Holding back never moves backwards; serving an older publication after
a newer one does, and only a broken or hostile mirror does that.

## Nothing expires

A snapshot is valid for ever: using one from years ago is valid, if not
wise. A pointer file carries the time it was signed so that a consumer can
show it, such as `signed 2026-11-01`, and a machine on a stale mirror can be
seen to be behind. A consumer MUST NOT refuse a pointer file for its age.

## Serving a repository

Every file of a repository but `repository` and `repository.sig` is named by
its hash and never changes, so a static web server can serve a repository as
it is, and a cache can keep every file but those two for ever.

## Serving over HTTP

A repository served over HTTP is named by a **base URL**: an `http` or
`https` URL with a host and no query or fragment. A consumer treats a base
URL that doesn't end in `/` as if it did. Each file of the repository is at
the base URL followed by the file's path in the repository's directory
(§5.30), such as `https://pkgs.peios.org/trees/sha256/<hash>`. A server
MUST serve a file's bytes unchanged as the body of a `200` response, and
need not list directories or answer range requests.

A repository served over HTTP MUST have a pointer file. Its directories
can't be listed, so a consumer takes its packages from its catalog, at the
identities the catalog gives, whether or not a key is configured (§5.29),
and doesn't read its refs.

A consumer reads the pointer file and its signature from one base URL, so
that a publication between the two reads can't give it a signature over
another pointer file. It MUST check the pointer file as §5.33 orders, and
every tree node, manifest and blob against its hash before it uses it. It
MUST check a blob before the blob is named in the store, so that a blob
that fails its check is never stored. Where the pointer file says the
blobs are compressed, a blob's hash is that of what it decompresses to
(§5.12).

## Base URLs tried in order

A machine can give a repository several base URLs (§5.35), each serving a
copy of the repository, such as a cache on its own network and then the
repository's own server. Each is a mirror of the repository. A consumer
reads each file from the first base URL that serves it:

- A base URL that can't be reached, or that answers with anything but the
  file, such as `404 Not Found` or a server error, is passed over for the
  next. The pointer file and its signature are passed over together.
- A file that fails its check, against the key or its hash, MUST be
  refused, and the consumer MUST NOT read it from another base URL. A
  mirror that serves the wrong file is broken or hostile, and the error
  is reported, not hidden.
- If no base URL serves the file, the consumer fails, saying why each
  didn't. If every base URL answers `404 Not Found` for the pointer file,
  the repository has none.

## Keeping what was read

A consumer MAY keep the tree nodes and manifests it reads from a repository
served over HTTP, under the paths the repository gives them, and read them
again from there. It MUST check one against its hash each time it reads
it. The pointer file and its signature are read from the repository each
time; what the consumer keeps of them is the sequence (§5.35).
