---
title: Core Style
type: reference
description: The writing rules every form of Peios documentation shares,
  covering voice, word choice, spelling, capitalization, punctuation, numbers,
  formatting, page structure, procedures, and code examples.
---

These rules apply to every form of Peios documentation: learn, man pages,
command-line help, regman, evman, technical reference manuals, and
specifications. Each form has its own page that adds to them or adjusts
them, and where a form's page disagrees with this one, the form's page wins
for that form:

- [Learn](~psc/style/learn)
- [Man Pages](~psc/man-pages)
- [Command-Line Help and Errors](~psc/command-line-help-and-errors)
- [regman and evman](~psc/regman-and-evman)
- Specifications and technical reference manuals:
  [Conventions for Specifications and TRMs](~psc/conventions)

This page is the canonical source. If a rule is not written here or on a
form's page, it is not a Peios rule. When something comes up that no rule
covers, choose the clearest option for the reader and propose a rule.

## Voice and tone

**Be direct.** Say what something does, or what to do, in as few words as
possible. Lead with the point; put background after it, or link to it.

- Do: "Run `svctl restart netd` to apply the change."
- Don't: "In order to apply the change, it will be necessary to restart the
  netd service, which can be done using svctl."

**Use active voice.** Name who or what does the thing. Use passive voice
only when the actor is unknown or truly does not matter.

- Do: "The kernel rejects the request."
- Don't: "The request is rejected."

**Use present tense.** Documentation describes what the system does now.

- Do: "netd reads the configuration at startup."
- Don't: "netd will read the configuration at startup."

**Use the imperative for instructions.** Start the sentence with the verb.

- Do: "Open the Registry Editor."
- Don't: "You should open the Registry Editor." or "Please open the Registry
  Editor."

**Address the reader as "you"** in learn and in man page prose where a
person is the subject. Specifications and technical reference manuals
describe the system and do not address the reader; see their form pages.

**Don't use "we", "our", or "us".** The documentation speaks for Peios, not
for a team. Give recommendations directly.

- Do: "Use a group, not individual accounts, in the access control list."
- Don't: "We recommend using a group."

**Don't write about time.** Avoid "new", "now", "currently", "recently",
"soon", "in a future release", and "no longer". They go stale silently. When a
change in behavior matters to the reader, state the version it applies to.

**Don't condescend.** Avoid "simply", "just", "easily", "obviously", "of
course", and "it's easy to". If a step is not simple for the reader, the word
is wrong; if it is, the word is unnecessary.

**No humor, idioms, or cultural references.** They do not translate and they
date quickly.

- Do: "This setting has no effect until netd restarts."
- Don't: "This setting is a bit of a damp squib until netd restarts."

**Use contractions where they read naturally** in learn and man page prose:
"don't", "isn't", "you're". Don't use them in specifications or technical
reference manuals, and never contract a negative in a sentence that states a
requirement or a warning: "Do not remove the key", not "Don't remove the key".

## Sentences and paragraphs

**Keep sentences short.** Aim for under 25 words. Split a sentence that
carries two ideas into two sentences.

**Keep paragraphs short.** One idea per paragraph; three or four sentences is
usually enough. A paragraph that needs a fifth sentence often wants to be a
list.

**Put the condition before the instruction.** The reader should know whether
a sentence applies to them before they act on it.

- Do: "If the service is running, stop it first."
- Don't: "Stop the service first if it is running."

**Keep "that" when it helps the reader parse the sentence.** "Check that the
key exists", not "Check the key exists".

**Make every pronoun unambiguous.** If "it" or "this" could refer to two
things, name the thing.

- Do: "The token carries the user's SID. The kernel compares the SID with
  each access control entry."
- Don't: "The token carries the user's SID. It compares it with each entry."

**Avoid noun stacks.** Break up chains of three or more nouns.

- Do: "the cache for registry layer metadata"
- Don't: "the registry layer metadata cache"

**Avoid "there is" and "there are" openings.** Start with the subject.

- Do: "Three layers apply to every key."
- Don't: "There are three layers that apply to every key."

## Spelling and word choice

**Use US English spelling**: "behavior", "color", "initialize", "license"
(noun and verb), "canceled", "catalog". Identifiers, quoted output, and names
of external standards keep their own spelling.

**Prefer the short, common word.**

| Use | Instead of |
|---|---|
| use | utilize, leverage |
| start | initiate, commence |
| end, stop | terminate (unless it is the literal name of an operation) |
| help | facilitate, assist |
| about | approximately, in regard to |
| to | in order to |
| if | in the event that |
| because | due to the fact that |
| can | is able to |
| need, must | is required to |
| enough | sufficient |

**Don't use Latin abbreviations.** Write the English.

| Use | Instead of |
|---|---|
| for example | e.g. |
| that is | i.e. |
| and so on (or end the list) | etc. |
| through, by using | via |
| compared with, or | vs. |
| namely | viz. |
| about (for dates) | circa, ca. |

**Use "can", "might", and "must" for their one meaning each.**

- "can" is ability: "You can grant the privilege to a group."
- "might" is possibility: "The request might time out."
- "must" is necessity: "The value must be a string."
- Don't use "may" in prose. It is ambiguous between permission and
  possibility. Specifications use **MAY** as a defined keyword; outside that
  use, write "can" or "might".

**Use "select" for choosing anything in a graphical interface**, whether by
mouse, keyboard, or touch. Don't use "click", "tap", "hit", or "press" for UI
elements. Use "press" only for keys on a keyboard.

**Use "enter" for typing a value into a field**, and "type" only when the
reader types characters that are not submitted.

**Use "turn on" and "turn off"** for toggles and features. Don't use
"enable" and "disable" in learn prose; keep them where they are the literal
name of an option, flag, or registry value.

**Spell out an acronym on first use on each page**, followed by the acronym
in parentheses: "security identifier (SID)". After that, use the acronym.
Acronyms every reader knows (CPU, URL, USB, HTTP) need no expansion.

**Choose "a" or "an" by pronunciation.** "a SID" (said as a word), "an ACL"
(said as letters), "an HTTP request". The [word list](~psc/word-list)
records the decided form for Peios terms.

**Pluralize acronyms without an apostrophe**: "SIDs", "ACLs", "PIDs".

**Use Peios terms as the word list defines them.** Where Peios uses a word
that means something different in Windows, Linux, or elsewhere, the
[word list](~psc/word-list) is the authority.

## Inclusive language

**Use "they" for a person of unknown gender**, including the singular.
Better still, address the reader as "you" or name a role: "the
administrator".

**Don't use terms with harmful associations** when a neutral term is equally
precise.

| Use | Instead of |
|---|---|
| allowlist, denylist | whitelist, blacklist |
| primary, replica | master, slave |
| main | master (branch) |
| placeholder, sample value | dummy value |
| confidence check, quick check | sanity check |
| stop responding | hang (of a program, in prose) |

A literal identifier keeps its literal name. If an upstream command, flag, or
field uses one of these words, write it exactly as it is, in code
formatting.

**Don't refer to ability or disability unless it is the subject.** "Turn on
the screen reader", not "for blind users, turn on the screen reader", unless
the page is about accessibility.

## Capitalization

**Titles use title case.** A title is the name of a page, topic, shelf,
anthology, book, product, or chapter, wherever it is set: frontmatter
`title:`, a `trail.toml` `title`, or a man page `NAME` header. Capitalize the
first and last words and every major word. Lowercase these unless they are
the first or last word:

- articles: a, an, the
- coordinating conjunctions: and, but, or, nor, for, so, yet
- prepositions of any length: to, of, in, on, at, by, for, from, with,
  about, between, through, without
- "to" in infinitives and "as" in any role

So: "Developing for Peios", "Writing Policy for the Network Firewall", "What
an Event Is".

**Headings within a page use sentence case.** Capitalize the first word and
proper nouns only.

- Do: "## Choosing a registry layer"
- Don't: "## Choosing a Registry Layer"

**Lowercase common nouns, even important ones.** "access token", "security
descriptor", "registry key", "service". Capitalize product and component
names: "Peios", "GXWI", "Registry Editor" (the application). Components
whose names are written in lowercase keep it, even at the start of a
sentence: "netd", "peinit", "regman". Rephrase if that reads badly.

**Write identifiers exactly as they are.** Code formatting keeps the case:
`svctl`, `Machine\System\KMES`, `KACS_ACCESS_DENIED`.

**After a colon, lowercase the next word** unless it is a proper noun or
begins a complete sentence.

**Expanded acronyms are lowercase** unless the expansion is a proper noun:
"access control list (ACL)", not "Access Control List (ACL)".

## Punctuation

**Use the serial (Oxford) comma**: "users, groups, and services".

**Use em dashes sparingly, with a space on each side**:
"the kernel — not the service — makes the decision". Prefer commas,
parentheses, or a second sentence. Never
use more than one pair in a sentence. Write the em dash as the character
`—`, not as `--`.

**Use an en dash for ranges in tables and compact contexts**: "0–65535",
"pages 4–9". In running prose, write "from 0 through 65535".

**Use hyphens for compound modifiers before a noun**: "a read-only key", but
"the key is read only". Don't hyphenate after an adverb ending in "-ly": "a
widely used flag".

**Put commas and periods inside closing quotation marks** in prose. Text the
reader types or sees literally goes in code formatting, not quotation marks,
so its punctuation is never in doubt.

**Don't use exclamation points.**

**Don't use "and/or".** Write "A, B, or both".

**Don't use the ampersand** in prose or titles, except in a literal name.

**Use semicolons sparingly.** Usually a period is clearer.

**End list items with a period only when they are complete sentences.** In a
single list, either every item is a sentence or none is.

**Use one space after a period.**

**Use straight quotes and apostrophes** (`"` and `'`), not typographic ones.
Use a normal space and a normal hyphen, and no zero-width characters. They
render the same and search differently.

## Numbers and units

**In prose, spell out zero through nine and use numerals for 10 and above.**
Exceptions, which always take numerals:

- any technical quantity: sizes, counts in a specification, limits, ports,
  versions, offsets, durations ("3 seconds", "a 2-byte field")
- anything with a unit or symbol ("4 KiB", "5%")
- any number in a table, list of values, step, or code example
- a number that sits next to another number in the same sentence ("between
  2 and 12 entries")

**Don't start a sentence with a numeral.** Rephrase or spell it out.

**Use commas in numbers of five or more digits** in prose: "65,535", but
"4096". Never in code, values, hexadecimal, or anything the reader types.

**Use IEC binary prefixes for binary quantities**: KiB, MiB, GiB, TiB. Use
KB, MB, and GB only for decimal quantities, such as disk capacity as sold or
network throughput. Put a space between the number and the unit: "64 KiB",
"100 ms". Percentages take no space: "5%".

**Write hexadecimal with a `0x` prefix and uppercase digits** in prose and
tables: `0x1F`, `0xC0000022`. Code examples follow the code's own style.

**Write dates as "October 15, 2026"** in prose. Use ISO 8601 (`2026-10-15`,
`2026-10-15T08:30:00Z`) in tables, frontmatter, logs, and anything machine
read. Don't write dates as `15/10/2026` or `10/15/2026`.

**Write times in 24-hour form with a time zone** where one matters: "14:30
UTC".

## Formatting text

**Use code formatting for anything literal**: commands, flags, file names
and paths, registry paths and value names, event and field names,
identifiers, data types, constants, environment variables, and values the
reader enters or sees.

- Do: "Set `LogLevel` under `Machine\System\Network` to `3`."
- Don't: "Set LogLevel under Machine\System\Network to 3."

Code spans are not prose. Don't translate them, inflect them, or split them:
`size_installed`, not "size installed" or "`size_installed`s". Write "the
`--force` flag", "each `Precedence` value".

**Use bold for UI elements the reader acts on**, written exactly as they
appear: "Select **Apply**." Bold also marks the term being defined in a
definition list. Use it sparingly for anything else.

**Use italics only for a placeholder in prose** ("replace *name* with the
service's name") and for the titles of external books. Don't use italics
for emphasis; restructure the sentence instead.

**Write keyboard keys with a capital and join combinations with `+`**:
<kbd>Ctrl</kbd>+<kbd>C</kbd>, <kbd>Enter</kbd>, <kbd>Super</kbd>.

**Write placeholders in code as `<name>`**: lowercase, hyphenated, in angle
brackets: `svctl status <service-name>`. Explain each placeholder directly
after the example that uses it. Optional parts go in square brackets:
`[--verbose]`.

## Links

**Make the link text say where it goes.** The text should make sense read
on its own, as screen readers present it.

- Do: "Check the term in the [word list](~psc/word-list)."
- Don't: "To check the term, [click here](~psc/word-list)."

**Use `~` page references for links within the site**, never a pasted URL.
Trail checks them at build time.

**Link the first useful mention on a page**, not every mention.

**Don't use bare URLs in prose.** Give the link a name.

**Don't refer to position.** Avoid "above", "below", "the previous section",
and "the following". Name or link the thing instead: "the table of exit
statuses". The one exception is a sentence that directly introduces a list,
table, example, or set of steps.

## Page structure

**Every article has frontmatter with `title` and `description`.** Articles
in topics also carry `type`.

- `title` names the subject in title case. "Registry Layers", not "How
  Registry Layers Work" or "About Layers".
- `description` is one sentence saying what is on the page, naming the
  specific things it covers. It is what search results and link previews
  show. Don't restate the title.
- `type` is `concept` (explains how something works or why), `how-to`
  (walks through a task), or `reference` (lists facts to look up). Choose the
  one that describes most of the page; if a page is evenly two types, split
  it.

**Start with the point.** The first paragraph says what the page is about
and why the reader cares. Don't open with a heading; the title is already
there. Don't repeat the title as a heading.

**Use `##` for top-level headings and don't skip levels.** Use `###` only
under a `##`, and avoid `####`; a page that needs it should be split.

**Make headings short and specific.** No end punctuation, no code-only
headings unless the page is a reference to that identifier. Don't put two
headings in a row with no text between them.

**Wrap prose at 78 columns** in the source. Tables, code blocks, and lines
dominated by a link are exempt. A one-word change then produces a one-line
diff.

## Lists

**Use a bulleted list for items in no particular order** and a numbered
list for a sequence or a ranking.

**Introduce every list** with a sentence or fragment ending in a colon.

**Keep items parallel.** Every item starts with the same part of speech:
all verbs, all nouns, all complete sentences.

**Capitalize the first word of every item.**

**Keep lists short.** Two to seven items. A list with one item is a
sentence; a list with more than seven usually wants grouping, a table, or
subheadings.

**Use a list with bold lead-ins** when each item needs a label and a short
explanation:

- **Machine layer.** Settings that apply to every user.
- **User layer.** Settings that apply to one account.

## Tables

**Use a table when items share two or more attributes.** A list of names
with one description each is a list, not a table.

**Introduce every table** with a sentence.

**Give every table a header row.** Header cells use sentence case.

**Don't leave a cell empty.** Write "None", "Not applicable", or `—` (an em
dash alone means "none") and use that choice consistently within the table.

**Keep cells short.** If a cell needs more than one sentence, the content
probably belongs in prose with a heading.

## Procedures

**Number the steps of a procedure that has two or more steps.** A
single-step procedure is a sentence, not a list.

**Put prerequisites before the first step**, as a list headed by a short
sentence: "Before you start:" or a `## Before you start` heading.

**Write one action per step.** Two very short actions on the same screen
can share a step: "Select **Users**, then select **Add**."

**Say where before what.** "In the Registry Editor, select
**Machine**." The reader finds the place first, then acts.

**Start each step with the verb**, or with the location then the verb.

**State the result when it is not obvious**, as the last sentence of the
step or as a new step: "The service restarts and its status changes to
**Running**."

**Keep procedures to 10 steps or fewer.** Split a longer one into
procedures with their own headings.

**Put optional steps in the step itself**: "Optional: set a description."

## Code examples

**Every example works.** Copy it, run it, and it does what the text says.
Don't publish an example that has not been run against the version of
Peios the page describes.

**Tag every fenced block with its language**: `sh`, `c`, `rust`, `go`,
`toml`, `json`, and so on. Use `text` for output and for anything with no
language.

**Write shell commands without a prompt.** The copy button copies the whole
block, and a `$` breaks the pasted command.

```sh
svctl restart netd
```

**Put output in a separate `text` block** after the command, introduced by
a sentence such as "The output looks like this:".

**Show only what the example needs.** Cut unrelated lines and mark the cut
with a comment in the example's language.

**Use the placeholder rules in code**: `<service-name>`, never `foo`,
`bar`, or `example123`. Use realistic sample values where a placeholder
would make the example harder to follow, and use the reserved example
ranges: `example.com`, `192.0.2.0/24`, `2001:db8::/32`.

**Introduce every example** with a sentence saying what it does, and explain
anything non-obvious after it.

## Admonitions

Admonitions interrupt the reader. Use them only when the text would be
missed or misread without one, and never two in a row. Each type has one
job:

| Type | Use for |
|---|---|
| `> [!NOTE]` | An aside worth knowing that doesn't belong in the flow. |
| `> [!TIP]` | A better or faster way to do what the page describes. |
| `> [!IMPORTANT]` | Something a reader who skims will regret missing. |
| `> [!WARNING]` | Something that will go wrong if the reader ignores it. |
| `> [!CAUTION]` | Something that will go irreversibly wrong, such as data loss or lock-out. |

**State the consequence and the action.** "Removing this key locks every
account out of sign-in. Export the key before you change it."

**Don't use an admonition to hold ordinary content** that happens to be
important. If everything on a page is important, nothing is.

## Images and diagrams

**Use a diagram when a relationship is easier to see than to read**: a
flow, a hierarchy, a state machine. Don't use one to decorate.

**Give every image alt text** that says what it shows, not what it is:
"The token passes the DACL check, then the SACL check", not "Diagram".

**Don't use screenshots for anything the reader could copy.** Show commands,
output, and code as text.

**Crop screenshots to the relevant part of the window** and don't include
personal data.

## Sources

The rules on this page are based on the
[Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/)
and, for man page conventions, on
[man-pages(7)](https://man7.org/linux/man-pages/man7/man-pages.7.html).
They are restated here so that this page is the one place to look. Where
this page and either source differ, this page is correct for Peios.
