---
title: Interfaces and Data
type: reference
description: Arguments, dependencies, documentation, contracts, and data
  boundaries.
---

## Function arguments

Avoid positional arguments whose purpose is difficult to infer at the call
site. This applies to all argument types, especially booleans: a call such as
`save(file, true, false)` leaves the reader guessing what the switches
control.

Use named arguments where supported, meaningful named choices, or a clearer
interface to make the purpose apparent. Positional arguments remain
appropriate when their meaning is clear, as in `set_enabled(true)`. Do not
require readers to look up the function declaration merely to decipher an
ambiguous argument.

## Dependencies

Give a proportionate justification when adding a dependency. Explain what it
provides and consider maintenance, compatibility, licensing, build and runtime
footprint, and performance costs. Record the reasoning with the associated
work; a small, obvious choice does not need an elaborate report.

A maintained library can be appropriate for a complex parser, while a whole
package might be unnecessary for a trivial helper. There is no blanket rule to
reimplement functionality or always prefer a library.

## Documentation comments

Document public APIs and non-obvious internal contracts. Describe behavior,
errors, ownership, and locking requirements where relevant, using the
language's documentation-comment format. Explain constraints callers must
satisfy and guarantees they can rely on.

Use implementation comments to explain reasoning, invariants, or surprising
constraints that the code alone does not make clear. Keep comments accurate
when behavior changes. Do not add comments that merely repeat obvious code. An
internal function whose purpose and contract are clear from its code and names
does not need a documentation comment solely because it is a function.

## External contracts and style changes

Style cleanup must preserve behavior and externally consumed contracts. This
includes API and ABI names, calling conventions, and layouts, serialized field
names and values, configuration keys, and protocol-defined identifiers. Follow
required external names even when they differ from the naming table.

For example, renaming a local variable to match the guide must not silently
rename the JSON field it is serialized into. A symbol with no internal callers
might still be a supported public entry point; it is not obsolete on that
basis.

Intentional contract changes are functional work, not incidental formatting.
Apply the component's compatibility requirements and the breaking-change
documentation in [Commit Style](~psc/commit-style). This styleguide does not
establish a new ABI support period or authorize a breaking change during
cutover.

## Data representation

Prefer data structures that make contradictory states difficult to express.
For example, represent mutually exclusive connection states with one choice
between `connecting`, `connected`, and `disconnected`, rather than independent
boolean flags that can accidentally contradict one another. Apply this where
it simplifies the code; do not require elaborate types for every small value.

Represent missing values explicitly using the language's appropriate mechanism
rather than assigning a hidden meaning to an otherwise ordinary value. For
example, prefer an optional timeout to using `-1` for an unspecified timeout.
Respect established external APIs and formats that prescribe special values;
make their meaning clear where those representations are used.

## Validation boundaries

Make representations explicit at file-format and protocol boundaries. Specify
the text encoding and, for binary data, relevant field sizes, byte order, and
layout rather than accidentally depending on the current machine's in-memory
representation. Reference an existing format specification where it already
defines these details; do not duplicate or silently change its contract.

Deliberately platform-specific formats are permitted when their assumptions
are explicit. This rule does not require every format to be portable or choose
one universal encoding or byte order for Peios.

Validate incoming data at component boundaries and document the guarantees
internal code can rely on. For example, parse and check configuration values
before passing them around as valid settings. Internal helpers need not repeat
every check when the required guarantees already hold.

Revalidate when data can change in ways that invalidate those guarantees or
when it crosses another trust boundary. Boundary validation does not justify
trusting unchecked or subsequently changed data.

## Type annotations and inference

Where a language supports local type inference, prefer it when the type is
clear. For example, Rust's `let user = User::new()` need not repeat the `User`
type. Add an explicit annotation when it clarifies important information or
selects the intended type, such as a particular numeric representation.

Function interfaces follow their language's separate rules. Local inference
does not remove the requirement to make units and meaning clear.
