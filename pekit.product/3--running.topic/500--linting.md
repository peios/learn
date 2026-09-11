---
title: Linting
type: reference
description: "The lint command, the lint.pekit.toml file that enables its rules, how files layer and how exemptions work, and every rule pekit ships."
related:
  - pekit/running/commands-and-targets
  - pekit/running/workspaces
  - pekit/reference/supporting-files
  - pekit/reference/cli
  - pekit/recipes/sources
  - pekit/recipes/packages
---

`pekit lint` checks a recipe against a set of rules and reports every
violation in one pass. It is the mechanical half of a packaging review: the
things a person would otherwise verify by reading the recipe and running
`readelf` over the build, written down once and run everywhere.

pekit ships the rules but enables **none of them by default**. A
`lint.pekit.toml` file turns rules on and sets their parameters, so a
distribution decides what its recipes are held to and a standalone project
decides the same for itself. A tree with no lint file has nothing to lint,
and `pekit lint` says so (`missing_lint_config`).

Every rule is an error. There is no warning level: a rule is either on, or
exempted for a stated reason. A warning would be a finding nobody has to
justify.

## Running it

```text
pekit lint
pekit lint --version 1.5.7
pekit workspace lint --json
```

With no version flag, an ordinary non-delegated recipe reads only its committed
recipe files, `pekit.lock`, and patch series. It resolves no source and touches
no network.

A delegated recipe is the deliberate exception. Plain `pekit lint` acquires
one source snapshot, loads the delegated `pekit.toml`, package files, and
`lint.pekit.toml`, merges them with the wrapper, and runs static rules against
that effective recipe. A templated, tracked-path, or PyPI source selects the
newest discoverable version; a fixed Git ref or fixed URL needs no synthetic
version; a local-only delegate uses its configured `[source.local]` tree. This
may contact the source and populate `out_dir`'s source cache, but it runs no
target and needs no build stage.

With an explicit source/version flag (`--version`, `--latest`, `--local`),
`lint` performs the same effective-recipe checks and additionally checks the
**payload** each package would pack, read from an existing build stage. It
never builds: a missing stage is `stage_missing`, naming the `pekit build` to
run first. The rules that need a payload are marked in the tables below;
without an explicit selection they are skipped with a `lint_skipped` event
that says how many.

`lint` takes the version-selection and local-source flags, `--env` and
`--keyring`, and the global flags. It accepts no selectors and no `--all`:
every package a recipe defines is checked. `pekit workspace lint` fans out
across every member like any other command.

Output is one `lint` event per finding, with `rule`, `package` and `path`
fields under `--json`, an event per exemption that applied (`lint_allowed`),
one per exemption that did not (`lint_unused_allow`), and a `lint_summary`.
The command fails with `lint_failed` when any finding stands.

## The `lint.pekit.toml` file

A rule is enabled by giving its key a value. A boolean rule takes `true`; a
rule with a real choice takes one of its enumerated strings; a rule with a
parameter takes the parameter. An absent key is a rule that does not run.

```toml
[package]
name.style    = "reverse-dns"
license       = "spdx"
license_class = true
description   = 80

[source]
discovery      = true
versions.floor = true
lock           = true

[elf]
pie   = true
relro = "full"
```

A rule's **ID** is its key path in the file: `package.name.style`,
`elf.relro`. That ID is what findings carry, what `[allow]` names and what
this page lists. Unknown keys are rejected (`unknown_key`), as is a value of
the wrong shape (`invalid_value`), so a misspelled rule cannot silently not
run.

### Where files are found, and how they layer

Files are found by walking up from the recipe directory to the workspace
root. A recipe outside a workspace reads only its own, except that a delegated
recipe also reads the file at its acquired source root. Plain lint performs
that acquisition automatically; it is not necessary to request payload lint
just to apply the source project's rules.

They merge **outermost first, nearest winning per key**, in this order:

1. the delegated source root, when there is one;
2. the workspace root;
3. each directory down to the recipe directory;
4. the recipe directory.

The source root comes first, not last, deliberately. A project may carry a
lint file that holds itself to a higher bar than the distribution packaging
it, but it cannot relax the distribution's rules.

A nearer file may re-parameterise a rule (`description = 40` under a
workspace that says `80`) but may **not** switch one off. Setting a rule
that an outer file enabled to `false` is refused (`lint_rule_disabled`).
Switching a rule off goes through `[allow]`.

### `[allow]`: exemptions with reasons

```toml
[allow]
"source.reproducible" = "non-public: grants unauthenticated SYSTEM access to a DWE guest"
"payload.manpages.required" = "upstream ships no manual pages; tracked in PEI-27"
```

An `[allow]` entry names a rule and gives a reason. The reason is mandatory
(`missing_reason`) and may not be empty. While the entry stands, that rule's
findings for the recipe are reported as `lint_allowed` rather than failing
the run. An entry that never applies is reported as `lint_unused_allow`, so
an exemption outlives its cause visibly and can be removed.

`[allow]` may appear in any file in the chain, but it belongs as close to
the recipe as the exemption is true for. Under `--json`, a workspace-wide
`pekit workspace lint` lists every exemption in the tree and its reason: the
review list of what is not yet up to standard and why.

## Rules

Each rule is general packaging hygiene, of the kind lintian, rpmlint,
rpminspect or a Homebrew audit also checks. Anything distribution-specific
is a parameter, never a value baked into pekit. Rules marked **payload**
need a staged build and run only with a version flag.

### `[package]`

Checked for each package definition the recipe produces.

| Rule | Value | Checks |
|---|---|---|
| `package.name.style` | `"reverse-dns"` or `"lowercase"` | Every package name, and the recipe directory when the recipe is a workspace member, matches the style. Reverse-DNS is `org.example.thing`; lowercase is any `[a-z0-9._+-]` name. |
| `package.license` | `true` or `"spdx"` | A license is declared. With `"spdx"`, the expression also parses as SPDX: identifiers joined by upper-case `AND` / `OR`, `WITH` for exceptions, balanced parentheses. The SPDX license list itself is not consulted. |
| `package.license_class` | `true` | A peipkg-format package declares `license_class`. Other formats are not checked. |
| `package.homepage` | `true` or `"https"` | A homepage is declared; with `"https"`, it is an https URL. |
| `package.description` | `true` or a length | A description exists, is one line, is at most the given length (80 when `true`), does not end with a full stop, and does not start with the package name or its last dotted label. |
| `package.dependencies` | `"consistent"` | No self-dependency; no dependency on a name the package itself provides; no name both depended on and conflicted with; no name in both `[dependencies]` and `[optional_dependencies]`; no provide or conflict on the package's own name. |
| `package.references` | `"reverse-dns"` | Every concrete package reference in package metadata and every Peipkg target dependency uses its canonical reverse-DNS name. Structured virtual capabilities such as `pkgconfig(foo)`, `python(abi)` and ELF SONAMEs remain valid. Other deliberately unqualified interfaces must be listed in `package.virtual_capabilities`. |
| `package.architecture` | `"consistent"` **payload** | A package declared architecture-independent ships no ELF object and nothing under an architecture-specific directory; a package declared for an architecture ships at least one such thing. The architecture-independent name is the `package.noarch` parameter, default `noarch`. |

`package.virtual_capabilities` is an array parameter shared by the
`package.references` checks. It is for genuine interchangeable interfaces such
as `sh` or an operating-system role, never for a compatibility alias for a
concrete package. For example:

```toml
[package]
references = "reverse-dns"
virtual_capabilities = ["init", "sh"]
```

### `[source]`

Checked against the recipe's `[source]` table. Rules for a source kind the
recipe does not use do nothing.

| Rule | Value | Checks |
|---|---|---|
| `source.reproducible` | `true` | The source is not `[source.local]` alone. A recipe with no source at all passes. |
| `source.discovery` | `true` | A URL source has `listing_url`; a git source (other than a tracked path) has `tag_regex`. Without them new upstream releases cannot be found, and every update is by hand. |
| `source.versions.floor` | `true` | A discovering source has a `versions` constraint with a lower bound: `>=`, `>`, `=`, `^` or `~`. A `< x` ceiling alone, `*`, or no constraint follows any release upstream ever published, including ones older than the recipe. Ceilings are never required. |
| `source.versions.ceiling` | `"none"` | No `versions` constraint bounds from above: no `<` or `<=` term, no `=` pin, no `^` or `~` range. A ceiling is where unattended updates silently stop; a new major is reviewed when it arrives, not fenced off in advance. |
| `source.ref` | `"immutable"` | A git `ref` is a template (`v{{version}}`), a full commit hash, a `refs/tags/` path or a tag-like `v1.2`, not a branch name that the lock could never pin. |
| `source.url.scheme` | `"https"` | Every source URL (`url`, `listing_url`, signature and patch-series URLs) is https. A git URL may also be `ssh://`, `git+ssh://` or `user@host:path`. |
| `source.lock` | `true` | `pekit.lock` exists with at least one entry; every URL entry carries a sha256 (and each patch its own); every git entry a commit hash; and, when the recipe verifies signatures, every URL entry records the key that verified it. |
| `source.signature.required` | `true` | A URL source has a `[source.url.signature]` block. |
| `source.signature.fingerprint` | `"full"` | A signature block lists at least one fingerprint, and each is the full 40- or 64-hex-digit fingerprint, never a short key id. |
| `source.signature.keys` | `true` | Every `key_files` entry exists and is not empty. |
| `source.patches.headers` | `true` | Every patch in the series has, ahead of its first hunk, a `Description:` or `Subject:` line and an `Origin:`, `Author:` or `From:` line (DEP-3). `git format-patch` output satisfies this as written. |

### `[build]`

| Rule | Value | Checks |
|---|---|---|
| `build.dependencies.providers` | array of provider names | Every build target declares a `[build.<name>.dependencies.<provider>]` table for each listed provider. An empty table is an explicit "none". |
| `build.test` | `true` | The recipe defines a test target. A delegate recipe whose targets live in its source is not checked. |

### `[payload]`

All **payload** rules. Paths are payload destinations, slash-separated,
relative to the package root.

| Rule | Value | Checks |
|---|---|---|
| `payload.junk` | `true` or an array of patterns | No destination matches a build-leftover pattern. `true` uses the built-in list: `**/*.la`, `**/*.orig`, `**/*.rej`, `**/*.o`, `**/*~`, `**/*.swp`, `**/.git`, `**/.git/**`, `**/.gitignore`, `**/CMakeCache.txt`, `**/.DS_Store`, `usr/share/info/dir`, `**/perllocal.pod`, `**/.packlist`. An array replaces it; `"@default"` in the array includes it. A `.pyc` without its `.py` is always reported. |
| `payload.scripts` | `true` | A file with a `#!` line is executable; its interpreter is an absolute path that is shipped by this recipe or listed in `payload.interpreters`; and, for `sh`, `dash`, `ash` and `bash`, the host shell's `-n` syntax check passes. |
| `payload.symlinks.dangling` | `"forbidden"` | Every symlink resolves to something shipped by one of the recipe's packages. Claim slot paths, which point across packages by design, are skipped. |
| `payload.symlinks.absolute` | `"forbidden"` | No symlink has an absolute target. |
| `payload.filenames` | `"portable"` | Every destination is printable ASCII with no whitespace. |
| `payload.special_files` | `"forbidden"` | No device node, fifo or socket. |
| `payload.manpages.required` | `true` | Every file in a bin directory has a manual page, shipped by any package of the recipe, named after it in any section. |
| `payload.manpages.compression` | `"gzip"` or `"none"` | Every file under a man directory is gzip-compressed, or none is. |
| `payload.pkgconfig` | `true` | No `.pc` file contains the build directory path. |
| `payload.license_file` | a path template | Every package ships a regular file under the rendered directory. `{{name}}` is the package name; version tokens render as in a recipe. |

Parameters, all optional: `payload.interpreters` (default `/bin/sh`,
`/usr/bin/sh`, `/bin/bash`, `/usr/bin/bash`, `/usr/bin/env`,
`/usr/bin/python3`, `/usr/bin/perl`), `payload.dirs.bin` (default `bin`,
`sbin`, `usr/bin`, `usr/sbin`), `payload.dirs.lib` (default `lib`, `lib64`,
`usr/lib`, `usr/lib64`, `lib/*-linux-*`, `usr/lib/*-linux-*`) and
`payload.dirs.man` (default `usr/share/man`, `share/man`). Directory
parameters are glob patterns matched against a destination's directory.

### `[split]`

| Rule | Value | Checks |
|---|---|---|
| `split.devel.packages` | a name pattern, or an array | **payload.** Development files land only in packages whose names match: headers, pkg-config files, CMake files, aclocal macros (the `split.devel.files` patterns, default `usr/include/**`, `include/**`, `**/pkgconfig/*.pc`, `**/cmake/**`, `usr/share/aclocal/**`, `usr/lib/**/*.cmake`) and unversioned `.so` symlinks in a lib directory. After ten findings in one package the rest are counted. |

### `[elf]`

All **payload** rules, checked for every ELF program or shared library in
every package. Relocatable objects, kernel modules and anything under
`usr/lib/debug/` or `usr/src/` are skipped.

| Rule | Value | Checks |
|---|---|---|
| `elf.pie` | `true` | No `ET_EXEC` program; executables are position-independent so address-space randomisation applies. |
| `elf.stack` | `"non-exec"` | A `PT_GNU_STACK` header is present and does not request an executable stack. |
| `elf.relro` | `"partial"` or `"full"` | A dynamic object has a `PT_GNU_RELRO` segment; with `"full"`, it is also bound at load (`BIND_NOW`), so the GOT is read-only afterwards. |
| `elf.relr` | `true` | A dynamic object with relative relocations left in `.rela.dyn` has none, or carries `DT_RELR`; the linker flag is `-z pack-relative-relocs`. |
| `elf.cet` | `true` | An x86 object carries the `GNU_PROPERTY_X86_FEATURE_1_AND` note with both IBT and SHSTK. One assembly object without the note drops it for the whole link. Other architectures are not checked. |
| `elf.rpath` | `"forbidden"` | No `DT_RPATH` or `DT_RUNPATH`. |
| `elf.textrel` | `"forbidden"` | No text relocations. |
| `elf.stripped` | `true` | No `.debug_*` sections and no `.symtab`. |
| `elf.debuginfo` | a package-name template | The recipe has a package named by the template (`{{name}}` is the shipping package) and, for every object with a build-id, that package ships `usr/lib/debug/.build-id/xx/yyyy.debug`. An object without a build-id is reported. |
| `elf.build_paths` | `"forbidden"` | The object does not embed the build directory path anywhere in its bytes. |
| `elf.soname` | `true` | A `lib*.so*` regular file directly in a lib directory has a `DT_SONAME`, and its file name is the soname or the soname followed by more version components. |

## What lint does not check

Whether a package's role is documented, whether its split is sensible,
whether a service runs under the right identity, and whether its files sit
in the places a particular distribution mandates. The first three are
review judgement; the last is [pack-time validation](~peios/peipkg/producing-packages/building-and-signing)
in the package format, not a lint rule.
