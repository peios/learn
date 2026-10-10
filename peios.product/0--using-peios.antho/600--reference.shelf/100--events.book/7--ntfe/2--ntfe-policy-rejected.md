---
title: "ntfe.policy.rejected"
description: "The record that the kernel read a traffic policy and refused it, so the policy an administrator wrote is not the policy in force."
---

- **Event type:** `ntfe.policy.rejected`
- **Defined in:** `ntfe.evman`
- **Tier:** essential
- **Gating:** a refusal unlike the last one recorded
- **Cardinality:** once per distinct refusal

The record that the kernel read a traffic policy and refused it, so the
policy an administrator wrote is **not the policy in force**. NTFE accepts
or refuses a policy whole: one bad rule anywhere refuses every layer, and
the previous generation goes on judging traffic exactly as before. Nothing
is half-applied. The registry shows what was written; this shows that it
did not take.

The kernel reads the policy again whenever anything under
`Machine\System\Network` changes, including netd's inventory, and a broken
policy is refused by every read until it is fixed. The same refusal of the
same policy is recorded once: a new record means the policy or the reason
changed. A policy that is accepted, or found unchanged, starts the count
again.

The rule, where there is one, is the place to look: `outcome.reason` says
what is wrong with it.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`policy.generation`](~peios/events/field-index/fields-policy#policy.generation) | `uint` | required | The generation still in force, which the refused policy did not replace. |
| [`policy.previous-retained`](~peios/events/field-index/fields-policy#policy.previous-retained) | `bool` | required | Always true: NTFE never leaves part of a refused policy in force. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.reason != no-rules-key` | The error the operation failed with, as a negative errno. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | Why the policy was refused. A rule's own content: `unknown-fact` (a condition names a fact the language does not have), `bad-operator` (an operator the fact does not support), `bad-pattern` (a match value that does not parse for its fact), `bad-counter-view` (a `Counter.<n>` key that does not parse), `bad-actions-value` (`Actions` missing or not a list of strings), `bad-action` (an action that does not parse; `rule.action-error` says how), `prompt-chain-too-deep`, `bad-priority` (not an integer), `bad-enabled` (not 0 or 1), `bad-rule-name`, `present-never-at-layer` (a `Present` condition on a fact the layer never has), `key-not-at-layer` and `action-not-at-layer` (a condition or action the rule's layer does not speak). How it was stored: `bad-value-type` (a registry type rules do not use), `bad-value-length` (an integer of the wrong size), `not-utf8`. The policy as a whole: `rule-too-deep` (more than 13 levels), `too-many-rules` (more than 4096 in a layer), `bad-reporting-level` (`CurrentReportingLevel` not an integer from 1 to 6), `tag-hash-collision` and `stream-hash-collision` (two names that hash alike), `counter-never-written` (a counter no rule writes), `tag-downward-read` (a rule reading a tag a higher layer writes), `counter-store-refused` (the counter tables could not be built). And the read itself: `registry-read-failed`, `out-of-memory`, and `no-rules-key`, which is no policy at all — recorded once each time the key goes missing.<br><br>Values here (open set): `out-of-memory` · `unknown-fact` · `bad-operator` · `bad-pattern` · `bad-counter-view` · `bad-actions-value` · `bad-action` · `prompt-chain-too-deep` · `bad-priority` · `bad-enabled` · `bad-rule-name` · `tag-hash-collision` · `stream-hash-collision` · `counter-never-written` · `tag-downward-read` · `present-never-at-layer` · `key-not-at-layer` · `action-not-at-layer` · `rule-too-deep` · `too-many-rules` · `bad-value-type` · `bad-value-length` · `not-utf8` · `bad-reporting-level` · `counter-store-refused` · `registry-read-failed` · `no-rules-key`. |
| [`rule.name`](~peios/events/field-index/fields-rule#rule.name) | `str` | optional | The rule the refusal is in, or names, as its path relative to its layer key. Absent when the refusal is not one rule's: two names hashing alike, the reporting level, a registry read that failed outside any rule, or no Rules key. Held to 255 bytes. |
| [`rule.name-truncated`](~peios/events/field-index/fields-rule#rule.name-truncated) | `bool` | optional | Whether `rule.name` was cut short because the rule's path did not fit in the record. |
| [`rule.layer`](~peios/events/field-index/fields-rule#rule.layer) | `str.enum` | optional | The layer the named rule is in. Absent with `rule.name`, and also for the checks that span layers (`counter-never-written`, `tag-downward-read`), which name a rule but not its layer. |
| [`rule.action-error`](~peios/events/field-index/fields-rule#rule.action-error) | `str.enum` | when `outcome.reason == bad-action` | Why one action expression in a rule's `Actions` value failed to parse. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
