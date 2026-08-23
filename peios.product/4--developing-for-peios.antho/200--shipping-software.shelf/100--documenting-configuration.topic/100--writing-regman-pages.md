---
title: Writing regman pages
type: how-to
description: How to document your package's registry keys so regman can explain them. You ship a .regman fragment in /usr/share/regman/; this is its fenced format, the fmt/lint workflow, and the rules the tools won't catch for you.
related:
  - peios/registry-administration/regman
  - peios/registry-concepts/configuration-and-meaning
  - pekit/recipes/anatomy
  - pekit/reference/recipe-format
---

The registry stores a value's *type* and *bytes*, but never its *meaning* — it does not know that a queue depth must be at least 16, or what changing it costs. That knowledge ships with the software that owns the key, as documentation `regman` reads. From the operator's side this is [the registry manual](~peios/registry-administration/regman); from yours, the package author's, it is a file you write and install.

This page is how you write one. The package that *owns* a set of registry keys is the package that documents them — the only arrangement that stays correct as packages come and go.

## Where the documentation lives

`regman` reads a drop-in directory, `/usr/share/regman/`. Each `*.regman` file in it is one **provider**, and the provider's name is the file's stem:

```
/usr/share/regman/
    kmes.regman          # provider: kmes
    exampled.regman      # provider: exampled
```

A package documents its whole registry surface in one file. There is no central index to register with and no install-time hook: dropping the file in is the whole act, and removing it on uninstall is the whole undo. A missing directory simply means nothing is documented — not an error.

You ship the fragment the same way you ship any other file. Have your build target install it, then map it into the payload from the package file's `[files]` table:

```toml
[files]
"main:share/regman/exampled.regman" = "usr/share/regman/exampled.regman"
```

If the fragment is hand-written rather than generated — which it usually is — keep it beside the recipe and take it from there, no build target involved:

```toml
[files]
"@recipe:exampled.regman" = "usr/share/regman/exampled.regman"
```

See [Packages](~pekit/recipes/packages) for ref resolution, and [Multi-package recipes](~pekit/recipes/multi-package) if one recipe produces a family of packages that each document their own keys.

> [!NOTE]
> `regman` reads shipped documentation, never the live registry. A `.regman` page describes what a setting *means and should be* — its type, default, valid range — not what some machine currently has it set to. Don't write current-state-specific prose; it won't be true on the next box.

## The shape of a fragment

A fragment is a sequence of **records**, each documenting one key or one value. A record is a fence line, a small header, a blank line, then a Markdown body:

```
--- machine\system\exampled maxqueuedepth
canonical: Machine\System\Exampled MaxQueueDepth
type: REG_DWORD
default: 1024
valid: 16–65536
applies: restart

Maximum number of jobs held in the spool queue before new submissions
are rejected with EAGAIN.

Raising this lets the queue absorb larger bursts at the cost of memory.
The queue is preallocated, so the change takes effect at the next service
restart rather than live.
```

Four parts, in order:

- **The fence line** — `--- ` (three dashes, one space) followed by the **anchor**: the case-folded, lowercased lookup token `regman` matches against. You do not write this by hand; `regman fmt` bakes it from `canonical` (see *The fmt/lint workflow*, below).
- **The header** — `key: value` lines, one per line, until the first blank line. Keys are case-insensitive; values are trimmed. Unknown keys are ignored, so a typo'd field is silently dropped rather than rejected — watch for it.
- **A blank line** — this is what ends the header and starts the body. A record with no blank line has no body.
- **The body** — Markdown, rendered when the page is shown.

### Key docs and value docs

There is no `kind:` field. A record is a **value doc** if it carries any of `type`, `default`, `valid`, or `applies`; otherwise it is a **key doc**. That is the whole distinction — a key doc is just a record that omits all four.

A **key doc** introduces a subtree. Its body explains the shared semantics once (validation philosophy, security intent, how the subsystem reads the keys), and `regman <key>` renders that body followed by an auto-generated index of the values beneath it:

```
--- machine\system\exampled
canonical: Machine\System\Exampled

The Exampled spooler reads its tuning parameters from the values under
this key. Compiled-in defaults apply until LCS is available; after that
Exampled reads, validates, and applies each value, then watches the
subtree for later changes.
```

A **value doc** documents one knob. The four value fields are what fill in its card:

| Field | On | What it tells the reader |
|---|---|---|
| `canonical` | every record | The original-case `Path[ Value]` shown in the heading. **The one required field.** |
| `type` | value docs | Registry type tag — `REG_DWORD`, `REG_QWORD`, `REG_SZ`, … |
| `default` | value docs | The value used when nothing is set. |
| `valid` | value docs | The range, set, or constraint a sensible value must satisfy. Human-readable prose. |
| `applies` | value docs | When a change takes effect: `live`, `restart`, or `reboot`. |
| `deprecated` | either | Present ⇒ the item is being retired; the value is the replacement or a note. Renders as a banner at the top of the card. |

`canonical` is the only field any record *must* have — a record without it is dropped and flagged. The four value fields are not individually enforced, but each one you omit is a blank on the card, and `applies` in particular is the field operators reach for most. Treat a value doc as incomplete until it carries all four.

> [!NOTE]
> `regman` renders field values **verbatim** — it does not reformat them. If you want the default to read `1024 (1 K jobs)`, write exactly that into the `default:` field. The card shows what you wrote.

### The body's first line is the summary

There is no `summary:` field. The **first non-empty line of the body** is taken as the one-sentence summary — it is what shows next to the value name in a key doc's index and in `regman -k` search results. So write the body like a good commit message or docstring: lead with one self-contained sentence, then elaborate in the paragraphs below.

The body is Markdown: `**bold**`, `` `code` ``, headings, and bullet lists render; prose is wrapped to the terminal width. On a non-tty (piped) it renders plain, honouring `NO_COLOR`.

## A complete fragment

`/usr/share/regman/exampled.regman`, one key doc plus one value doc, as a package would ship it:

```
--- machine\system\exampled
canonical: Machine\System\Exampled

The Exampled spooler reads its tuning parameters from the values under
this key. Compiled-in defaults apply until LCS is available.

Security is on this key, not per value: every value inherits this key's
Security Descriptor.

--- machine\system\exampled maxqueuedepth
canonical: Machine\System\Exampled MaxQueueDepth
type: REG_DWORD
default: 1024
valid: 16–65536
applies: restart

Maximum number of jobs held in the spool queue before new submissions
are rejected with EAGAIN.

Raising this lets the queue absorb larger bursts at the cost of memory.
The queue is preallocated, so the change takes effect at the next service
restart rather than live.
```

That renders, for `regman Machine\System\Exampled MaxQueueDepth`, as:

```
Machine\System\Exampled MaxQueueDepth                 documented by exampled

  Type     REG_DWORD
  Default  1024
  Valid    16–65536
  Applies  restart

Maximum number of jobs held in the spool queue before new submissions
are rejected with EAGAIN.

Raising this lets the queue absorb larger bursts at the cost of memory.
The queue is preallocated, so the change takes effect at the next service
restart rather than live.
```

— and the bare `regman Machine\System\Exampled` renders the key body plus the index:

```
Machine\System\Exampled                               documented by exampled

The Exampled spooler reads its tuning parameters from the values under
this key. Compiled-in defaults apply until LCS is available.

Security is on this key, not per value: every value inherits this key's
Security Descriptor.

Values
  MaxQueueDepth  Maximum number of jobs held in the spool queue before n…
```

## The fmt/lint workflow

You write `canonical` with whatever casing reads best. The fence anchor — the folded, lowercased token the scanner matches — is *derived* from it, because the registry compares keys case-insensitively (Unicode Simple Case Folding) while a filesystem does not. Keeping the two in sync by hand is exactly the kind of error a tool should own, so two commands own it:

```bash
regman fmt  exampled.regman    # bake the folded anchor onto every fence line
regman lint exampled.regman    # verify structure and anchors
```

The workflow is:

1. **Write each record** with its `canonical` and body. Open the record with a fence line — you can put any placeholder after the dashes, e.g. `--- x`; `regman fmt` overwrites it.
2. **Run `regman fmt`.** It rewrites every fence to `--- <fold(canonical)>` and prints `<file>: anchors updated` if anything changed. It is idempotent — a second run is a no-op. A record missing `canonical` is skipped and reported.
3. **Run `regman lint`.** It reports any record with no `canonical:` and any fence anchor that disagrees with its `canonical` (`anchor for ...: fence has X, expected Y — run regman fmt`). A clean fragment prints nothing and exits 0.

Wire `regman lint` into your build or CI so a malformed fragment fails the build rather than shipping silently broken.

### Preview before you ship

`regman` honours `REGMAN_DIR`, so you can point it at your working directory and see exactly what an operator will see, without installing anything:

```bash
REGMAN_DIR=. regman Machine\\System\\Exampled MaxQueueDepth
REGMAN_DIR=. regman Machine\\System\\Exampled
REGMAN_DIR=. regman -k queue
```

## Rules the tools won't catch

`regman lint` checks structure and anchors. These conventions it does **not** enforce — they are on you:

- **Never start a body line with `--- ` (three dashes, a space, then text).** Any such line *is* a fence — it will be read as the start of a new record and silently split your page in two. A bare `---` on its own line (a Markdown thematic break) is fine; it's the `--- text` form that bites. If you need a horizontal rule, use `***` or `___`.
- **Keep `applies` to the vocabulary `live` / `restart` / `reboot`.** A short parenthetical is fine (`live (ring-buffer swap)`); a freeform sentence defeats the at-a-glance purpose of the field.
- **Lead the body with one summary sentence** (above) — an empty or buried first line leaves a blank in the key index and in `-k` results.
- **Don't invent fields.** Unknown header keys are ignored, so `defualt:` or `applies-to:` vanish without warning. There is deliberately no `access:`/SD field (the deployed Security Descriptor is live state a shipped file can't know — say access intent in prose if it matters) and no `since:` field (the package version already records provenance).

## Two documenters, one key

If two installed packages document the same `(key, value)`, `regman` does not pick a winner — it shows both records under a `documented by N packages:` banner, flagging the overlap as the anomaly it is. That's a safety net, not a feature: a key should have exactly one documenting package, the one that owns it. If you find yourself documenting another package's keys, that's usually a sign the ownership is wrong.

## Keeping lookups fast

Lookup is correct with no index at all — `regman` scans the corpus directly, and at realistic sizes that's a few milliseconds. An optional index (`regman index`, kept warm by a supervised `regman index --watch`) just skips the scan; it can be absent or stale without ever producing a wrong answer. None of this is your concern as a fragment author, with one exception worth knowing: package installs must **replace** a fragment by atomic rename rather than truncate-and-rewrite, so a lookup never sees a half-written file. peipkg already does this, so simply shipping the file the normal way is correct.

## See also

- [The registry manual](~peios/registry-administration/regman) — the operator's view of `regman`: reading a knob-card, the `-k` search, and the intent-not-state boundary.
- [Configuration, not storage](~peios/registry-concepts/configuration-and-meaning) — *why* the registry holds values without their meaning, the idea a `.regman` page exists to serve.
- [Packages](~pekit/recipes/packages) and [the recipe format reference](~pekit/reference/recipe-format) — installing the fragment as part of your package.
