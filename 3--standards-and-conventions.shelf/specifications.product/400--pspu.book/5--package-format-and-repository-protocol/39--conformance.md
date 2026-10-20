---
title: Conformance
description: Every requirement collected by role — producer, repository and consumer — and what conformance deliberately does not require.
---

## Producer

A conforming producer:

- emits packages satisfying §5.10 through §5.17: the container, every
  determinism rule, the internal layout, the payload path constraints,
  the install destinations, the triplet rule, the entry rules, and the
  symlink rules;
- emits a manifest satisfying §5.18, with names, versions, and
  architectures satisfying §5.3 through §5.8;
- emits a files manifest satisfying §5.25, covering exactly the
  regular-file payload entries, with `size_installed` equal to the sum
  of its sizes;
- declares relationships satisfying §5.21, sorted and unique within each
  field, using the derived-capability names of §5.22 where a capability
  is machine-derived;
- declares claims satisfying §5.23, with every target a payload path of
  its own;
- declares side effects satisfying §5.24, declaring each that its
  payload requires and none that it does not;
- signs packages satisfying §5.28, or emits them unsigned knowing they
  will be accepted only under a permissive policy.

## Repository

A conforming repository:

- publishes a descriptor satisfying §5.31 with a valid detached
  signature, and serves the public key file of every key the descriptor
  declares, including revoked ones (§5.32);
- publishes an active index satisfying §5.33 and an archive index
  satisfying §5.35, each with a valid detached signature, each derived
  directly from package manifests;
- increases `index_version` strictly on every publication (§5.34);
- retains every version it has ever advertised, and removes a pruned
  package from both its archive index and its storage (§5.35);
- serves everything over HTTPS at the URLs its descriptor declares
  (§5.36).

## Consumer

A conforming consumer:

- verifies a package by §5.26 in full, including the transaction-wide
  rule and the path-resolution rule, before installing anything;
- enforces the decompression bounds of §5.27 continuously, from the
  index-declared sizes;
- verifies signatures by §5.30, against a trust set scoped to the
  originating repository, honouring key status before any cryptography;
- rejects a package violating any rule of §5.10 through §5.25 — the
  determinism rules and the payload rules included, on the way in, not
  only on the way out;
- enforces the freshness and rollback rules of §5.34 on both indexes,
  and never lowers a recorded floor except by removing the repository;
- establishes and maintains trust by §5.37, including the fingerprint
  comparison, the per-operation warnings, the maximum trusted age, the
  orphan rules, and the two cross-repository guards;
- enforces the security descriptor policy of §5.20;
- invokes side effects by §5.24, once per transaction, by fixed absolute
  path, with a cleared environment, against the root the transaction
  acted on;
- materialises claims by §5.23, and never at a path an installed package
  owns.

## What conformance does not require

A conforming consumer is not required to resolve dependencies by any
particular algorithm, to store its state in any particular form, to
recover from an interrupted operation by any particular mechanism, or to
offer any particular command surface. Those are its own design, and
§5.1 places them outside this chapter deliberately.

What it *is* required to do is reach the same answer as any other
conforming consumer about whether a given package satisfies a given
dependency (§5.21), and about which of two versions is newer (§5.6).
Those two questions are the ones a producer's declarations depend on,
and they are frozen.
