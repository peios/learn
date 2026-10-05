---
title: Building a settings app
type: how-to
description: Build a settings window that looks and behaves like Peios's own with libgxwi's settings kit — sections, groups of rows, switches that apply at once, questions asked under a row, read-only states — and record a keyboard shortcut with fx-record.
related:
  - peios/desktop-settings/overview
  - peios/desktop-settings/keyboard-shortcuts
---

System Settings, My Settings, Desktop Settings, SSH Settings, Security
Policy, Package Manager and Feature Manager are built from one kit,
`libgxwi::settings`, so they share a layout
and behave alike. An app of your own can use it too. The kit is functions
that return HTML for a GXWI live surface (`libgxwi::Live`) and a stylesheet
that draws it; what a setting is and what changing it does stay your app's.

## The window

Serve the kit's stylesheet before your own:

```rust
libgxwi::settings::stylesheet(&mut app);
app.stylesheet("/my-app.css", include_str!("my-app.css"));
```

A window with sections is `settings::window(nav, current, page, status)`:

- `nav` is the side: `Nav::Heading` over runs of `Nav::Section`, each with
  an id, a title, what it is set to now in a few words, and a `Glyph` on a
  `Tile` colour. Choosing one sends the event `section` with `section` set
  to its id.
- `page` is the chosen section.
- `status` is `settings::status(said, aside)`: the line along the bottom,
  for what the last change did or why it didn't. It is always there, so
  nothing moves when it fills.

A window with one page and no sections is `settings::single(page, status)`.
Below 720 pixels wide, as when a second window tiles yours to half the
screen, the side keeps its icons and drops its words.

## A section

Start a section with `settings::head(glyph, tile, title, about)`. Where the
section is about one thing, put it large in a `settings::hero`, with
`hero_title` or `big` on the left and a `pill` or a switch on the right.

Settings go in groups of rows: `settings::group(title, rows, foot)`, with
rows from

- `row(label, about, control)`: a setting, its name and what it means on
  the left, what changes it on the right;
- `fact(label, value, mono)`: something known rather than set;
- `item(icon, name, lines, control)`: one of a list, such as a key;
- `link(icon, name, lines, aside, event, values)`: one of a list that opens
  to more about it;
- `more(More::Form | More::Asking, html)`: what opens under the row before
  it, a form to fill in or a question to answer.

Controls are `switch`, `select`, `text`, `button` and `submit`. Above a long
list, `search` is a field to narrow it, with buttons beside it; on a page
opened from a list, `back` returns to it. For something that takes a
while, `progress(done, of, text)` is a bar with what is being done over
it; with `of` 0 it moves without saying how far.

## How changes behave

Peios's settings apps follow these rules, and the kit is shaped for them.

- **A switch or a choice applies at once.** Both are fields: apply them in
  `Live::input`, and when a change can't be made, put the field back to what
  is set and say why on the status line.
- **What is typed applies when asked to**, with an **Apply** button that
  appears only once the field differs from what is set, inside a
  `<form fx-submit>`.
- **What is hard to undo asks first**, under its row (`More::Asking`), with
  the safe answer focused: `focused_button` gives the keyboard to it.
- **Ask the system what the person may change.** Open the registry key, or
  ask the daemon, for what a change needs; never infer it from the groups
  they are in. Show what they can't change read-only, and say why once:
  `banner` under the section's heading, or `locked` under one group.
- **Name things plainly.** Labels are short Title Case names of what they
  are, such as Machine Name or Time Zone; an inherited value is **System
  Default**; status messages are short and in the past tense, such as
  "Key removed."

## Recording a shortcut

A keyboard shortcut is chosen by pressing it, not typing it. An element
with `fx-record="bind"`, once clicked, waits for the next chord pressed
while its page has the keyboard and sends the event `bind`, with its
`fx-value-*` attributes and `chord`, such as `Ctrl+Alt+J`. It takes the
chord before anything else hears it, even one the desktop has claimed, so a
person can move a shortcut that is already in use.

Modifiers held alone are waited past. Escape, a click elsewhere or the
keyboard leaving the page stops it and sends nothing. While it waits, the
element carries `data-fx-recording="true"` for a stylesheet to show. The
browser keeps a few chords for itself (Ctrl+W, Ctrl+T, F11), and those
never arrive.

The kit's `recorder(event, values, idle, enabled)` is such a button, and
`chord` and `chords` show the shortcuts already set as keys, each with a
button to remove it.

## Where to go next

- [Keyboard shortcuts](~peios/desktop-settings/keyboard-shortcuts), where the
  recorder is used
