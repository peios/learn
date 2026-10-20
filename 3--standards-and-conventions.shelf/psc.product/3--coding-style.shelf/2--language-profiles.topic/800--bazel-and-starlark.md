---
title: Bazel and Starlark
type: reference
description: Peios coding conventions for Bazel and Starlark.
---

Use four spaces, `snake_case` functions/variables, and explicit `load`
imports. Use the language's underscore-prefixed private top-level names. Keep
the shared 100-column readability target, allowing intact labels where
splitting them is not useful. Starlark is not Python; Python-only typing and
syntax rules do not apply to it.

Use `buildifier` as the formatting baseline. Keep target declarations readable
and use shared abstractions for shared concepts rather than merely hiding
repeated declarations. Document public `.bzl` interfaces and their contracts.

Reference: [Bazel's Starlark guide](https://bazel.build/rules/bzl-style).
