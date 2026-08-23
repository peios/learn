---
title: Trust Anchors
description: A key fingerprint supplied out of band is the root of the whole repository trust model — where anchors come from, and what that means.
---

A trust anchor is a key fingerprint an operator supplies out of band, and
it is the root of everything the repository trust model builds on
(§3.2).

## Where they come from

Two places, and only two: the `--anchor` option at repository-add time,
and the trust-anchors key of a repository's configuration file.

The intended third place — a file installed by the base system, outside
any package, carrying the official repository's anchors — does not
exist, and nothing looks for one.

## What that means

The configuration directory those files live in is the **writable**
local tier. So the official repository's anchors, when an image ships
them, sit in mutable local state protected by that directory's security
descriptor rather than in a read-only base-system location.

The configured form of `repo add` performs the full trust ceremony
against anchors read from that directory. Anything able to write there
can substitute the official repository's anchors before the ceremony
runs.

Placing a rogue repository configuration is not by itself an escalation
— adding a repository is an operator action, and the security descriptor
on the directory is what decides who may take it. Substituting the
anchors of a repository the operator believes is already trusted is a
different thing.

## The redundancy that is planned

The intended end state distributes anchors redundantly: the base-system
file, plus a registry key populated at first boot, with peipkg
cross-checking every available source byte for byte, refusing repository
operations on disagreement — with the base-system file authoritative —
and refusing on a missing source in a rescue-media boot.

The model is additive: once the registry source exists, the cross-check
applies without changing the file's role as authoritative.

Neither leg is present today. The registry source is correctly inert,
since the registry it would live in is not yet available. The
base-system file it would be checked against is simply absent.
