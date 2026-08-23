---
title: Lexical Rules and Literals
description: The lexical layer — identifiers, strings, binary, numbers, durations and times — and what fixes the evaluation time.
---

A query string is UTF-8. Whitespace separates tokens outside quoted
strings and is otherwise insignificant.

## Identifiers

An unquoted identifier is ASCII and matches:

```text
[A-Za-z_][A-Za-z0-9_.-]*
```

Identifiers name fields, payload paths, metric names, label keys, event
type patterns, log origins and value aliases. `.`, `_` and `-` are
permitted inside one; `/`, `:`, whitespace, quotes, brackets,
parentheses, commas and the comparison operators are not.

This grammar is the same one that constrains a log origin, a metric name
and a metric label key at ingestion (§3.7, §3.10), which is what makes
every stored identifier writable here without quoting.

A value that cannot be written as an identifier MUST be written as a
quoted string. Quoted forms are accepted anywhere an identifier is —
they are never required for a conforming identifier, but a *pattern* may
need one, and a collector holding identifiers stored under an earlier
revision must still be able to select them.

## Strings

A string literal is double-quoted UTF-8. The escapes are `\"`, `\\`,
`\n`, `\r`, `\t`, and `\uXXXX` for a scalar value in `U+0000` to
`U+FFFF` written as four hexadecimal digits.

A collector MUST reject any other backslash escape as a parse error, and
MUST reject `\uXXXX` naming a surrogate code point in `U+D800` to
`U+DFFF`. Surrogate pairs are not decoded: a character outside the basic
multilingual plane is written directly as UTF-8, not as two escapes.

> [!NOTE]
> Refusing surrogates rather than pairing them means there is exactly one
> way to write every character, and no way to write a sequence that is
> not valid UTF-8. A language that accepts lone surrogates has to decide
> what they mean when compared against stored text that cannot contain
> them.

## Binary

A binary literal is a lowercase `x`, a double quote, an even number of
hexadecimal digits, and a closing quote:

```text
WHERE target_sid == x"010500000000000515000000"
```

Hexadecimal digits inside are case-insensitive. `x""` is valid and is
the empty byte string. Whitespace inside the payload, an odd digit
count, and any non-hexadecimal character are parse errors.

A binary literal compares only against MessagePack `bin` values. A
collector MUST NOT coerce one to a string or a string to one: `x"6162"`
and `"ab"` are different values and never compare equal (§3.20).

## Integers

An integer literal is decimal or hexadecimal.

```text
WHERE origin_class == 2
WHERE granted_access == 0x1F01FF
```

A decimal integer MAY carry a leading `-`, in which case it MUST fit in
signed 64 bits; without one it MUST fit in unsigned 64 bits. A
hexadecimal integer is `0x` followed by one or more digits, is always
non-negative, and MUST fit in unsigned 64 bits. A leading `+` is not
valid. An out-of-range literal is a parse error.

## Floats

A float literal is a finite decimal number with an optional leading `-`
and either a fractional part or an exponent: `42.0`, `0.001`, `1e6`,
`-1.25e-3`. A token that looks like an integer, such as `42`, **is** an
integer literal and not a float.

Float literals are binary64 and MUST be finite. `NaN`, `Infinity`,
`-Infinity` and any literal that overflows to infinity are parse errors.
A leading `+` is not valid.

## Booleans and null

`true` and `false` are matched case-insensitively with ASCII folding.

`NULL`, likewise folded, is valid **only** in `IS NULL` and
`IS NOT NULL`. A collector MUST reject `field == NULL` and
`field != NULL` as parse errors rather than evaluating them.

> [!NOTE]
> Equality against null is refused rather than defined because every
> definition of it is a trap. Under three-valued logic it is neither
> true nor false, which no other operator here does; under two-valued
> logic it silently disagrees with SQL. `IS NULL` says what was meant
> and cannot be misread.

## Durations

A duration is an unsigned decimal integer followed immediately by `s`,
`m`, `h` or `d` — seconds, minutes, hours or days. A zero duration is a
parse error.

## Times

| Literal | Meaning |
|---|---|
| `<duration> ago` | That duration before the evaluation time. |
| `<duration> hence` | That duration after it. |
| `today` | Midnight of the current day, UTC. |
| `yesterday` | Midnight of the previous day, UTC. |
| `YYYY-MM-DD` | Midnight of that date, UTC. |
| `YYYY-MM-DDTHH:MM:SS` | That instant, UTC. |

Absolute literals are a fixed UTC subset. Components MUST be zero-padded
exactly as shown, the date MUST be a valid Gregorian date, hours are
`00`–`23`, minutes and seconds `00`–`59`. Leap seconds are not accepted.
Timezone suffixes and fractional seconds are not part of this revision
and MUST produce a parse error.

## The evaluation time

A collector MUST capture the evaluation time **once**, before execution
begins, and MUST use that one reading for every `ago`, every `hence`,
and for an omitted `UNTIL`, throughout the query — including throughout
the watch phase of a streaming query.

A query that read the clock more than once could produce a range whose
end preceded its start, or a window that grew while it was being
scanned. One reading makes the effective query range a fixed interval
for the life of the query.

`SINCE` is inclusive, `UNTIL` is exclusive: the effective query range is
`[SINCE, UNTIL)`. If `SINCE` is greater than or equal to `UNTIL` the
query returns no records — which is a successful query with an empty
result (§3.16), not an error. A time literal that evaluates outside the
timestamp domain MUST produce an error (§3.5).
