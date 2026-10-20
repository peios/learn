---
title: Learn
type: reference
description: How to write learn pages, the educational form of Peios
  documentation, covering the three page types, titles, page openings,
  references to prior art, how-to structure, linking to the forms that own
  each fact, and when a page should be split.
---

Learn is the educational form of Peios documentation. It is what a reader
opens to understand something: how a part of Peios works, why it is built
that way, and how to get a task done with it. Everything in
[Core Style](~psc/core-style) applies; this page adds the rules specific to
learn.

## Who learn is for

Learn is written for a reader who is new to the subject, not new to
computers. Assume they can use a terminal and read a configuration file.
Don't assume they know any other operating system: every page has to make
sense to a reader who has used neither Windows nor Linux.

Address the reader as "you". Use contractions where they read naturally.
Explain the reason behind a rule or a design decision whenever the reader
would otherwise have to take it on trust.

## Learn explains; other forms own the facts

Learn is never the authority for an interface detail. When a learn page
touches a flag, a registry value, or an event, it says what the reader needs
for the task in hand and links to the form that owns the full detail:

- **Commands, files, system calls, and library functions:** the man page.
  Refer to it by name and section, as `svctl(8)`.
- **Registry keys and values:** the regman page. Give the path, as
  `Machine\System\Network`.
- **Events and fields:** the evman page. Give the event or field name, as
  `kacs.audit.access.checked`.
- **Shared protocols and formats:** the specification section.
- **How one component works inside:** its technical reference manual.

Show the one or two flags or values a task needs. Don't reproduce an option
table, a list of every value under a key, or every field of an event; those
go stale in the copy and stay correct in the original.

Don't use the specification keywords **MUST**, **SHOULD**, or **MAY** in
learn. A learn page that needs to state a requirement links to the
specification that makes it.

## Page types

Every learn article is one of three types, set in its `type:` frontmatter.
Choose the type before writing; a page that tries to be two types does
neither well.

| Type | Answers | Title form | Example title |
|---|---|---|---|
| `concept` | How does this work, and why? | Noun phrase naming the subject | Logon Sessions |
| `how-to` | How do I get this done? | Gerund phrase naming the task | Configuring Network Profiles |
| `reference` | What are the values or options? | Noun phrase naming the set | Logon Types |

### Concept pages

A concept page explains one idea. Start with what the thing is and why it
exists, in two or three sentences, before any detail.

Use a diagram when the idea is a flow, a hierarchy, or a set of states. Keep
procedures out of concept pages; link to the how-to page instead.

### How-to pages

A how-to page gets one task done. Use this structure:

1. **The goal.** One or two sentences saying what the reader will have
   achieved and when they would want to.
2. **Before you start.** Prerequisites as a list: required privileges,
   packages, and anything that must already be configured. Leave the
   section out if there are none.
3. **The steps.** A numbered procedure, following the procedure rules in
   Core Style. Use subheadings when the task has distinct stages, each with
   its own procedure.
4. **Check the result.** How the reader confirms it worked: a command and
   its expected output, or what they will see.
5. **See also.** Optional. Two to five related pages.

Write for the common case. Put variations after the main procedure under
their own headings, rather than branching inside the steps.

### Reference pages

A reference page in learn collects facts that support understanding: the
set of logon types, the well-known SIDs, and the privileges and what each one
allows. It is not an interface reference; that belongs to man, regman,
and evman.

Open with one paragraph saying what the set is and how it is used, then
present it as a table or a list with bold lead-ins. Sort entries in the
order a reader is most likely to look for them: alphabetical by default,
numeric where the values are numbers.

## Openings

The first paragraph of every learn page says what the page covers and why
the reader would care, in plain terms. It is the paragraph a reader uses to
decide whether they are on the right page.

- Do: "A security descriptor records who owns an object and who can do what
  to it. Every access check Peios makes reads one, so understanding them
  explains most access-denied errors you will meet."
  <!-- lint-disable-next-line spelling -->
- Don't: "In this article, we will discuss logon sessions."

## Prior art

The opening can orient the reader by pointing to something they have almost
certainly met: a Windows or Linux equivalent, or a Peios concept covered
elsewhere. One or two sentences are enough to say "this is like that", and
where the likeness stops if that would otherwise mislead.

- Do: "If you have used Windows, a security descriptor will be familiar:
  Peios uses the same model of an owner, a discretionary access control list,
  and a system access control list."

After the opening, the page stands alone. Explain Peios in its own terms,
and don't refer to other operating systems or alternative software again. A
reader who skipped the comparison, or never knew the system it names, has
to be able to follow everything that comes after it.

- Do: "A deny entry takes effect only if it comes before any entry that
  grants the same access."
- Don't: "As on Windows, a deny entry takes effect only if it comes before
  any entry that grants the same access."

Software that Peios ships or interoperates with is not prior art. A how-to
page about configuring sshd names sshd throughout.

## Size and splitting

Keep a page readable in about 10 minutes. Split a page when:

- it covers two ideas that a reader could want separately,
- a how-to has become two tasks, or
- it needs a heading deeper than `###`.

Give each topic a clear scope and order its articles so a reader can go
through them in sequence: concepts first, then how-to pages, then
reference.

## Links and related pages

Link the first useful mention of another Peios concept to its page. Use
`related:` frontmatter for two to four pages a reader is likely to want
next. End a page with a **See also** section only when the related pages
need a sentence of explanation each; otherwise `related:` is enough.

## Examples

Use realistic examples drawn from a real Peios system: real paths, real
service names, real output. Every command must work as written on the
version of Peios the page describes. When an example depends on earlier
state, such as a service being installed, say so in the text before it.
