---
title: Formatting
type: reference
description: Indentation, line length, whitespace, quoting, and brace
  placement.
---

## Indentation

Use four spaces per indentation level as the shared Peios default. Use spaces,
not hard tabs, unless a language or repository exception applies.

## Line length

Keep source lines within 100 columns as a strong expectation, not an absolute
limit. Wrap ordinary code and comments to fit. A longer line needs a concrete
readability or correctness reason; convenience alone is not an exception.

Examples include a URL that must remain intact, a diagnostic string whose
splitting would make it harder to find, or an expression that wrapping would
make materially harder to understand. Keep the exception local rather than
using it to justify long lines throughout a file.

Configure formatters to target 100 columns where supported, subject to the
agreed language and repository exceptions. Do not require awkward changes
solely to bring an otherwise justified exception under the limit.

## Text-file hygiene

Use UTF-8 encoding and LF line endings. End text files with a newline and
remove trailing whitespace. Preserve exceptions where the file format requires
a different representation or gives the whitespace meaning.

## Spacing and multiline lists

Prefer ordinary spacing rather than manually padding neighboring statements to
align columns. Allow alignment when it makes a genuine table clearer or is
produced by the agreed standard formatter. Avoid alignment that causes
unrelated lines to change merely because one identifier becomes longer.

Prefer a trailing comma after the final item of a multiline list where the
language permits it. Follow language-specific conventions and the agreed
formatter. Adding an item should not needlessly require changing the preceding
item's line.

## Quotes and statement terminators

Prefer double-quoted strings where single and double quotes are semantically
interchangeable. Allow alternative quoting when it reduces escaping. Preserve
language-specific distinctions, such as shell expansion and string
interpolation; this preference must not change a value's meaning. Use
semicolons in JavaScript and TypeScript.

## Braces

Use same-line opening braces as the common default for functions and control
flow, as in `if (ready) {`. Keep a closing brace and following `else` together
as `} else {`. Language and documented repository exceptions can override this
placement.

Where a language permits optional braces for conditionals or loops, braces can
be omitted only when the body contains one statement and the control clause
and body appear together on one line within 100 columns. Omitting braces is
permitted in that case, not required.

```c
if (!token) return INVALID_TOKEN;
```

Use braces for a body containing multiple statements, or when the condition or
body spans multiple lines. This includes a single statement placed on a line
below its condition:

```c
if (!token) {
    return INVALID_TOKEN;
}
```

If any branch in an `if` / `else if` / `else` chain needs braces, use braces
for every branch in that chain:

```c
if (!token) {
    record_failure();
    report_invalid_token();
} else {
    use_token(token);
}
```

Language requirements and documented repository exceptions still apply. Kernel
C deviations are specified in its repository guide. The optional-brace rule
applies where braces are optional control-flow delimiters; it does not replace
the block syntax of languages such as Python, Go, or Rust.
