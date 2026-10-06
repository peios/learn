---
title: "emitter.*"
description: "Every field the evman catalogue defines under emitter: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `emitter`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="emitter.class"></a>`emitter.class`

- **Type:** `uint.enum`
- **Values:** `0 userspace` · `1 kmes` · `2 kacs` · `3 lcs` · `4 ntfe`
- **Set:** open
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The emission path that wrote the record: a kernel subsystem, or userspace
through the emit system call. Set by the kernel, never by the emitter, so
a record claiming a kernel event type with class `userspace` was written
by a program, whatever its type says.

The class is the path, not the event type's root. StrataFS records are
written through KACS and carry class `kacs`.

**Carried by:**

Every record, in the header.

## <a id="emitter.process.executable"></a>`emitter.process.executable`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The path the emitting process was executed from, resolved at exec with
symbolic links already followed.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))

## <a id="emitter.process.guid"></a>`emitter.process.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The process the record was written from, as a durable GUID. A random v4
minted when the process's KACS state is allocated, so unlike a PID it is
never reused and outlives the process. Zero on records written outside
task context, where `current` names whatever task was interrupted rather
than a real actor.

**Carried by:**

Every record, in the header.

## <a id="emitter.process.init-ns-admin"></a>`emitter.process.init-ns-admin`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the acting credential held `CAP_SYS_ADMIN` in the initial user
namespace at the time of the check. A Linux capability, so context for a
decision and never the decision itself: it says whether the caller could
have done the same thing from outside any user namespace, which is how an
operator tells a container-local actor from a host-wide one.

**Carried by:**

No event carries this field yet.

## <a id="emitter.process.name"></a>`emitter.process.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The kernel's name for the emitting process, typically the executable's
basename. Not `argv[0]` — a process that rewrote its argv is unaffected
here. Lossy: two processes can share a name.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))

## <a id="emitter.process.pid"></a>`emitter.process.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`
- **In groups:** [`subject`](~peios/events/groups/group-subject)

The process ID the record was written from. Reliable only in the short
term: PIDs are reused, so a PID in a week-old record may name something
unrelated. Correlate durably on `emitter.process.guid`.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped) (via [`subject`](~peios/events/groups/group-subject))
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged) (via [`subject`](~peios/events/groups/group-subject))

## <a id="emitter.process.userns-depth"></a>`emitter.process.userns-depth`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How deeply nested the acting credential's user namespace is. 0 is the
initial namespace; each level of `unshare(CLONE_NEWUSER)` adds one. Read
beside `emitter.process.init-ns-admin`: a capability held at depth 3 is
held only over that namespace's own objects.

**Carried by:**

No event carries this field yet.

## <a id="emitter.stamp-failure"></a>`emitter.stamp-failure`

- **Type:** `str.enum`
- **Values:** `no-task-context` · `effective-token-guid-read-failed` · `true-token-guid-read-failed` · `process-no-process-state`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which header identity stamp could not be filled, and why. A header GUID of
zero is otherwise ambiguous: a kernel-originated record that correctly has
no actor and one whose actor was lost read the same, and this field is what
tells them apart. Absent when every stamp was filled.

`no-task-context` covers all three stamps at once: the record was written
outside task context, where `current` is whatever task was interrupted, so
the kernel deliberately writes no identity rather than a wrong one. The
other values name one stamp each — the effective or true token's GUID
could not be read, or the process had no KACS process state.

**Carried by:**

No event carries this field yet.

## <a id="emitter.thread.tid"></a>`emitter.thread.tid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The thread that wrote the record, where the operation is scoped to a thread
rather than to its process. Impersonation is per thread, so on an
impersonation record this, not `emitter.process.pid`, names what took on
the client's identity. Reused like a PID, so correlate durably on the
header GUIDs.

**Carried by:**

No event carries this field yet.

## <a id="emitter.token.guid"></a>`emitter.token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The effective token the emitting thread ran under, as a durable GUID.
Under impersonation this is the client's token; `emitter.true-token.guid`
is the thread's underlying one.

**Carried by:**

Every record, in the header.

## <a id="emitter.true-token.guid"></a>`emitter.true-token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The emitting thread's own token, before any impersonation. Equal to
`emitter.token.guid` when the thread is not impersonating, so a query for
records where the two differ is a query for impersonated work.

**Carried by:**

Every record, in the header.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
