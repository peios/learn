---
title: Ingestion and generations
description: How the kernel walks Machine\System\Network into a validated forest and a network context table, what refuses a generation, what is republished and what is not, and how a generation is published under RCU and retired.
---

The kernel reads its own policy. There is no daemon that compiles rules
and pushes them down; `ingest.c` walks the registry through the LCS
source interface, feeds what it finds to the `pnp-core` builder over the
bridge, and publishes the result as a generation — or keeps the previous
one, loudly. [*ntfe-ingest.refused-walk-keeps-previous-generation] The same walk reads netd's inventory beside the rules into
the network context table (§6.3), [*ntfe-ingest.walk-reads-inventory-with-rules] because to a flow the two change
together: a network being recognised on an interface is as much a
policy change as a rule being written.

## Discovery and change notification

At LCS bootstrap, NTFE's key is discovered fifth alongside the other
kernel-owned subtrees: [*ntfe-ingest.key-discovered-at-bootstrap] `pkm_lcs_walk_absolute_components()` resolves
`Machine\System\Network` (the leading `Machine` hive component is
resolved locally against the hive root, not round-tripped), [*ntfe-ingest.machine-component-resolved-locally] and its
absence is not an error — no key, no policy and no context, generation
stays where it is. [*ntfe-ingest.absent-network-key-is-not-an-error] When the key exists one internal watch is armed on
it, depth-unbounded, for every change of content at any depth — LCS
delivers it a value set, a value deleted, a subkey created, a subkey
deleted and a key deleted; a security-descriptor change is not
delivered: [*ntfe-ingest.one-unbounded-watch-on-network-key] `Rules\`, `Interfaces\` and
`Networks\` beneath it are what NTFE reads; [*ntfe-ingest.ntfe-reads-rules-interfaces-networks] `Profiles\` and `Dns\` are
netd's and resolvd's, and a write there fires the watch and costs a
walk that publishes nothing. [*ntfe-ingest.foreign-subtree-write-publishes-nothing]

Watch events arrive per key and uncoalesced.
`peios_ntfe_network_registry_changed()` records the source and key, sets
a pending flag, and `mod_delayed_work()`s a re-walk with a 50 ms
debounce: [*ntfe-ingest.rewalk-debounced-50ms] a burst of writes (a transaction touching a rule and its
values, an autoapply seeding a whole policy, netd syncing every
interface's `Status` after a link event) yields one re-walk after the
burst goes quiet. [*ntfe-ingest.burst-yields-one-rewalk] The walk itself runs in process context on
`system_wq`, one at a time under a mutex, since the bootstrap refresh
and the deferred work may overlap. [*ntfe-ingest.walks-serialized-under-mutex]

## The walk

`peios_ntfe_network_refresh_from_key()` snapshots the LCS runtime limits,
sequence and layer view, enumerates the Network key's children for
`Rules`, `Interfaces` and `Networks`, and runs two independent stages —
the rules, then the context; [*ntfe-ingest.rules-stage-then-context-stage] a failure in the first does not skip the
second, and the walk reports the first error. [*ntfe-ingest.rules-failure-does-not-skip-context] No `Rules` key leaves the
previous generation standing, exactly as a walk that refused would. [*ntfe-ingest.absent-rules-key-keeps-generation]

The rules stage:

1. reads the Rules key's own values for `CurrentReportingLevel`
   (`REG_DWORD`, `REG_DWORD_BIG_ENDIAN` or `REG_QWORD`; 1..6; absent =
   1; anything else refuses); [*ntfe-ingest.reporting-level-type-and-range]
2. enumerates its children for the layer keys `Packet`, `RawPacket` and
   `Flow` (`Interface` is netd's — the interface layer is built and judged
   in userspace with the same `pnp-core`, and the kernel never reads it;
   any other name is ignored); [*ntfe-ingest.kernel-reads-three-layer-keys-only]
3. for each present layer, opens a builder and walks the layer key's
   subkeys as rule roots. Each rule is one `RSI_QUERY_VALUES` round trip
   (its effective, layering-resolved values, delivered in the batch
   record format `u32 name_len | name | u32 type | u32 data_len | data`)
   followed by one `RSI_ENUM_CHILDREN` round trip for its exceptions,
   recursively, [*ntfe-ingest.rule-read-is-two-round-trips] bounded by depth 12 and 4096 rules per layer: a root rule
   is depth 0, so a chain of 13 keys is the deepest read, and a rule
   deeper than that or a 4097th rule refuses the walk. [*ntfe-ingest.walk-bounded-depth-12-and-4096-rules]

Registry types are lowered as the builder ABI expects: `REG_SZ` and
`REG_EXPAND_SZ` to strings (NUL termination stripped), `REG_DWORD` and
`REG_DWORD_BIG_ENDIAN` to integers, `REG_QWORD` to a signed 64-bit
integer, `REG_MULTI_SZ` to a list of strings. [*ntfe-ingest.registry-type-lowering] Any other type in a rule
refuses the walk: [*ntfe-ingest.other-value-type-refuses-walk] atomic transitions prefer a loud rejection over a
silently half-read rule. So does an integer of the wrong length — a
`REG_DWORD` or `REG_DWORD_BIG_ENDIAN` whose data is not 4 bytes, a
`REG_QWORD` not 8 — in a rule or in `CurrentReportingLevel`. [*ntfe-ingest.wrong-length-integer-refuses-walk]

Everything the stage feeds the builder — each layer and whether its key
exists, rule name and depth, value name, type and bytes — also goes
through an FNV-1a digest, and so does the reporting level's *value*
(not its bytes: the same level re-written as another integer type
digests the same). [*ntfe-ingest.rules-input-digested] When the digest equals the one of the last walk that
published (none before the first), the stage publishes nothing: the
built forests are freed and the generation does not move. [*ntfe-ingest.unchanged-digest-publishes-nothing] The
active generation already *is* this policy — even when that policy is
no forests at all — and republishing would only make every sentence
stale for nothing. A walk fired by an inventory write therefore
publishes no rules; it moves the generation only if the context stage
finds the table changed (below). The writes of a transaction reach the
watch together at its commit and, like any burst, coalesce into one
walk. [*ntfe-ingest.inventory-write-changes-no-generation]

### The context stage

The inventory is read into one `struct peios_ntfe_context_table`, at
most 64 entries of interface name, network id, name and trust: [*ntfe-ingest.context-table-at-most-64-entries]

1. every child of `Networks\` is a record; its key name is the id (a
   UUID — a name of 40 bytes or more, which no id field can hold, is
   ignored with its record, once loudly), [*ntfe-ingest.overlong-network-id-ignored-once-loudly] and one
   `RSI_QUERY_VALUES` round trip reads its `Name` and `Trust`
   (`REG_SZ`; absent or unreadable is empty, and the id is still a
   fact), [*ntfe-ingest.unreadable-name-or-trust-is-empty] up to 256 records; [*ntfe-ingest.network-records-up-to-256]
2. every child of `Interfaces\` is an interface; its `Status` subkey is
   found by one `RSI_ENUM_CHILDREN` and read by one `RSI_QUERY_VALUES`
   for `Name` (the kernel interface name) and `Network` (the id netd
   identified on it). [*ntfe-ingest.interface-status-read] Both present make an entry, joined to the record
   of that id for its name and trust; [*ntfe-ingest.interface-entry-joins-network-record] either absent — no link, no
   offer yet, an `IGNORE`d or `DOWN` interface — makes none. [*ntfe-ingest.incomplete-status-makes-no-entry]

Nothing in the stage refuses a generation. [*ntfe-ingest.context-stage-never-refuses] A record that cannot be read is
logged and skipped — an interface key whose subkeys cannot be listed,
or whose `Status` cannot be read, carries no context; a network record
whose values cannot be read keeps its id with no name and no trust; [*ntfe-ingest.unreadable-record-skipped]
an interface beyond the 64th carries no context, [*ntfe-ingest.interface-beyond-64th-has-no-context] a value
longer than its field is truncated with one warning. [*ntfe-ingest.overlong-context-value-truncated] If the list of
`Networks\` or `Interfaces\` itself cannot be read, the stage publishes
nothing and the previous table stands: a table built from half a list
would strip every network after the failure point of its name and
trust, and with them every rule that names them. That failure is the
walk's error — it shows in `last_ingest_error` — and the rules stage's
outcome is untouched by it. [*ntfe-ingest.unreadable-list-keeps-previous-table] Otherwise the table goes to `peios_ntfe_context_publish()` (§6.3): if it equals the active
one entry for entry it is freed and nothing happens; [*ntfe-ingest.equal-context-table-publishes-nothing] otherwise it is
`rcu_assign_pointer()`ed into place, the generation counter advances,
the old table is freed after grace, and the kernel log says how many
interfaces carry a context. [*ntfe-ingest.changed-context-table-advances-generation] The generation advance is the whole
mechanism by which a context change reaches running flows: every
sentence is now stale and is re-judged on its flow's next packet
(§6.8), the same path a rule change takes. [*ntfe-ingest.context-change-rejudges-flows-on-next-packet]

## Building and validating

The builder (`ntfe_rust_builder_*`) accumulates `RuleInput` trees; `build`
runs `pnp_core::ingest::build_forest`, which parses every condition key
and action expression, orders each rule's conditions with the live-time
ones last (§6.4), [*ntfe-ingest.build-orders-live-time-conditions-last] resolves priority inheritance, [*ntfe-ingest.build-resolves-priority-inheritance] lints layer-impossible
facts (a `FlowState` or tag condition in a `RawPacket` forest; a
per-packet fact — `Length`, `TcpFlags`, `Fragment`, `Ttl`, `Dscp`,
`EtherType`, `DstMac`, `FlowState` — in a `Flow` forest; `Related` or
`Start.*` anywhere but `Flow` — all legal, and built never to hold; the kernel drops
lints, the authoring surface shows them), [*ntfe-ingest.layer-impossible-facts-lint-not-refuse] and collects the forest's
**name sets**: every tag name mentioned in a `TAG` action, a `PROMPT`
fallback, or a `Tag.<n>` condition, split into the names the forest
*writes* and the first rule reading each; every stream a `COUNT` writes;
every distinct counter view a `Counter.<n>(...)` condition reads, with
the first rule and value that mentioned it. [*ntfe-ingest.build-collects-name-sets] Views are deduplicated and
conditions refer to them by index — that index is what the bridge uses
when it fills `counter_views` (§6.3). [*ntfe-ingest.views-deduplicated-and-indexed]

Refusals, each carrying the offending rule's path (`BuildError`):
unknown fact, [*ntfe-ingest.refuse-unknown-fact] unsupported operator, [*ntfe-ingest.refuse-unsupported-operator] unparsable pattern, [*ntfe-ingest.refuse-unparsable-pattern] a counter view
that does not parse (bad duration, unknown key fact, duplicate
arguments, a window over the one-day horizon), [*ntfe-ingest.refuse-unparsable-counter-view] a non-list `Actions`, [*ntfe-ingest.refuse-non-list-actions] an
unparsable action, [*ntfe-ingest.refuse-unparsable-action] a `REJECT` kind that is not `Refused` or
`Prohibited`, [*ntfe-ingest.refuse-unknown-reject-kind] a `PROMPT` chain nested deeper than `MAX_PROMPT_CHAIN`
(4), refused as an unparsable action, [*ntfe-ingest.refuse-prompt-chain-too-deep] an action the layer does not
speak (`JOIN`, `IGNORE` or `DOWN`, the interface layer's verdicts, in
a kernel layer, directly or as a `PROMPT` fallback), [*ntfe-ingest.refuse-action-not-at-layer] a `Present`
condition on a fact that never exists at the rule's layer (every other
operator over such a fact is only linted, below; `Present` looks
through the absent-fact law, so `X.Present = 0` there would always
hold), [*ntfe-ingest.refuse-present-never-at-layer] a `Priority` that is not an integer, [*ntfe-ingest.refuse-non-integer-priority] an `Enabled` that is
not 0 or 1, [*ntfe-ingest.refuse-enabled-not-0-or-1] a rule name that is empty or contains a path separator [*ntfe-ingest.refuse-rule-name-with-path-separator]
(a backstop: LCS refuses such a key name before the walk could read
it) — and, over the name sets, two distinct tag names (or stream names)
whose 64-bit hashes collide. [*ntfe-ingest.refuse-name-hash-collision]

After all three layers build, `ntfe_rust_forests_check()` runs the checks
that span forests, because the stores are machine-wide: tag and stream
hashes must be distinct across *every* forest; [*ntfe-ingest.hashes-distinct-across-forests] every counter view must
have a writer in *some* forest — a view over a stream no rule writes is
statically dead (it can only ever read absent) and is refused with the
rule and key that read it; [*ntfe-ingest.refuse-view-without-writer] and no forest may read a tag a *higher*
forest writes (`RawPacket` < `Packet` < `Flow`) — tags flow strictly
upward, and since rules are the only source of tag names the downward
read is refused statically, with the reading rule and the name. [*ntfe-ingest.refuse-downward-tag-read]

## Publication

`peios_ntfe_policy_publish(packet, raw, flow, reporting_level)` is
process context under a mutex. [*ntfe-ingest.publish-serialized-under-mutex] It runs the cross-forest check, then
materializes the counter store for the union of every forest's views
(§6.6) — so a store that cannot be built (allocation, more than eight
windows on one table) refuses the generation before anything is
swapped. [*ntfe-ingest.unbuildable-counter-store-refuses-generation] Only then does it advance the generation counter, allocate the
new `struct peios_ntfe_policy` (three opaque forest pointers plus the
reporting level) and `rcu_assign_pointer()` it into place. [*ntfe-ingest.generation-advances-only-after-checks] Hook-path
readers dereference it under `rcu_read_lock()` and never block; [*ntfe-ingest.hook-readers-never-block] they see
the old generation or the new one, never a mix. [*ntfe-ingest.readers-never-see-mixed-generation] The old policy is
released by `call_rcu()`, and its forests by `ntfe_rust_forest_free()` in
the callback after grace. [*ntfe-ingest.old-policy-freed-after-grace]

Every walk records its outcome: `last_ingest_error` (0, or the positive
errno of the last failed walk) and `last_ingest_t_ns`, both in the
status. [*ntfe-ingest.walk-outcome-in-status] A refusal leaves the previous generation active and says so in
the kernel log. [*ntfe-ingest.refusal-logged-and-previous-stays-active] `contexts` in the status is the number of interfaces in
the active context table. [*ntfe-ingest.status-contexts-counts-interfaces]

### In the event stream

NTFE writes its own lifecycle to KMES, origin class `KMES_ORIGIN_NTFE`
(4), beside the reports of §6.6. Every publication writes one
`ntfe.policy.published`, after the swap; a refusal writes none. [*ntfe-ingest.publish-emits-policy-published]
Its payload is one `policy` map: `generation`, the generation now in
force; `generation-previous`, the generation of the policy it replaced,
0 for the first since boot; `layers`, the layers that have a forest, in
the order `raw-packet`, `packet`, `flow`, and an empty list for a policy
of no forests; and `report-threshold` and `report-threshold-previous`,
the new and the replaced `CurrentReportingLevel`, the latter 1 when
nothing was replaced. [*ntfe-ingest.published-event-payload] A walk
whose digest is unchanged publishes nothing, and so writes nothing. [*ntfe-ingest.unchanged-walk-writes-no-published-event]
A context-table change advances the generation without a policy and
writes no `ntfe.policy.published` either, so the generations between
two of these events are the earlier policy under a changed context.

A refused rules walk writes one `ntfe.policy.rejected`. [*ntfe-ingest.refusal-emits-policy-rejected]
Its `policy` map holds the `generation` still in force and
`previous-retained`, always true. Its `outcome` map holds `errno`, the
walk's negative errno, and `reason`. When the refusal is in, or names,
one rule, a `rule` map follows. It holds `layer` when the refusal arose
building one layer's forest, and `action-error` for a `bad-action`. It
holds `name`, the rule's path relative to its layer key; a path longer
than 255 bytes is cut at a character boundary, with `name-truncated`. [*ntfe-ingest.rejected-event-payload]

The errno is the walk's, unchanged. The reason is new: the bridge's
`ntfe_rust_builder_build_why()` and `ntfe_rust_forests_check_why()`
fill a `struct peios_ntfe_build_why` from pnp-core's `BuildError`. A
builder refusal keeps its own name and its rule's path, such as
`unknown-fact`, `bad-action` with its action error, `bad-priority`, or
`tag-downward-read` from the cross-forest checks, which name the rule
but no layer. [*ntfe-ingest.build-refusal-reason-crosses-bridge] The walk names the refusals it makes itself:

- `rule-too-deep` and `too-many-rules`, with `-E2BIG`;
- `bad-value-type`, `bad-value-length` and `not-utf8`, in the rule that
  holds the value;
- `bad-reporting-level`, `counter-store-refused` and `out-of-memory`;
- `registry-read-failed` for a source round trip that failed. [*ntfe-ingest.walk-refusal-reasons]

A walk that finds no `Rules` key writes the event too, with reason
`no-rules-key`, no `errno` and no rule. [*ntfe-ingest.absent-rules-key-emits-rejected]

Every walk re-reads the policy, including the walks netd's inventory
writes cause, so a broken policy is refused again and again until it
is fixed. The event is written once per distinct refusal: a walk whose
digest, errno and reason equal those of the last refusal written writes
none. A walk the rules stage accepts, published or unchanged, clears
that memory, so the next refusal is written whatever it is. A missing
`Rules` key is therefore written once each time the key goes missing. [*ntfe-ingest.repeated-refusal-written-once]
The kernel log line is written for every refusal, as before, and now
names the reason. Both events are built on the stack in process context,
under the publication mutex or the walk mutex; neither is ever written
from the packet path.

### In force

A registry write that has returned is delivered, not enforced: the walk
that reads it runs after the debounce. [*ntfe-ingest.returned-write-not-yet-enforced] Two status counters say which a
writer is looking at. `changes_noted` is incremented by
`peios_ntfe_network_registry_changed()` for every watch event, [*ntfe-ingest.changes-noted-counts-watch-events] and LCS
delivers its internal watches inside the write that caused them, after
the commit and before the syscall returns, so a writer that reads the
status after its write sees its own change counted. [*ntfe-ingest.writer-sees-own-change-noted] The deferred work
reads `changes_noted` under the same lock that clears the pending flag,
before it walks, and stores that value in `changes_walked` when the walk
returns, whether it published or was refused. [*ntfe-ingest.changes-walked-set-from-pre-walk-noted]

So a writer is in force once `changes_walked` reaches the `changes_noted`
it read after writing: the walk that satisfied it started after the
write committed. [*ntfe-ingest.in-force-when-walked-reaches-noted] A change that lands mid-walk raises `changes_noted`
again and re-arms the work, so the pair stays unequal until a later walk
covers it. [*ntfe-ingest.mid-walk-change-rearms-work] A refused walk still advances `changes_walked`; [*ntfe-ingest.refused-walk-advances-changes-walked] the writer
then reads `last_ingest_error` to learn that what it wrote is not what
is enforced. The walk records its error before it stores
`changes_walked`, and the status reads them in the other order, so a
status that shows a change walked shows that walk's error or a later
one's, never an older one. The bootstrap walk is not a noted change and moves neither
counter. [*ntfe-ingest.bootstrap-walk-moves-neither-counter] `net policy wait` is this loop.

## Generation 0

Until the first successful ingestion there is no policy at all, and
every layer is permissive: [*ntfe-ingest.generation-zero-is-permissive] `judged` stays 0, `permissive` counts
traversals, no events are emitted (there is no decision to attribute),
and the status reports `enforcing = 0`. [*ntfe-ingest.generation-zero-status-and-no-events] The init log line says it
plainly. This is the ratified loud default — the alternative, a
compiled-in policy the registry cannot see, was rejected.

A new generation does not touch the flows: every sentence written under
the old one is stale by generation and is re-judged on its flow's next
packet (§6.8). [*ntfe-ingest.new-generation-stales-sentences-without-flow-walk] That is how a policy change — and a context change,
which advances the same counter — reaches running connections without
a walk of the conntrack table.
