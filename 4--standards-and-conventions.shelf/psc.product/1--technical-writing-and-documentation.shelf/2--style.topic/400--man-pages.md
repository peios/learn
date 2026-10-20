---
title: Man Pages
type: reference
description: How to write Peios man pages, covering sections, the header and
  NAME lines, the required section order, roff formatting conventions, the
  CONFIGURATION, SECURITY, and EVENTS sections, API pages, and patching pages
  adopted from upstream.
---

Man pages are the thorough technical reference for everything a user,
administrator, or developer touches directly: commands, daemons, files,
system calls, and library functions. A man page records every flag, exit
status, file, environment variable, and error, including the edge cases
learn leaves out. [Core Style](~psc/core-style) applies to the prose; this page
adds the structure and formatting rules of the form.

## Where pages live

Each component keeps its man pages in its own repository, at
`man/<name>.<section>`, beside the code they describe. A change to the
behavior and the change to its page go in the same commit.

Pages are written in roff, using the `man(7)` macros (`.TH`, `.SH`, `.TP`,
`.B`, `.I`, `.BR`, and so on). Don't use the `mdoc(7)` macros.

## Sections

Put each page in the section that matches what it documents:

| Section | Contents |
|---|---|
| 1 | Commands any user can run |
| 2 | System calls, including Peios kernel interfaces |
| 3 | Library functions, including libpeios |
| 4 | Device and special files |
| 5 | File formats and configuration files |
| 7 | Overviews, conventions, and miscellaneous topics |
| 8 | Administration commands and daemons |

A command that only an administrator can usefully run goes in section 8,
even if any user can start it.

## The header and NAME lines

The `.TH` line gives the page name in uppercase, the section, the date of
the last change to the page's content in ISO 8601 form, and the source as
`Peios` followed by the package name and version:

```text
.TH NET 1 2026-09-14 "Peios netd 0.1.1"
```

Leave out the fifth argument; the formatter supplies the standard manual
title for the section.

The NAME section is one line: the name, an escaped dash, and a description
in lowercase with no final period. The description is what `apropos` and
`whatis` show, so make it specific.

```text
.SH NAME
net \- inspect and control the Peios network manager
```

## Section order

Use these sections, in this order, and only those that apply. Section
headings are in uppercase.

| Section | Required for | Contents |
|---|---|---|
| NAME | All | One line, as described in the header and NAME rules. |
| SYNOPSIS | All | Every form of invocation, or the declarations a program uses. |
| DESCRIPTION | All | What it is and what it does, starting with the common case. |
| COMMANDS | Commands with subcommands | Each subcommand, as a tagged paragraph. |
| OPTIONS | Commands with options | Every option, as a tagged paragraph. |
| CONFIGURATION | Programs that read the registry | The registry keys read, pointing to regman. |
| SECURITY | Anything that checks access | The rights, privileges, and descriptors involved. |
| EXIT STATUS | Sections 1 and 8 | Every exit status and what it means. |
| RETURN VALUE | Sections 2 and 3 | What the call returns on success and failure. |
| ERRORS | Sections 2 and 3 | Every error value and the condition that produces it. |
| ENVIRONMENT | Anything that reads environment variables | Every variable and its effect. |
| FILES | Anything that reads or writes files | Every path and what it holds. |
| SIGNALS | Daemons | Every signal handled and its effect. |
| EVENTS | Anything that emits events | The event types emitted, pointing to evman. |
| NOTES | Optional | Details that matter but fit nowhere else. |
| BUGS | Optional | Known defects that a user is likely to meet. |
| EXAMPLES | Commands beyond the trivial | Worked invocations with explanation. |
| SEE ALSO | All | Related pages. |

A page that needs a section not in this list can add one, placed where it
reads best. Keep its heading short and in the same style, such as
READINESS or MULTICALL NAMES.

## Writing the sections

**SYNOPSIS** shows syntax, not explanation. Literal text is bold, arguments
the reader replaces are italic, and optional parts are in square brackets.
Put each form of a command with subcommands on its own line.

**DESCRIPTION** opens with a sentence saying what the program does, with the
program's name as its subject: "**net** is the stateless operator client for
**netd**(8)." Describe behavior in the present tense. Address the reader as
"you" only where a sentence is about what the reader does.

**OPTIONS** documents every option. For each one, give:

- the short and long forms, and the argument it takes,
- what it does, including its default when not given,
- how it interacts with other options, and
- any right or privilege it needs.

Order options alphabetically by their long form, unless a different order
is clearer for the reader, such as grouping by purpose on a page with many
options.

**CONFIGURATION** names the registry keys the program reads and says what
they control as a whole. It doesn't document individual values; regman owns
those. End the section by pointing the reader there:
"Each value is documented in **regman**(1); run
**regman Machine\\System\\Network**."

**SECURITY** says what access the program checks, and against which security
descriptor: which rights each operation needs, which privileges change its
behavior, and what the default descriptor allows. Say also what the program
deliberately does not allow, when a reader coming from another system would
expect it.

**EXIT STATUS**, **RETURN VALUE**, and **ERRORS** list every value, each as a
tagged paragraph. Don't write "a non-zero value on failure" when the program
uses distinct values. A first-party program's exit statuses follow
[Command-Line Help and Errors](~psc/command-line-help-and-errors): 0 for
success, 1 for failure, 2 for a usage error, and 3 upward for anything more
specific.

**SYNOPSIS** and **OPTIONS** must agree with the program's `--help` output.
Change them in the same commit.

**EVENTS** lists the event types the program emits, one per line, and
points to **evman**(1) for their meaning and fields. Don't describe the
fields in the man page.

**EXAMPLES** gives each example as a command in bold, followed by a sentence
saying what it does and what to expect.

**SEE ALSO** lists related pages as `.BR name (section)`, separated by
commas, ordered by section number and then alphabetically, with no final
period. A relevant learn page can follow as a URL on its own line.

## Formatting conventions

roff has no code formatting, so the typeface rules differ from the rest of
Peios documentation:

| Bold (`.B`) | Italic (`.I`) |
|---|---|
| Command, program, and function names | Arguments and placeholders the reader replaces |
| Options and literal keywords | File and directory paths |
| Registry paths and value names | Titles of external documents |
| Event names, constants, rights, and privileges | |
| Environment variable names | |
| Literal input and output | |

Refer to another man page as the name in bold followed by the section in
parentheses: `.BR netd (8)`. Placeholders are italic words, such as
*interface*, not the `<name>` form used elsewhere.

Escape characters that roff treats specially:

- Write a hyphen-minus in an option or command as `\-`, so `--force` is
  `\-\-force`. A plain `-` can render as a hyphen that doesn't paste.
- Write a backslash as `\\`, so `Machine\System\Network` is
  `Machine\\System\\Network`.
- Start a line with `\&` when it would otherwise begin with a period or an
  apostrophe.

Start every sentence on a new line in the source. roff then spaces
sentences correctly, and a change to one sentence changes one line. This
replaces the 78-column wrapping rule for man page sources; still break a
sentence that runs past 78 columns at a natural phrase boundary.

Don't use admonitions, or tables built with `tbl` where a list of tagged
paragraphs would do. Avoid em dashes, because they render inconsistently in
terminals; where one is truly needed, write `\(em` with a space on each
side.

## API pages

Pages in sections 2 and 3 document programming interfaces.

- **One page per function**, or per group of functions that are always used
  together, such as a create and destroy pair. Give every function in a
  group its own NAME entry.
- **SYNOPSIS** shows the `#include` lines and full prototypes exactly as the
  header declares them.
- **DESCRIPTION** covers every argument, every flag value, ownership of
  memory and handles, and thread safety.
- **ERRORS** lists every error the call can return, with the condition that
  produces it. If the call can return errors the page does not list, the
  page is incomplete.
- Bindings for other languages, such as Rust or Go, document themselves with
  their language's own tools and point to the man page for the semantics.

## Pages adopted from upstream

Peios ships man pages from upstream projects, such as coreutils. Where Peios
behaves differently from upstream, the page is patched to describe Peios.
Peios does not ship a page it knows is inaccurate.

- **Correct, don't restyle.** Change only what is inaccurate for Peios.
  Leave upstream's wording, structure, and style alone, so the patch stays
  small and survives the next upstream update.
- **Describe Peios, not the difference.** Write the patched text as if the
  page had always described Peios. Don't add "On Peios, …" notes or a
  separate Peios section.
- **Keep the patch with the package.** The change lives in the package's
  patch series, beside any code patches, with a description saying what
  behavior it corrects.
- **Patch when the behavior changes.** A Peios change that makes an adopted
  page inaccurate includes the patch to that page.

Core Style's spelling and wording rules don't apply to upstream text you
leave unchanged. Text you add or replace follows them where it can do so
without reading oddly against the surrounding page.
