---
title: Element Types
description: The initial element-type set — state fields and answer encodings for text, string, boolean, select, progress, log and action.
---

The initial set. Each type lists its state fields (beyond the common
fields of §3.8) and, for input types, the JSON encoding of its answer
value. The set grows by capability negotiation, not by version bump
(§3.5); a new type is specified by adding it here.

## `text` — output

Prose for the person to read.

| State | Meaning |
|---|---|
| `text` | The content. |

## `string` — input

One line of text; with `secret`, a password collector.

| State | Meaning |
|---|---|
| `min`, `max` | Length bounds, in characters. |
| `pattern` | Anchored regular expression the value must match. |
| `placeholder` | Ghost text; not a default. |

Answer value: JSON string.

## `boolean` — input

A yes-or-no.

Answer value: JSON true/false.

## `select` — input

Choose from what the daemon offers.

| State | Meaning |
|---|---|
| `choices` | Array of `{value, name, help?}`, in display order. |
| `multiple` | Zero or more choices rather than exactly one. |

Answer value: one choice's `value`; with `multiple`, an array of
them. Values are compared as exact JSON values.

## `progress` — output

How far along the work is.

| State | Meaning |
|---|---|
| `value` | Progress so far. |
| `max` | The whole; absent means indeterminate. |

## `log` — output

Accumulating lines of detail.

| State | Meaning |
|---|---|
| `lines` | The lines so far. |
| `append` | *In a sparse patch only:* lines to add. |

`append` exists so progress detail need not resend the backlog; the
daemon folds appended lines into `lines` (§3.10), so a late joiner
receives the accumulated state.

## `action` — pressed

| State | Meaning |
|---|---|
| `validate` | Default true; false skips §3.9 validation. |
| `primary` | The action an unattended answerer presses. At most one per turn. |
| `destructive` | Pressing this destroys something; a surface SHOULD make it hard to press by accident. |

Answer value: none, ever. The pressed action travels in
`Answer.action`.
