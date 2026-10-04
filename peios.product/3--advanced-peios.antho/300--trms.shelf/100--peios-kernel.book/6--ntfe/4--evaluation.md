---
title: Evaluation
description: The pnp-core algorithm — trigger set, abstention and speakers, collation, the backstop — and how the bridge carries a snapshot in and a verdict plus applied effects out.
---

Evaluation is `pnp_core::eval::evaluate(forest, snapshot, ctx)`: pure,
allocation-fallible, and the same code under cargo and in the kernel. [*ntfe-eval.evaluate-is-pure-and-shared]
Its steps are the ratified design's six, in order. [*ntfe-eval.six-steps-in-order]

## 1. Matching

A rule matches iff it is enabled and every one of its conditions holds
against the snapshot. [*ntfe-eval.rule-matches-iff-enabled-and-all-conditions-hold] Conditions are a conjunction; a value written as a
list is a disjunction *within* that one field. [*ntfe-eval.list-value-is-disjunction-within-field] A disabled rule never
matches, so its subtree is unreachable. [*ntfe-eval.disabled-rule-subtree-unreachable]

Conditions are evaluated in the order ingestion stored them, which puts
live-time conditions (`Time.*`) **last**, [*ntfe-eval.live-time-conditions-evaluated-last] and the conjunction stops at
the first false one. [*ntfe-eval.conjunction-stops-at-first-false] Every live-time condition actually reached — true
or false — is *consulted*, and `Rule::matches_traced()` records into a
`MatchTrace` the moment it would next flip (`Condition::next_flip()`): [*ntfe-eval.reached-clock-conditions-record-next-flip]
for hour, minute, second and day-of-week, the value sequence is scanned
one cycle ahead with the condition's own operator, so `Time.Hour.Equal
9-17` at 10:30 flips at 18:00 and `Time.Hour.LessThan 24` never does; [*ntfe-eval.clock-flip-scans-one-cycle-ahead]
day-of-month, month and year answer "next midnight", since exact flips
need calendar arithmetic nobody has asked for. [*ntfe-eval.calendar-fields-flip-at-next-midnight] A false condition is
consulted too: a higher-priority rule that missed only on the clock may
match later. [*ntfe-eval.false-clock-condition-is-consulted] A rule whose address or port conditions fail first never
consults its clock and contributes nothing. [*ntfe-eval.unreached-clock-condition-not-consulted] The earliest consulted flip
is the evaluation's `expires_at` — the Flow layer's sentence expiry
(§6.8); [*ntfe-eval.expires-at-is-earliest-consulted-flip] the per-packet layers compute it and ignore it. [*ntfe-eval.per-packet-layers-ignore-expires-at]

## 2. The trigger set

The walk descends each tree from its root. A node **triggers** iff it
matches and none of its children match: a matching child shadows its
parent. [*ntfe-eval.matching-child-shadows-its-parent] Shadowing exists only within a lineage — two trees never shadow
each other, and their order in the forest carries no meaning. [*ntfe-eval.trees-never-shadow-each-other] The walk
returns "matched" to the parent so the parent knows it was shadowed. [*ntfe-eval.walk-reports-match-to-parent]

## 3. Resolving a triggered rule

Every triggered rule's action list is resolved once. [*ntfe-eval.triggered-rule-resolved-once] Verdict actions fold
to the strictest listed; [*ntfe-eval.verdict-actions-fold-to-strictest] `TAG` and `COUNT` push effects; [*ntfe-eval.tag-and-count-push-effects] `REPORT` folds
to the highest level listed and pushes one effect if that level clears
`CurrentReportingLevel` (one report per rule per evaluation); [*ntfe-eval.report-folds-to-highest-level-and-gates] `PROMPT`
pushes a prompt-issued effect and, with no handler transport in this
release, resolves its fallback in place [*ntfe-eval.prompt-resolves-fallback-in-place] (nesting bounded by
`MAX_PROMPT_CHAIN`, 4). [*ntfe-eval.prompt-chain-bounded-at-four] Side effects always execute — they are pushed
before anyone knows whether the rule's verdict will win. [*ntfe-eval.side-effects-execute-regardless-of-verdict]

## 4. Abstention

A triggered rule that yields no verdict abstains. The walk then goes up
the rule's own parentage — the chain it descended by — to the nearest
ancestor whose actions contain a *direct* verdict (a top-level `PASS`,
`DROP` or `REJECT`; a verdict inside a `PROMPT` fallback does not count), [*ntfe-eval.prompt-fallback-verdict-is-not-direct]
and that ancestor **speaks for the region**: its full action list
resolves, once. [*ntfe-eval.abstainer-climbs-to-nearest-verdict-ancestor] A speaker reached by several abstaining descendants in
one evaluation executes only the first time (`spoken` tracks resolved
speakers by identity). [*ntfe-eval.speaker-executes-once-per-evaluation] Intermediate abstaining ancestors execute
nothing. [*ntfe-eval.intermediate-abstainers-execute-nothing] If no ancestor bears a verdict, the branch contributes nothing
and other trees or the backstop answer. [*ntfe-eval.verdictless-branch-contributes-nothing]

The attribution of a speaker's verdict is the speaker's path, not the
abstaining descendant's. [*ntfe-eval.speaker-verdict-attributed-to-speaker]

## 5. Collation

Every yielded verdict is a candidate `(verdict, priority, path)`. [*ntfe-eval.every-verdict-is-a-candidate] The
winner has the highest priority; at equal priority the strictest
verdict: `DROP` (3) > `REJECT(Refused)` (2) > `REJECT(Prohibited)` (1) >
`PASS` (0). [*ntfe-eval.highest-priority-then-strictest-wins] The two reject ranks are a deterministic tie-break — the
quieter story wins — that exists only because candidate order is
meaningless. Priority is the rule's *effective* priority, resolved at
ingestion: a rule's own `Priority` value, else its parent's, else 0. [*ntfe-eval.effective-priority-inherits-from-parent]

## 6. The backstop

No candidate at all: the verdict is `DROP`, attributed to `backstop`,
and the evaluation is flagged so the event can say so. [*ntfe-eval.no-candidate-drops-via-flagged-backstop] The backstop is
compiled in and un-deletable; [*ntfe-eval.backstop-is-undeletable] every permissive statement in a policy is
therefore a visible rule.

## The evaluation as data

`Evaluation` carries the winning verdict, its attribution, the backstop
flag, every effect to apply, every candidate (winners and losers alike)
for observability, and `expires_at`. [*ntfe-eval.evaluation-carries-every-candidate-and-effect] Effects reference their stores by
name *and* hash: `Effect::Tag { hash, op }`, `Effect::Count { hash,
amount }` with the amount already resolved (`Length` becomes the packet
length, or 0 when the packet has none), [*ntfe-eval.count-length-is-packet-length-or-zero] `Effect::Report { rule, level }`,
`Effect::PromptIssued { rule, handler }`. [*ntfe-eval.effects-carry-name-and-hash]

## The bridge

`ntfe_rust_evaluate(forest, snap, layer, reporting_level, out)` is what
`policy.c` calls under `rcu_read_lock()`. [*ntfe-eval.bridge-runs-under-rcu-read-lock] It:

1. lifts the C snapshot (§6.3) and resolves the forest's machinery facts
   through the stores — `peios_ntfe_tag_lookup()` for every tag name the
   forest mentions (`Packet` and `Flow` layers; `RawPacket` reads none), [*ntfe-eval.rawpacket-forest-reads-no-tags]
   `peios_ntfe_counter_read()` for every view — and gives a `Flow` forest
   its own facts, `Related` and `Start.*`; [*ntfe-eval.bridge-resolves-machinery-facts-before-eval]
2. evaluates with `EvalContext { reporting_level }`; [*ntfe-eval.bridge-passes-reporting-level]
3. writes the verdict, the reject kind, the backstop flag, the truncated
   attribution and `expires_at` (0 = never) into `struct
   peios_ntfe_outcome`; [*ntfe-eval.bridge-writes-outcome]
4. **then** applies the effects — `peios_ntfe_tag_apply()`,
   `peios_ntfe_counter_add()`, `peios_ntfe_report_emit()` with the verdict
   it just computed — counting each species into the outcome. [*ntfe-eval.effects-applied-after-verdict]

Ordering 4 after 2 is what the snapshot-immutability law requires: a
`COUNT` is applied after this packet's own view reads, so a rule cannot
trip its own threshold, [*ntfe-eval.count-cannot-trip-own-threshold] and a `REPORT` can name the verdict. [*ntfe-eval.report-names-the-verdict] Every
allocation in 1–2 is `GFP_ATOMIC` (`pnp-core`'s `pkm_alloc` in kernel
mode); [*ntfe-eval.bridge-allocations-are-atomic] a failure returns `-ENOMEM` and the hook fails closed (§6.2). [*ntfe-eval.allocation-failure-fails-closed] The
store calls never sleep. [*ntfe-eval.store-calls-never-sleep]
