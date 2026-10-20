---
title: Errors and Resources
type: reference
description: Error handling and reporting, mutability, resource ownership, and
  cleanup.
---

## Error handling

Handle expected failures through the language's normal error mechanism.
Invalid input, missing files, and I/O failures are ordinary possibilities:
handle them where an appropriate response is known, or return/propagate the
error so the caller can decide what to do. Recovery is not required at every
layer.

Reserve assertions and panics for internal bugs or broken invariants:
conditions the implementation relies on being impossible during correct
operation. Do not use them as ordinary error handling for externally supplied
invalid input. Application boundaries can decide to report an error and exit.
Kernel and other component-specific requirements can impose stricter rules on
assertions or panics; this distinction does not require panicking on every
internal failure.

### Intentionally ignored errors

Make a deliberate error discard explicit in the code. Document why ignoring
the error is safe, either at the discard site or in the helper's contract. An
empty handler or an unchecked result must not conceal forgotten error
handling.

For example, after a document has been saved successfully, failure to update
an optional recent-files list can be deliberately ignored. The explanation
should make clear that the document is safely saved and that the list is
optional. This does not justify ignoring failure of the save itself.

## Error reporting

Normally report a failure once, with enough context to understand it. Add
relevant context as an error propagates, then report it at the layer
responsible for handling or presenting it. Avoid logging the same failure at
every layer.

For example, preserve the underlying file error while adding that it happened
while loading settings during application startup. Separate log entries remain
appropriate when they serve distinct operational purposes rather than merely
duplicating the same report.

## Mutability

Prefer read-only data and bindings where the language supports them. Permit
mutation when the implementation needs it, rather than making values mutable
for hypothetical future changes.

Account for changes made through helper functions or other references, not
only assignments in the current scope. Distinguish a binding that cannot be
reassigned from an object whose contents cannot change; language-specific
rules will describe the appropriate mechanisms.

## Resource ownership and cleanup

Every resource must have a clear owner responsible for releasing it. Resources
include memory, open files, and acquired locks. Make ownership transfers clear
when responsibility passes to another part of the program.

Prefer the language's automatic cleanup mechanisms where available. For
example, Go's `defer` can schedule cleanup after successful acquisition so it
runs when the surrounding function returns, including early returns. Choose
the cleanup lifetime to match the resource's actual use: function-exit cleanup
is not the same as cleanup at the end of a nested block.

Where cleanup is explicit, cover error paths and early returns as well as the
successful path. Cleanup errors still follow the error-handling rules in this
article; scheduling cleanup does not justify silently ignoring a meaningful
failure.

## Shared mutable state

Avoid mutable global state by default. Pass the data or services a function
needs explicitly so its dependencies and possible effects are visible. This
does not require a framework or elaborate wrappers.

Allow justified exceptions for genuinely shared facilities, such as a
system-wide device list. Document who owns the state, how long it lives, who
can change it and how concurrent access is coordinated.
