---
title: JavaScript and TypeScript
type: reference
description: Peios coding conventions for JavaScript and TypeScript.
---

Use conventional `camelCase` variables/functions and `PascalCase`
types/classes. Use the shared constant naming rule for named constants, not
for every local binding declared with `const`. Keep four spaces and the
100-column target: a formatter's two-space default alone does not override the
Peios baseline.

Apply read-only-by-default to bindings with `const`, and use `let` where
reassignment is needed. Remember that `const` does not freeze object contents.
The common optional-brace and explicit-argument rules apply.

In TypeScript, use strict type checking by default. Avoid `any` as a way to
bypass checking; use `unknown` for values that must be checked before use.
Allow narrow, explained exceptions where needed, such as integration with an
untyped third-party interface. Type declarations alone do not validate
external data.

That type-checking requirement concerns TypeScript; this guide does not itself
require converting JavaScript projects to TypeScript. Apply the approved
common quote preference and explicit semicolons using the pinned formatter
settings.

References: [TypeScript strict
checking](https://www.typescriptlang.org/tsconfig/strict.html) and [MDN
JavaScript
conventions](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Code_style_guide/JavaScript).
