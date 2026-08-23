---
title: The Recipe
description: The recipe's own file — environment variables, wrapping, build targets and generation targets.
---

`pekit.toml` has ten top-level keys.

| Key | Type | Meaning |
|---|---|---|
| `out_dir` | string | Stage and output base, relative to the recipe root. Defaults to `out` |
| `env` | table | Environment for target commands |
| `wrap` | table | A command wrapper applied to every target command |
| `source` | table | Where the source comes from |
| `delegate` | bool or table | Borrow build targets, environment, wrapper, or package definitions from the fetched source tree |
| `build`, `test`, `install`, `clean` | tables | Target namespaces |
| `gen` | table | Generation targets, with their own verification |
| `source_package` | table | Whether and under what name to emit a corresponding-source package |

## Environment

`[env]` maps variable names to values. A name matches the usual shell
identifier pattern, and cannot begin with the reserved prefix pekit uses
for its own variables.

Declaration order is preserved, so a later variable may reference an
earlier one — `CXXFLAGS = "$CFLAGS ..."` works because `CFLAGS` was
declared above it.

## Wrapping

`[wrap].command` is a shell string or an argv array containing exactly
one `{{command}}` placeholder. In argv form the placeholder is a whole
argument, and cannot be the program name.

Every target command runs through the wrapper, which is how a whole
recipe is built inside a sandbox or under a cross-compilation shim
without each target knowing about it.

## Targets

A target namespace takes one of two shapes. A **bare** namespace — the
table itself carries a `command` — is a single target named `main`.
Otherwise each sub-table is a named target. Mixing the two is an error.

| Key | Meaning |
|---|---|
| `command` | Required. A shell string, or a non-empty argv array |
| `needs` | Other targets that run first |
| `clear_out` | Whether to clear the target's stage directory first. Defaults to true |
| `dependencies` | Build-tool dependencies, in the build namespace only |

Build-tool dependencies are grouped by provider — `peipkg`, `apt`, and
so on — and each entry maps a capability name to a constraint string.
The name is validated as a capability, so sonames and pkg-config module
names are legal; the constraint is a non-empty string, with `*` meaning
any.

These are the tools the *build* needs, and they drive the environment
the build runs in. They are not the dependencies the resulting package
declares.

## Generation targets

A `gen` target has its own shape: no `needs`, no `clear_out`, and a
verification half.

| Key | Meaning |
|---|---|
| `command` | Required. Regenerates the artifact |
| `verify_command` | Checks that the committed artifact is up to date |
| `verify_on_build`, `verify_on_test` | Which targets in that namespace the verification gates |
| `dependencies`, `verify_dependencies` | As for a build target; the verify set, when present, replaces rather than extends |

The two gating keys are three-valued. Absent gates every target in that
namespace; an empty array gates none; a populated array gates exactly
those named. Setting either without a `verify_command` is an error.

This is how a generated file — an ABI table, a constants header — is
kept honest: the artifact is committed, and a build fails if
regenerating it would change it.
