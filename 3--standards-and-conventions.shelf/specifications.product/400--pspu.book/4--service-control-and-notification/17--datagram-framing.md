---
title: Datagram Framing
description: Newline-separated KEY=VALUE lines — what makes a datagram malformed, the three ways one line can fail, and why rejection is recorded rather than answered.
---

A datagram carries zero or more lines, separated by `0x0A`. Each line is
`KEY=VALUE`.

```
READY=1
STATUS=Listening on port 8096
```

A trailing newline on the last line is permitted and is not a line of
its own. A trailing `0x0D` on any line MUST be stripped before the line
is interpreted, so a sender that emits CRLF is understood.

The datagram MUST be well-formed UTF-8.

## Applying a datagram

The manager MUST parse every line before applying any of them, and MUST
apply every line of a datagram it accepts, in order.

**If any line is malformed, the manager MUST reject the entire datagram
and apply nothing from it.** Any file descriptors it carried MUST be
closed.

Partial application is the failure this rule exists to prevent. A
datagram saying `RELOADING=1` and something unintelligible has an
ambiguous meaning, and applying the half that parsed picks one reading
of it silently.

## What is malformed

A **line** is malformed when it is non-empty and:

- it contains no `=`; or
- its key is empty.

An **empty line** is not malformed. It is skipped.

A datagram is malformed when it is not well-formed UTF-8, or when it
exceeded a bound in §4.16.

## Three ways a line can fail to take effect

These are distinct and a service author needs the distinction:

| Situation | Effect on the datagram | Effect on the line |
|---|---|---|
| A malformed line | Rejected entirely | — |
| An **unrecognised key** | Applied normally | Ignored |
| A recognised key with an **unexpected value** | Applied normally | Ignored |

The second is what makes the field set extensible (§4.21): a service
built against a later revision may send a field an older manager does
not know, and the older manager applies the rest.

The third is the one that surprises. `READY=0` is not a malformed line
and does not reject the datagram; `READY` expects the value `1` and
anything else is silently ignored. A service MUST NOT send a recognised
key with a value the field does not define, and MUST NOT expect to be
told when it does. §4.19 gives each field's accepted values.

## Rejection is recorded, not answered

The manager MUST record a rejected datagram, with at least the sender's
identity and the reason, and MUST attribute it to a service where the
sender could be identified.

It MUST NOT reply. There is nothing to reply on.
