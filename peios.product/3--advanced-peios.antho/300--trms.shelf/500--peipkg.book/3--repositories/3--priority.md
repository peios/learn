---
title: Priority
description: Every repository carries a numeric priority deciding candidate selection and tie-breaks — and what priority pointedly is not.
---

Every configured repository carries a numeric priority. A lower number
is a higher priority.

Priority decides two things: which repository's candidate the resolver
prefers when several satisfy the same dependency (§4.3), and which of
two repositories counts as the more trusted when a cross-repository
guard fires (§3.7).

## What priority is not

peipkg has no notion of an "official" repository as a distinct kind.
Wherever the format's rules speak of a non-official repository acting
against an official one, peipkg substitutes a comparison of numeric
priorities. The two coincide exactly when the official repository has
been given the lowest number — which is the recommended configuration
but not something peipkg enforces, since every repository including the
official one is created at the same default priority.

## Local files

A package supplied as a local file rather than fetched from a repository
carries an empty repository name and priority zero. Zero is numerically
the highest priority available, so a local file outranks every
configured repository in candidate selection, and the same-repository
preference of §4.3 is permanently inert for it.
