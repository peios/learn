---
title: Extension
description: Neither channel carries a version number — what may be added freely, what may not, and what a client must do with something it does not recognise.
---

Neither channel carries a version number. Both are extended by the rules
below, which are what allow a client and a manager built against
different revisions to interoperate.

## What may be added

**A request field.** A manager MUST ignore a request field it does not
recognise (§4.8). A client MAY therefore send a field a manager may not
know, and MUST NOT depend on the field having had an effect.

**A response field.** A client MUST ignore a response field it does not
recognise, and MUST NOT treat its presence as an error. This includes an
unrecognised member of `summary` in a `reload-config` response, and an
unrecognised key in `current_job` or `current_operation`.

**A notification field.** A manager MUST ignore an unrecognised key
(§4.17). A service MAY therefore send a field a manager may not know.

**A `type` value in a status warning.** A client MUST accept a warning
whose `type` it does not recognise and MUST NOT discard it. An
unclassifiable warning is still a warning.

## What may not be added without a version

Anything a client must *recognise* in order to behave correctly cannot
be added compatibly, because an older client's only options are to fail
or to misbehave.

A manager MUST NOT, without a negotiated version:

- introduce an **error code** outside §4.10;
- introduce a **service state**, **transition cause**, **operation
  state**, **operation type**, **operation source** or **job type**
  outside §4.B;
- introduce a **reload mode** outside the three in §4.13;
- introduce a **command**, or change what an existing command does;
- change the **shape** of an existing response, including changing a
  field's type or making a non-nullable field nullable.

A client encountering one of these has no correct behaviour available.
Faced with an unknown `state` it cannot decide whether the service is
running; faced with an unknown error code it cannot decide whether to
retry.

## What a client must do with the unknown

A client MUST treat an unrecognised **enumerated value** in a field it
depends on as an error for that request, and MUST NOT map it onto the
nearest value it does know. Guessing that an unfamiliar state is
probably like `active` is how a monitoring tool reports a broken system
as healthy.

A client MUST treat an unrecognised **error code** as unrecoverable for
that request. It MUST NOT retry, since it cannot know whether the
condition is transient.

## Versioning, when it comes

A future revision introducing an incompatible change MUST do so through
an explicit negotiation, in which a client states what it understands
and the manager answers within that. Until such a mechanism exists, this
chapter's contract is fixed and the rules above are the whole of the
supported way for it to grow.
