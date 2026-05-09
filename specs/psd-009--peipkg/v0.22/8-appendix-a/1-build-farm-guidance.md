---
title: Build Farm Guidance
---

> [!INFORMATIVE]
> This appendix provides non-normative guidance for
> operators of build farms that produce peipkg packages.
> Nothing in this appendix is required for conformance to
> the package format. The normative requirements on
> producers appear in chapters 3 through 6.

## Reproducibility

A reproducible build farm produces byte-identical packages
from the same inputs across runs and operators. Achieving
this requires controlling everything the build process can
observe: timestamps, file ordering, locale, environment
variables, ambient filesystem state, build paths.

The format's determinism rules (§3.1.4) are necessary but
not sufficient: they specify what the package must look
like, not how to produce it. Operators are expected to use
established techniques:

- **SOURCE_DATE_EPOCH**: a single epoch timestamp that
  every build tool reads to set timestamps in outputs.
  The Reproducible Builds project's conventions apply.
- **Sealed build environments**: container or VM-based
  builds where the full build dependency closure is
  pinned (specific versions of compilers, libraries,
  build scripts). The dependency closure is itself a
  build input that determines the output.
- **Locale and time zone normalisation**: builds run in
  `LC_ALL=C` and `TZ=UTC` to suppress locale-dependent
  output ordering and time formatting.
- **Build path normalisation**: tools like `BUILD_PATH`
  manipulation or `RECORDED_BUILD_DIR` keep absolute
  paths from leaking into compiled binaries (debug info,
  embedded paths).

The `build.farm_id` and `build.source_ref` fields in the
manifest (§3.3.4) record the producer and inputs. A
recipient who has access to the same inputs and the same
farm's tooling can re-run the build and verify output
matches.

## Farm identifiers

The `build.farm_id` value is producer-defined. Conventions
that work well in practice:

- A short organisational identifier plus a generation
  number: `peios-build-1`, `peios-build-2`. The
  generation number bumps when the farm's tooling or
  hosting changes substantively.
- A combination of organisation and farm-specific role:
  `peios-build-amd64`, `peios-build-arm64`.

Farm identifiers should not encode information that
changes per-build (such as a build sequence number); they
identify the farm, not the build.

A farm identifier should be stable across many builds.
Changing the farm identifier without an underlying
operational change defeats reproducibility verification:
the same package built on the same farm should report the
same `farm_id`.

## Source references

The `build.source_ref` field is producer-defined. The
recommended form is a machine-resolvable reference that
fully identifies the build inputs:

```
git+https://git.peios.org/sources/nginx#refs/tags/v1.26.2-3
```

The form's components:

- A scheme identifying the source-control system (`git+`,
  `hg+`, etc.).
- An HTTPS URL for the repository.
- A fragment identifier specifying an exact ref (a tag,
  commit hash, or annotated reference).

Tags are preferred over commit hashes for human-readable
provenance. Annotated tags are preferred over lightweight
tags for cryptographic stability.

A source reference SHOULD be sufficient by itself to
recover the inputs. References that depend on transient
or mutable state ("the latest from main", a relative
date) are not reproducible and SHOULD be avoided.

## Signing key custody

Signing keys grant the holder the ability to publish
packages indistinguishable from official packages. Their
protection is the most security-critical operational
concern of a build farm.

Recommended practices:

- **Hardware security modules**: signing operations occur
  inside an HSM, where the private key never leaves the
  device. Hardware keys (YubiKey, Nitrokey) suffice for
  smaller operations; HSMs (CloudHSM, Nitro Enclaves) for
  larger.
- **Threshold signing**: split the signing key across
  multiple parties such that no single party can produce
  a signature alone. Schemes like FROST, GG20, or simpler
  Shamir-based custody.
- **Air-gapped signing**: the signing operation runs on a
  network-isolated machine. Packages are physically or
  cryptographically transferred for signing.
- **Key rotation schedule**: rotate signing keys
  periodically (annually or after major operational
  changes), even without suspicion of compromise. Use the
  rotation flow in §5.2.6.
- **Key fingerprint publication**: publish trust anchor
  fingerprints through multiple independent channels
  (project website, OS image, documentation, package
  manager preconfiguration) so users can cross-check.

These practices apply equally to the official Peios
project's keys and to operators of custom repositories.

## Build attestations

Future versions of this specification may introduce
formal build attestation as a sibling artifact published
alongside packages (see §6.4.4 sibling artifacts).

Attestations describe how a package was built: the
build environment, the inputs (resolved to specific
versions and hashes), the timestamp, and the attestation
producer's signature. Attestations enable consumers (or
auditors) to verify reproducibility independently of the
producer.

The SLSA (Supply-chain Levels for Software Artifacts)
framework defines a graduated set of attestation
practices. SLSA Level 3 corresponds approximately to:

- Signed build provenance describing the inputs.
- Hermetic, sealed build environments.
- Build platform integrity (the platform that ran the
  build is itself trustworthy and tamper-resistant).

Operators of significant repositories (especially the
official Peios project) SHOULD aim for SLSA Level 3 or
equivalent practices, even though attestations themselves
are not yet a normative artifact in this specification.

## Pre-publication checks

Before publishing a built package, the build farm SHOULD
verify:

- The package's hash matches the recorded hash.
- The signature verifies against the publishing key.
- The package can be installed cleanly in a fresh test
  environment.
- The dependency declarations are consistent (no
  references to non-existent packages, no impossible
  version constraints).
- Re-running the build from the same inputs produces a
  byte-identical package.

These checks catch errors before they propagate to
consumers. The cost of catching an error pre-publication
is low; the cost of an incorrect published package is
high (re-publication, possible user-facing rollback).

## Repository operations

A repository operator is responsible for:

- Maintaining the repository descriptor (§6.1) with
  current signing key state.
- Generating the active and archive indexes (§6.2, §6.3)
  whenever a new package is published.
- Signing the descriptor and indexes.
- Hosting the static files.
- Retaining archived package versions per §6.3.1.
- Communicating with consumers about key rotations,
  package retirements, and other operational events.

These responsibilities scale with repository size and
trust level. The official Peios project carries them all
fully; a homelab custom repository may operate with much
lighter ceremony.
