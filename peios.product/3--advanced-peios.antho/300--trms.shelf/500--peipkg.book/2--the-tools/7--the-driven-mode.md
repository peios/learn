---
title: The Driven Mode
description: How a program runs peipkg — events as JSON Lines on standard output, answers on standard input, and one terminal event — with every event, question and error code.
---

The driven mode is for a program that runs `peipkg` in place of a person
at a terminal. Package Manager uses it. It changes the channel, not what
is asked: every question a terminal run asks is still asked, each
authorisation is still separate and audited, and `--yes` is refused.

Pass `--driven` before the verb:

```
peipkg --driven install org.gnu.make
peipkg --driven upgrade --dry-run
```

It works with every verb. It matters for the verbs that change things:
`install`, `upgrade`, `downgrade`, `uninstall`, `undo` and `claim`.

`--driven` is not the same as the query commands' `--json`. `--json`
prints one JSON document and reads nothing. `--driven` is a conversation
that lasts the whole run.

## Events

Standard output carries one JSON object per line. Each has an `event`
member naming its kind.

| Event | Members | Meaning |
|---|---|---|
| `plan` | `operations`, `authorisations`, `notes`, `other_roots` | The resolved plan, before anything is asked |
| `question` | `id`, `kind`, and members by kind | Something to answer on standard input |
| `progress` | `phase`, `step`, `steps`, `package` | The transaction has reached a step |
| `warning` | `text` | What a terminal run prints as `peipkg: warning:` |
| `message` | `text` | Anything else a terminal run would print |
| `done` | `summary`, `transaction` | Terminal: the command finished |
| `cancelled` | `reason` | Terminal: an answer refused, so nothing was changed |
| `error` | `code`, `message` | Terminal: the command failed |

Every run ends with exactly one terminal event. Read the outcome from it,
not from the exit status.

### The plan

Each entry of `operations` has:

- `kind`: `install`, `upgrade`, `downgrade` or `remove`;
- `name`;
- `from` and `to`, the versions, where they apply;
- `repository`, and `local` (true for a package given as a file);
- `size_download` and `size_installed`, in bytes, for a package being
  brought in;
- `root`, only for an operation in a root other than the one invoked
  (§10.3).

`authorisations` lists the elevated actions, as text. Each is also asked
as its own question. `notes` lists the resolver's notices, such as a
request satisfied through a `provides`. `other_roots` lists any other
root the plan changes.

A plan with no operations ends with `done`, summary `nothing to do`. A
`--dry-run` ends with `done`, summary `dry run`, after the plan. So
`peipkg --driven upgrade --dry-run` gives the available updates.

### Questions

A question has an `id`, counting from 1 within the run, and a `kind`.

| Kind | Members | Answers |
|---|---|---|
| `authorise` | `text`, the elevated action | `yes` or `no` |
| `proceed` | none | `yes` or `no` |
| `modified` | `package`, `path` | `remove`, `keep` or `abort` |

The authorisations come first, one per elevated action (§13.4), then
`proceed`. A `modified` question arrives later, during staging: an
uninstall would delete a configuration file that has changed since it
was installed (§6.6). The conversation therefore lasts until the
terminal event.

### Progress

`phase` is one of these, in order:

| Phase | Step |
|---|---|
| `fetch` | One per package brought in: fetched and verified |
| `stage` | One per package brought in: its content written beside its destinations |
| `apply` | Every change moved into place |
| `commit` | The new state recorded; past this, the transaction stands |
| `finish` | Backups discarded, directories reclaimed, side effects run |

`step` counts from 1 to `steps` within the phase. `package` is present
for `fetch` and `stage`. A cross-root transaction reports each root's
phases in turn.

## Answers

Write each answer as one JSON object on a line:

```
{"id": 1, "answer": "yes"}
```

The `id` must be the question's. An answer with another id, or one that
cannot be read, is refused, with a warning saying so. The end of input
is a refusal too, as it is at a terminal: a closed input never approves
anything.

## Error codes

| Code | Meaning | The way on |
|---|---|---|
| `stale` | A repository's trust state or metadata is past its maximum age, and refreshing did not cure it (§3) | Run again with `--allow-stale`, which is audited |
| `busy` | Another package operation holds the lock | Try again once it finishes |
| `denied` | The operator may not change what the transaction touches (§13.1) | None from this account |
| `unowned` | A file that belongs to no package would be replaced (§5) | Run again with `--overwrite-unowned`; the displaced copy is kept |
| `alternate-upgrade` | A package is upgraded by some other means (§6) | Run again with `--bypass-alternate-upgrade` |
| `unresolvable` | No plan satisfies the request (§4) | Change the request |
| `untrusted` | A configured repository's trust ceremony has never run, as with one an image ships (§3) | `peipkg repo add <name>` runs it, or remove the repository |
| `failed` | Anything else | Read `message` |

`message` is the text a terminal run prints, for showing to a person.
Act on `code`.

## Cancelling

Before `proceed` is answered, refusing any question cancels and changes
nothing. Once it is answered, the transaction runs to its end.

If the driving program goes away, the transaction still finishes:
`peipkg` ignores the broken pipe, and a question still to come reads the
end of input, a refusal. A `modified` question refused this way aborts
the transaction, which rolls back. Killing `peipkg` itself
mid-transaction leaves a pending journal, which the next run rolls back
before doing anything else (§8).
