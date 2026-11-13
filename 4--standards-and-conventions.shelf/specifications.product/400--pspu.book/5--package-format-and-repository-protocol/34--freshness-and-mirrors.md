---
title: Freshness and Mirrors
description: What a mirror is trusted for and what it isn't, why a sequence can't go backwards, why nothing expires, and how a repository is served as it is.
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
it is, and a cache can keep every file but those two for ever. This version
specifies repositories as directories only; the mapping to URLs is reserved
for a future version.
