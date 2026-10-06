---
title: "rule.*"
description: "Every field the evman catalogue defines under rule: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `rule`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="rule.action-error"></a>`rule.action-error`

- **Type:** `str.enum`
- **Values:** `unknown-action` · `bad-arity` · `bad-argument` · `unknown-reject-kind` · `malformed`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Why one action expression in a rule's `Actions` value failed to parse.
`unknown-action` is a name the language does not have; `bad-arity` is the
wrong number of arguments; `bad-argument` is an argument of the wrong
shape, such as a `REPORT` level outside 1 to 5; `unknown-reject-kind` is a
`REJECT` story that is not minted; `malformed` is unbalanced parentheses or
trailing text. A rule with a bad action refuses the whole generation, not
just itself.

**Carried by:**

No event carries this field yet.

## <a id="rule.contender.name"></a>`rule.contender.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

A second rule named on the same record as `rule.name`: the rule that lost a
contest to it, or a rule that collided with it, such as one reading a tag
that a higher layer writes. Like `rule.name`, it is the rule's registry path
relative to its layer key.

**Carried by:**

No event carries this field yet.

## <a id="rule.hash"></a>`rule.hash`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The FNV-1a-64 hash of the rule's whole registry path. Always carried, even
when `rule.name` was cut short, so a reader can resolve a rule the record
could not name in full. Resolve it against the policy generation the
record names, because a later generation may name its rules differently.

A 64-bit integer rather than a `digest`: it identifies a path, and is not
a cryptographic summary of anything.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="rule.layer"></a>`rule.layer`

- **Type:** `str.enum`
- **Values:** `raw-packet` · `packet` · `flow`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Which evaluation layer the rule sat in. The layers see progressively more
context — a raw frame, a parsed packet, a tracked connection — so the layer
bounds what the rule could possibly have matched on.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="rule.lint"></a>`rule.lint`

- **Type:** `str.enum`
- **Values:** `fact-never-present-at-layer`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

A non-fatal finding about a rule that ingested but is almost certainly
wrong. `fact-never-present-at-layer` is a condition on a fact that never
exists at the rule's layer, which the absent-fact law makes permanently
false, so the rule occupies its place in the tree and never matches. A lint
never blocks ingestion and never appears beside a failure.

**Carried by:**

No event carries this field yet.

## <a id="rule.match-value"></a>`rule.match-value`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The literal match value written in a rule, exactly as its author wrote it
in the registry. It is the text the rule compares a fact against, such as
`10.0.0.0/8` or `22`, before NTFE parsed it. It matters most where the value
would not parse, because then the rule key alone does not say what was
wrong.

**Carried by:**

No event carries this field yet.

## <a id="rule.name"></a>`rule.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The policy rule that produced this record, by name. Rules are the unit an
administrator writes and edits, so this is the field that connects a record
back to something a person can change.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="rule.name-truncated"></a>`rule.name-truncated`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Whether `rule.name` was cut short because the rule's path did not fit in
the record. The cut falls at a character boundary, so the name is valid
text, but it is not the whole path: do not search for it exactly.
`rule.hash` still identifies the whole path, and is the value to resolve
the rule by.

Absent when the name was carried in full.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="rule.priority"></a>`rule.priority`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The effective priority of a rule, with any priority it inherits from its
ancestors in the rule tree already resolved. When several rules in one
layer yield a verdict, the highest priority wins and a tie goes to the
stricter verdict, so this is the number that explains why one rule beat
another. It is a signed 64-bit integer, as the rules language holds it, and
negative values are legal: a lower value means a rule loses to any rule
with a higher one.

**Carried by:**

No event carries this field yet.

## <a id="rule.report-level"></a>`rule.report-level`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The reporting level the matching rule asked for. Records exist only because
a rule contained an explicit report directive, and this is the level it
named.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="rule.seat"></a>`rule.seat`

- **Type:** `str.enum`
- **Values:** `ingress` · `egress` · `local-in` · `local-out`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Where in the path evaluation happened. Distinguishes traffic entering or
leaving the machine from traffic terminating at or originating from a local
socket, which is the difference between forwarding policy and host policy.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
