---
title: Presentation hints
type: reference
description: What a daemon can say about a page beyond its elements — the class vocabulary and element state the stock terminal surface honours, and what it does whether you hint or not.
related:
  - peios/msip/turns
  - peios/msip/elements
  - peios/msip/element-types
  - peios/disks-and-filesystems/installing-to-disk
---

MSIP keeps *what a page contains* apart from *how it is drawn*. A daemon sends a turn of typed elements; a surface draws them however it draws that type. That split is what lets one surface serve every daemon and one daemon be driven by any surface, including a script.

It also means a daemon cannot lay a page out. What it can do is say what a page *is for*, and let the surface decide what that looks like. PGSS §3.7 gives a turn a `class` and §3.8 gives an element one — "presentation hints", which the specification is careful to say promise nothing. This page is the vocabulary the stock terminal surface (`msip-tui`, the renderer behind `install-tui` and `oobe-tui`) actually honours, so that a hint you send lands somewhere.

A class a surface does not know is ignored, by design. Sending one costs nothing and breaks nothing; it just does not draw anything either.

## Turn classes

| Class | What the surface does |
|---|---|
| *(none)* | A form: heading, elements stacked down a column, the actions in a bar beneath. Right for most pages. |
| `menu` | The page is a choice among its actions. They are laid down the body as a list, one highlighted, rather than in a bar. For a page whose only elements are actions and a sentence — a mode chooser, a repair menu. |
| `confirm` | The page asks whether you mean it. The heading is marked, and the destructive action is drawn as such even when not focused. For the page before something irreversible. |
| `progress` | A job is running. The page's `progress` elements are drawn as a phase list — done, active with a bar, pending — and its `log` fills whatever height remains. |

One class per turn is the expectation; the surface reads each independently, so nothing stops you sending two, but nothing today means anything by the combination.

## Element state the surface reads

These are defined by the [element types](~peios/msip/element-types) appendix rather than being surface conventions, but what the surface makes of them is worth knowing when you write a page.

| On | State | Drawn as |
|---|---|---|
| `action` | `primary` | The accent colour and bold. Also what an unattended answerer presses, so there is at most one. |
| `action` | `destructive` | Red, and red-highlighted when focused. Pressing it is not otherwise made harder: the `confirm` page is where that happens. |
| `string` | `secret` | Masked; never echoed, logged, or carried in an update. |
| `string` | `placeholder` | Ghost text in an empty, unfocused field. |
| `table` | `align: right` on a column | Right-aligned cells. Sizes and counts read better that way. |
| `table` | `enabled: false` on a row | Listed, dimmed, skipped by the highlight, refused as an answer. |
| `table` | `note` on a row | A short remark after the cells — typically why the row is disabled. |
| `table` | `empty` | Shown in place of the rows when there are none. |
| any | `help` | See below. |
| any | `error` | Red, under the element, until an update clears it. |

## What it does whether you hint or not

Some of the surface's behaviour is not a hint you can send but a fact to design pages around.

**Disabled elements take focus.** Tab reaches them, and while one is focused the footer shows its `help`. This is how the surface treats a thing you show greyed out: as something the person is meant to *see* and ask about, not something to hide. So an element you disable should carry a `help` that says why — "no keymaps are packaged yet", "domain membership needs a directory source" — because that sentence is what the person will read.

**Focus opens on the first element that can be answered.** A page that starts with two disabled fields opens on the first enabled one, or the primary action.

**A field's note line is reserved.** An element with `help` or an `error` always has a line under it, so focus moving does not move the page. Help is shown there while the element is focused; an error is shown there always.

**A table drops columns from the right** when it has no room for them all, as the appendix asks. Put the column a person must see first.

**Leaving is the surface's sentence, not yours.** Esc opens a question whose wording comes from the surface binary, because what leaving means — an installation carrying on without you, a machine left without an account — is a fact about the program, not the page.

**A script sees none of this.** `msip-drive` prints elements and answers them from its arguments; every hint above is invisible to it, which is the point of hints. A page has to work with none of them honoured.
