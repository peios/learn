---
title: Adding a Repository
description: The trust ceremony where an operator decides a key speaks for a URL — the two forms, bootstrapping the freshness floor, and fetching keys before verifying.
---

Adding a repository is the trust ceremony of PSPU §5.37: the moment an
operator decides that a particular key speaks for a particular URL.

## The ceremony

peipkg fetches the descriptor and its detached signature, fetches the
public key for each anchor fingerprint the operator supplied, checks
each fetched key against the fingerprint that named it, and verifies the
descriptor's signature against those anchor keys and only those. On
success it records the descriptor's full key list, with statuses, as the
repository's trust state.

If no key matching an anchor verifies the descriptor, the add is
refused. The error names the condition but not the fingerprints
involved, which is the diagnostic a transcription error most needs.

peipkg does not display the fetched fingerprint alongside the supplied
one, and does not prompt for confirmation before recording trust. A
mismatch is caught — an anchor that does not match cannot verify
anything — but the operator is not shown the two side by side.

## Two forms

`peipkg repo add <name> <url> --anchor <fingerprint>` is the interactive
form: everything comes from the command line.

`peipkg repo add <name>` is the configured form: the URL, the anchors,
and the policy are already on disk, placed there by an image or a
configuration manager, and the command performs the ceremony against
them. When the ceremony fails for a repository whose configuration file
already existed, that file is deliberately left in place — the operator
put it there, and deleting it would discard their configuration over a
transient network failure.

## Bootstrapping the freshness floor

The first index a repository serves establishes the floor that §3.4's
rollback protection enforces from then on. A repository that publishes a
minimum acceptable index version alongside its anchors lets peipkg
refuse an add whose first index falls below it; without one the floor is
whatever the first fetch returned.

Adding a repository writes the floor unconditionally, including for a
repository already configured. Because the configured form of the
command needs no arguments and reads as idempotent, re-running it is the
route by which a recorded floor is replaced by whatever the current
fetch returns.

## Fetching keys before verifying

The descriptor names the URLs its keys are published at, so peipkg reads
an unverified document to know where to fetch from. It fetches
every key the descriptor declares, not only those matching the supplied
anchors.

## Official anchors

The anchors for the official repository come from a file installed by
the base system, outside any package. Bootstrap trust is a property of
the image rather than of the package format: peipkg relies on the
anchors being present when it first runs.
