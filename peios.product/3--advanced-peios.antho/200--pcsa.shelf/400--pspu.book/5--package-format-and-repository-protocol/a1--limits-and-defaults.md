---
title: Limits and Defaults
description: Every limit as a minimum conformance figure — package structure, manifest arrays, identity, documents, decompression and repository defaults.
---

Every limit below is a **minimum conformance** figure: a consumer MUST
process a package or document whose characteristics fall within it, and
MUST reject one that exceeds it.

A consumer MAY raise a limit through operator configuration, but MUST
NOT raise one silently: an operator-tuned value SHOULD be logged and
surfaced in diagnostic output.

A producer SHOULD stay well below these figures. They exist to bound a
consumer's resource use when processing a maliciously crafted package,
not to describe the scale of a well-formed one.

## Package structure

| Limit | Maximum |
|---|---|
| Payload entries | 100,000 |
| `.peipkg/manifest.json` size | 16 MiB |
| `.peipkg/files.json` size | 64 MiB |
| `.peipkg/signature` size | 64 KiB |
| Single payload path component (UTF-8 bytes) | 255 |
| Complete payload path (UTF-8 bytes) | 4096 |
| Path nesting depth (components) | 256 |
| Single claim path (UTF-8 bytes) | 4096 |

## Manifest arrays

| Limit | Maximum |
|---|---|
| `dependencies` | 10,000 |
| `optional_dependencies` | 10,000 |
| `conflicts` | 10,000 |
| `provides` | 10,000 |
| `replaces` | 1,000 |
| `sd_overrides` | 100,000 |
| Single `sd_override` decoded `sd` length | 64 KiB |
| Slots per `claims` field | 64 |
| Claim paths materialised per role | 256 |

The claim-path figure is a **materialisation** limit, not a manifest
limit: it bounds the union computed across every installed package
declaring a path for that role, which is the quantity an adversary
controls by installing many consumer-only packages.

## Identity

| Limit | Value |
|---|---|
| Package name length | 2 to 64 characters |
| Virtual name length | 2 to 128 characters |
| Architecture identifier length | at most 16 characters |

## Documents

| Limit | Value |
|---|---|
| JSON nesting depth | 64 |
| Integer field range | unsigned 64-bit |

## Decompression

| Bound | Value |
|---|---|
| Compressed overrun allowance over `size_compressed` | the lesser of 1% or 16 MiB |
| Decompressed overhead allowance over `size_installed` | 320 MiB |
| Absolute decompressed cap | 4 GiB (default; operator-tunable) |

## Repository defaults

| Default | Value |
|---|---|
| Maximum trusted age | 30 days |
| Maximum trusted age producing a warning | above 180 days |
| Maximum index staleness | 90 days |
| Maximum index staleness producing a warning | above 365 days |
| Revoked key retention | at least 1 year |
| Repository priority | positive integer; lower is higher priority |
| Default signature policy for a new repository | `required` |
