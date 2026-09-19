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

If a prepared root has a missing or empty `/etc/hosts`, Pekit supplies fixed
IPv4 and IPv6 localhost entries before starting the worker. A populated regular
hosts file remains intact; a symlink is replaced without following its target.
This supports offline loopback tests without importing the coordinator’s host
aliases or granting external network access.

The Peios catalogue uses Debian stable for reference builds, with reviewed
coordinator-owned Debian sid exceptions for rolling libxslt, Go and Rust
dependencies that stable cannot satisfy. Rolling Rust requires the matching
LLVM SDK; the retained Rust 1.83 lane continues to use Debian stable. The selected image contributes to the preparation
policy identity, and the resolved image digest, package closure and root archive
remain recorded. Recipe-local environment files cannot override this policy.

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


## Test prerequisites and coverage

A package gate must distinguish an unavailable worker prerequisite from a
product failure. Check the concrete prerequisite, retain its diagnostic and
identify every affected assertion. Do not turn an arbitrary failed test into
a skip or describe accepted exceptions as upstream passes.

Build workers have limited identity maps and do not run Peios authority services.
Perl's native hostname fixture compares its wrapper result with a direct libc
lookup: missing localhost resolution skips nine lookup assertions, while a
wrapper failure with working libc resolution still fails. Rsync checks mapped
identities and procfs ownership before selecting affected cases; its allocation
tests use a compiled filesystem probe when native Python has no ctypes module.
The remaining transfer and security assertions still run. Testing a blocked case
on a suitable host provides additional evidence, separately identified from the
isolated package gate.

Bash's upstream runner can return success after comparison failures. Its gate
collects failed comparisons and individual script statuses, uses a PTY for
terminal fixtures, and validates its private locale data through libc before
running locale-sensitive tests. Test-only platform expectations are explicit;
changing a golden file requires a demonstrated platform result, not merely a
failing comparison. A SIGCHLD fixture staggers child completion times because
ordinary signals can coalesce, while retaining all child and trap assertions.

Go runs its standard-library package set and cmd/go in upstream short mode.
A clone-based prerequisite probe determines whether five namespace-dependent
cases can run in the worker. Other clone errors fail the probe; unavailable
namespaces do not justify excluding unrelated tests. Short-mode success does
not certify resource-intensive upstream cases, and the existing internal-linker
hardening exceptions remain part of the recorded policy.

Record the scope of each suite. For example, cbindgen's library/binary unit tests
and generated C/C++ header checks do not establish its complete fixture or Cython
coverage. Kmod's native LLVM-generated alias fixtures can differ in entry order;
the gate checks the exact known diagnostics, identical alias sets, unchanged
module dependency data and preserved module precedence. It retains the raw
upstream discrepancy and rejects other failures.

Passing build, test and signed-archive checks establishes package qualification.
Repository-wide dependency closure, independently repeated builds, service
integration, privileged kernel behavior and image lifecycle checks remain
separate release requirements where applicable.


### Interpreter package tests

Perl and CPython use their upstream test suites as mandatory package gates in both the Debian reference root and the Peios native root. CPython's profile-guided optimization training is a separate build step; its smaller training selection does not replace the full test gate. Both interpreters also have staged runtime, embedding, installation-layout and native hardening checks.

The workers run offline and expose only one mapped user and group. Python's ownership and subprocess tests check the Linux UID/GID maps before requesting another identity. An unmapped identity is reported as an unavailable test prerequisite; mapped identities, ordinary ownership operations, and invalid-argument checks still run. This distinguishes the kernel's `EINVAL` for an unrepresentable identity from permission and interpreter failures.

Peios hostname lookup requires resolvd, which these offline workers do not run. Perl retains its existing `NO_NETWORK_TESTING` setting in the native root. Its `Net::hostent` test still loads the module and runs all hostname assertions if libc can resolve localhost. Otherwise, the nine lookup assertions are explicitly skipped. The Debian reference keeps those assertions unchanged. Package qualification therefore does not establish integration with a running resolvd service.

Python uses numeric loopback addresses for protocol transport tests while keeping TLS certificate names and SNI assertions distinct. Tests whose public API couples its destination hostname to TLS identity, local-address discovery, or a built-in localhost listener retain that hostname and require a functioning resolver. Positive POSIX account lookup and CGI identity cases likewise require actual account records. These are individual test or subtest prerequisites; no complete test module is excluded. The full Debian suite also runs these cases with its available services.

A small C control program, compiled inside the native test root, independently calls libc before any service-dependent skip. A successful libc control leaves the original Python assertion active, including any wrapper failure. Only explicit absence results can skip a case; an unexpected control error fails the gate. The current offline root lacks the Peios NSS resolver bridge and resolvd endpoint, which are checked independently when classifying its specific loader-error result. The helper captures its policy and control path before tests deliberately clear their environment. Qualification records upstream test totals and JUnit evidence. CPython's JUnit writer omits later skipped subtests within a test case, so verbose replays of the final artifacts and locked roots supplement the prerequisite skip IDs and reasons. These replay records remain distinct from qualification receipts. Resolver/account integration with running Peios authorities remains outside this isolated package gate.

The Python package's configured features remain explicit: TLS, bzip2, XZ, Zstandard, curses and UUID support are enabled. ctypes, SQLite, DBM/GDBM, Tk and Readline remain disabled until their required package dependencies are available. The package does not bundle pip/ensurepip; virtual environments use `python3 -m venv --without-pip`. Upstream platform and optional-resource skips are retained and recorded with qualification evidence.

Interpreter manuals are compressed and owned with their corresponding commands, including `pydoc3` and the `python3-config` SDK query tool. Python's shared runtime, development files, static library and debugging data remain separately installable. Compiled diagnostics and installed build metadata must not embed the build machine's temporary paths. The TLS smoke gate checks the supported OpenSSL minimum; dependency discovery records the actual linked SONAME, so a compatible newer OpenSSL major can be tested without an obsolete version-string restriction.

CPython source authentication retains its existing explicit limitation: the upstream Sigstore bundle is not yet verified by Pekit. Qualification records the immutable archive hash and source lock; it does not claim upstream signature verification. Python feature-minor upgrades remain ABI transitions for extension modules and site-packages, so automatic discovery follows the current supported feature-minor line.

The completed CPython 3.14.7 qualification reports 46,527 tests and 2,282 skips in the reference root, and 46,489 tests and 2,360 skips in the native root, with zero failures or errors. The native root additionally reports perf trampoline profiling as unsupported. Focused replays recover 10 reference namespace prerequisite skips and 57 native prerequisite skips: 29 forward hostname, one reverse lookup, 10 passwd-record, 13 CGI-account, one named-root-account and three namespace-ID cases. Other reported skips retain upstream platform, optional-feature and optional-resource reasons. These results establish build/test/archive qualification, not public repository installation or release acceptance.


### LLVM 18 experimental constant interpreter

LLVM 18's opt-in `-fexperimental-new-constant-interpreter` can leak wide-integer storage when function evaluation fails or speculative evaluation stops partway through an expression. The retained compatibility lane records this [upstream limitation](https://github.com/llvm/llvm-project/issues/139012); it does not carry the broader interpreter allocation and stack-lifetime rewrite.

The supplemental LeakSanitizer diagnostic failed, reporting 120 and 176 leaked bytes in its positive and negative experimental-interpreter corpora. These results remain failed and visible. Across 128 comparisons of the original and privately instrumented compiler, both leak classes also reproduced without the generic counting builtins. No sanitizer suppression or passing result replaces that evidence.

Both full default-interpreter diagnostic corpora and the bounded direct-builtin controls were clean under validated LeakSanitizer. The private assertion compile, link and deliberate-failure control also passed. These checks cover their recorded inputs; they do not establish universal leak freedom or a fully assertion-enabled compiler build.

Recording this limitation does not waive the configured package gates, signed-archive checks or installed Clang dependency-closure checks. Those requirements remain separate from the disposition of this supplemental experimental-interpreter diagnostic.


### Development package closures

A development package must install every file named by its exported build metadata. Some upstream CMake configurations load shared and static imported targets together, even when the consumer requests only a shared library. For these SDKs, the matching development package owns both the unversioned shared-library link and the static archive. Zstd, Capstone and both zlib-ng API variants follow this layout. Their existing static package names remain installable umbrellas depending on the complete SDK.

Imported executable targets also belong to the dependency contract. Capstone's SDK declares the package containing cstool. LLVM's SDKs similarly declare the tools referenced by their CMake exports, as well as external development libraries needed by exported components. Dependencies select matching same-family revisions, without cycles.

Package gates derive a minimal SDK prefix from the declared file mappings and same-family dependency closure. They configure, link and execute shared/static consumers against that prefix. Exact imported paths and linkage are checked, so unrelated staged files cannot conceal an incomplete package split. Independent qualification audits also compose signed package archives with their real resolver dependencies. Passing a consumer against the unsplit build installation alone does not establish that a separately installed SDK works.
