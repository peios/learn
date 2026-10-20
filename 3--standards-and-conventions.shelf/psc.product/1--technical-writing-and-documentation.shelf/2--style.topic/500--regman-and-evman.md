---
title: regman and evman
type: reference
description: How to write the prose in regman and evman records, covering
  summary lines for keys, values, events, and fields, what a body explains,
  header field wording, the markup each tool renders, and referring to other
  records without links.
---

regman and evman records document the registry and the event stream: every
key, value, event, and field. Each record is read in a terminal by someone
who has a specific path or event name in front of them and wants to know
what it means. [Core Style](~psc/core-style) applies to the prose; this
page adds the rules for writing it.

The file formats, the tools, and their lint checks are defined elsewhere:

- regman: [Writing regman pages](~peios/documenting-configuration/writing-regman-pages)
- evman: [Writing evman pages](~peios/documenting-events/writing-evman-pages)
  and PGSS §6.10, which defines the catalog normatively

## The first line is the summary

Each tool shows the first line or sentence of a record's body in its indexes
and search results, beside the name. Write it to stand on its own: someone
scanning a list of 50 values reads only this line. End it with a period.

The form of the summary depends on what the record documents:

| Record | Summary form | Example |
|---|---|---|
| Key | A noun phrase naming what the subtree holds | "Tuning parameters for the Exampled spooler." |
| Value | A noun phrase saying what the value is | "Maximum number of jobs held in the spool queue before new submissions are rejected." |
| Event | A past-tense sentence saying what happened | "A snapshot was written, or an attempt to write one failed." |
| Field | A noun phrase saying what the field holds | "The snapshot an event concerns, by the GUID the backup tool assigned it." |

Don't start a summary with the record's own name, or with "This value",
"This key", or "This event". The name is already printed beside it.

- Do: "Maximum number of jobs held in the spool queue."
- Don't: "MaxQueueDepth sets the maximum number of jobs in the queue."

## What the body explains

After the summary, explain what the reader needs to set the value or
interpret the event correctly:

- **For a value:** what changing it does, the trade-off involved, how it
  interacts with other values, and anything that makes a valid value a bad
  choice. Say why a limit exists when it is not obvious.
- **For a key:** the meaning shared by everything under it, such as how the
  owning component reads and validates the subtree, and where security is
  applied.
- **For an event:** when it is emitted and when it is not, what an operator
  would typically do on seeing it, and how it relates to other events.
- **For a field:** what the value means, its units, and when it is absent.

Don't describe the state of any particular machine. A record documents what
a value means and what it should be, never what it is set to now.

Don't record history. There is no "added in" or "previously"; the package
version records when a record changed.

When the meaning of each value of an enumeration is not obvious from its
name, document every value in the body as a list:

```text
- `full`: every file, regardless of earlier snapshots.
- `incremental`: files changed since the last snapshot of any kind.
```

In evman, the `values:` header line also lists the values. It says which
values exist; the body list says what each one means.

## Header fields

Header fields are shown verbatim in a fixed layout, so keep them short and
consistent.

- **`default`:** the exact value, as the reader would enter it. If there is
  no default, write `(required)` or say what absence means, in parentheses.
- **`valid`:** a short human-readable constraint. Write ranges with an en
  dash and no spaces (`16–65536`), sets with commas, and units in full after
  the number (`1–3600 seconds`).
- **`applies`:** exactly `live`, `restart`, or `reboot`. A short parenthetical
  is allowed when it helps: `live (at the next generation)`.

## Markup

Both tools render the same small set of Markdown: paragraphs, headings,
bullet lists, `**bold**`, and `` `code` ``. Prose is rewrapped to the
terminal width, so the source's line breaks within a paragraph don't show.

Use code formatting for every path, value name, event name, field name, and
literal value, as in any other form. Use bold sparingly, for the one warning
in a record that matters most. Don't use italics: both tools strip the
markers without styling the text, so the emphasis is lost.

## Referring to other records

Records are read in a terminal, so they cannot link. Refer to another
record by its full path or name in code formatting, and to a man page by name
and section. The reader can look up either directly.

<!-- lint-disable-next-line line-length -->
- Do: "The limit applies per interface; see `Machine\System\Network\Interfaces\<ifid> MaxRoutes`."
- Don't: "See the interface settings for the per-interface limit."

Document a key or event only in the package that owns it. When your
component reads another package's key, mention that key by path in your own
record's body; don't add a record for it.

## Wording

- Use the [word list](~psc/word-list) terms: a key holds values, a value
  has a type.
- Write "the value" or "the field", not "this setting", "this option", or
  "this parameter".
- Describe effects in the present tense, from the component's side: "netd
  rereads the key", not "the key will be reread".
- Write numbers as numerals, with units: "60 seconds", "4 KiB".
