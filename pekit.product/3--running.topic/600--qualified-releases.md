---
title: Qualified releases
type: reference
description: "Automatic upstream discovery, fixed release candidates, required acceptance evidence and protected repository promotion."
related:
  - pekit/running/commands-and-targets
  - pekit/running/workspaces
  - pekit/running/linting
  - pekit/running/signing-and-provenance
  - pekit/reference/supporting-files
---

`pekit release` selects a candidate once, qualifies it, then promotes the exact
checked archives. `--latest` continues to discover upstream releases on every
new attempt. It does not select again between environments or before promotion.
Normal successful attempts need no per-version recipe edits or approval prompt.

```toml
[release]
path = "public-repository"
name = "example"
signing_key = "keyring:signing.repository_key"
environments = ["reference", "native"]

[release.checks]
integration = ["python3", "release/check-images.py"]
```

The workspace owns this policy. `path`, `name`, `signing_key` and a nonempty,
nonduplicated `environments` list are required. The last environment supplies
the promoted artifacts; preceding environments provide independent build/test
and lint results. `checks` maps names to command strings or argv arrays, all of
which must succeed. Distributions must configure their required source-rebuild,
reproducibility and integration checks here; an absent requirement is not
inferred by Pekit. These checks are trusted maintainer orchestration on the
coordinator, not downloaded upstream tests. Private keyring values and the
operator's general environment are not forwarded to them.

```sh
pekit release --all --latest --keyring production
pekit workspace --jobs 4 release --all --latest --keyring production
```

Release accepts package selectors, `--all`, normal version selectors and
keyrings. It requires a clean committed catalogue, isolated workers and anchored
sources. It rejects local sources and build/test/verification/signature bypass
flags. Environment selection comes from policy, not `--env`. Each environment
uses fresh stages and a disposable copy of one frozen prepared source tree. The source
remains at `source/` beside `build/` and `test/` within each environment’s work
directory, preserving debug-source path remapping. Worker writes stay in its
private copy and cannot alter the frozen source or another environment’s input.
Corresponding-source inputs are captured for every candidate, including recipes
that do not emit an automatic source package.

All declared release gates and applicable generated-file checks must pass.
Configured recipe and payload lint must be enabled. Payload lint reads frozen
signed archives, including generated links and packaging transformations; it
does not assume a mutable build stage still represents the published files.
Archive signatures, integrity and identity are verified. Source archives undergo
archive/signature verification; binary ELF/placement rules do not apply to them.
Allowed lint findings retain their configured reasons in the evidence.

Evidence is retained under `.pekit/releases/candidate-*`: source/recipe identity,
build-controlling inputs, dependency-root records, selected environments, tool
identity, logs, artifact digests and check output. Root preparers must retain
actual dependency identities under `PEKIT_JOB_STATE/dependencies`; release
rejects a build without those records. Back up this store and any referenced
large root archives for the supported lifetime. The source lock alone is not a
complete historical build environment.

Pekit assembles a private candidate repository before running workspace checks.
Each check receives `PEKIT_RELEASE_DIR` and `PEKIT_RELEASE_REPOSITORY`; the former
contains `candidate.json` with the exact selected artifacts, hashes, environments
and repository identity. Check commands must test that candidate and must not
resolve another upstream release. Output and exit status are retained. Failures,
missing or altered evidence, changed source inputs, or changed base repository
state reject promotion. Changing symlinks, file modes or directory membership
in retained evidence is also detected.

The publisher checks each resulting active install closure, rather than trying
to co-install mutually exclusive packages. It uses the real dependency resolver
for capabilities, conflicts and named-root placement, checks payload ownership,
and tests upgrades from every previous active closure. An old installed package
can require a declared replacement transition even after current dependencies
have been renamed. These checks do not simulate every historical combination,
execute maintainer actions, boot a guest, or replace a product's actual supported
upgrade tests. A broken bootstrap repository is not a valid public base.

After all checks pass, Pekit signs `release.json`. Promotion checks its signature,
artifact/evidence identities and base repository again, then publishes the whole
selected batch. Workspace members never publish separately on this path. The
repository retains `releases/<receipt-sha256>.json` and its `.sig`, a raw 64-byte
Ed25519 signature over the JSON bytes by the repository key. Detailed logs stay
in the retained candidate store. `PROMOTED.json` identifies the resulting index
and receipt. Generation timestamps may differ between preview and production;
package bytes and their qualification remain identical.

New production targets use **publisher state schema 2**, with qualification
required. Older publisher tools reject that state version. Ordinary publication
cannot bypass signed qualification merely by possessing a package-signing key.
Consumer repository/index/package wire formats remain unchanged. Signing
operators remain trusted: this is a publication contract, not a defense against
someone authorized to replace repository configuration and sign arbitrary data.

A failed qualification leaves the previous production index untouched. Disk or
process failure during the eventual index writes still requires normal repository
verification and recovery: a batch does not provide an atomic multi-file filesystem
transaction. A failed candidate is retained with diagnostics, and a fresh attempt
reruns qualification rather than trusting a saved success flag. This command
publishes local repository state; deployment to a public host remains a separate
operation.


Automatically managed `pekit.lock` updates are exempt from the clean-catalogue
check and are captured as exact candidate inputs. A successful upstream release
therefore does not force a human to commit its generated lock before the next
attempt. Recipe, helper, lint, environment and release-policy changes still
require a reviewed commit; lock integrity/source-authenticity checks still apply.


If a required dependency is unavailable in a reference environment, that
qualification remains incomplete. A separate diagnostic snapshot may run only
the native environment, but its receipt is native-only evidence: it does not
satisfy the configured reference requirement or justify silently changing the
publication policy. Keep the failed reference attempt and the dependency reason
with the native results.

## Reference toolchain differences

The last entry in `release.environments` produces the archives selected for
publication. Earlier environments provide reference builds. A workspace may
record a known reference-toolchain limitation with a reason per lint rule:

```toml
[release.reference_allow]
"elf.cet" = "Debian startup/runtime objects do not promise Peios CET markers; reference artifacts are not published"
```

The coordinator still runs the rule and records each allowed finding in the
reference receipt. The allowance never applies to the final environment, so a
native artifact missing CET code evidence or properties still prevents promotion.
Unknown rules, parameter names and empty reasons are rejected. This policy does
not bypass build failures, test gates, source verification, archive signatures or
repository checks. Ordinary `pekit lint` continues to enforce its configured
package policy; these allowances apply only to release reference builds.
