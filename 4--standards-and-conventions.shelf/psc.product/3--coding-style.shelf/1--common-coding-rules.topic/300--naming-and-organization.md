---
title: Naming and Organization
type: reference
description: Names, units, constants, imports, visibility, and source
  organization.
---

## File organization

Group closely related code by purpose. Keep a small implementation and its
private helpers together when that makes them easier to understand; separate
unrelated features. Do not impose a blanket rule of one function or type per
file. Follow language-specific layout conventions where applicable.

## Naming

Use these shared defaults where there is no strong language convention or
documented repository exception:

| Identifier | Style | Example |
| --- | --- | --- |
| Variables | `snake_case` | `retry_count` |
| Functions | `snake_case` | `load_config` |
| Modules | `snake_case` | `package_store` |
| Types | `PascalCase` | `AccessToken` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |

Language-specific naming departures follow the [consensus
rule](~psc/scope-and-precedence); these defaults do not override a strongly
established language convention.

### Identifier wording

Prefer descriptive names that communicate the role of a value or operation.
Allow familiar abbreviations such as `id`, `fd`, and `url` when their meaning
is clear in context. Short local names such as `i` are acceptable in small
scopes where their purpose is obvious. A short name is not a reason to make
readers trace distant code to discover its meaning.

### Units and type information

Make units explicit in a value's name or type. For example, use `timeout_ms`
for a number of milliseconds, or `timeout` when its type conveys the unit or
duration semantics. Do not leave readers guessing whether a bare number means
seconds, milliseconds, bytes, or another unit.

In typed languages, do not encode a value's programming-language type in its
name. Use `timeout_ms`, not `timeout_ms_int`: the unit explains the meaning,
while the type declaration already supplies the representation. Name values
for their role and meaning rather than adding type prefixes or suffixes.

## Constants and literal values

Strongly avoid magic constants: fixed values whose meaning or significance is
unclear from the code. This applies to strings, numeric values, bit masks, and
other literals, not only numbers. Give them meaningful names or use
appropriate named choices so readers can understand their purpose. Explain the
reason for a particular value when its name alone cannot convey it.

For example, use `MAX_RETRIES` for a retry policy instead of an unexplained
number in the retry logic. A name should explain meaning, not merely repeat
the value. Obvious literals, such as starting a counter at `0`, do not need a
named constant solely because they are literals.

## Imports

Prefer explicit imports that make dependencies and the origins of names clear.
Avoid wildcard imports by default. This is a preference, not a hard rule:
allow exceptions when they improve clarity or follow a strongly established
language convention. Explain non-obvious exceptions where useful.

Group standard-library, third-party, and project-local imports in that order
where the language supports it. Preserve side-effect-sensitive ordering and
document narrow exceptions rather than blindly sorting imports.

## Visibility and encapsulation

Keep functions, types, and fields private or module-local by default where the
language supports it. Expose them more widely when other code needs that
interface. Keep implementation details behind the interface so they can change
without requiring changes in callers.

Encapsulation should serve a clear purpose. Do not add unnecessary getter,
setter, or forwarding wrappers solely to make simple code appear encapsulated.

## Unused and commented-out code

Remove unused code and old implementations left inside comments. Use version
control to recover previous implementations instead of retaining them in the
source for possible future use.

Keep useful documentation examples and code with a real supported purpose. An
implementation for another supported platform is not unused merely because the
current build does not select it. Establish that code is obsolete before
removing it.
