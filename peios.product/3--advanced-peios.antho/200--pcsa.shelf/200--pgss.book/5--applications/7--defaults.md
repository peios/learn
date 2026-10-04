---
title: Defaults
description: Which application opens a type of file when several could — the person's choice, else the machine's — where each is kept in the registry, how a consumer finds the default from them, and who may set them.
---

A person may choose which application opens a type of file, and so may
whoever administers the machine, for everyone on it. Each such
**choice** is one value in the registry. The **default** for a media
type is the application the choices give it, by the rules of this
section, and it is what a consumer that picks among the candidates
(§5.6) opens a file with.

## Where choices are kept

There are two places, each a registry key:

| Key | Whose choices |
|---|---|
| `CurrentUser\Generic\Applications\Defaults` | The person's. The kernel routes `CurrentUser\` to the caller's own `Users\<SID>\`, so each person has their own. |
| `Machine\Generic\Applications\Defaults` | The machine's: everyone's on it, for whatever they have not chosen themselves. |

Each value of either key is one choice:

| Part | Is |
|---|---|
| Name | A media type pattern (§5.2): the type the choice is for, `image/png`, or a top-level type and `*`, `image/*`. |
| Type | `REG_SZ`. |
| Data | The id (§5.3) of the application chosen, in UTF-8, with or without a terminating NUL. |

The registry compares value names ignoring case, as media types are
compared (§5.6), so one key holds at most one choice for a type however
it is spelt. A writer SHOULD write the name in lowercase. A consumer
reads the name ignoring case, and the data with leading and trailing
whitespace removed.

A value whose name is not a media type pattern, whose type is not
`REG_SZ`, or whose data is not in the form of an id is no choice. A
consumer passes over it, SHOULD say on its own log which value it
passed over and why, and goes on to the rest of the key.
[*applications.defaults.malformed-value-is-no-choice]

A key that is absent has no choices, and neither has one the consumer
may not read. Neither is an error. Anything in either key other than
its values, such as a subkey, is reserved (§5.8) and a consumer MUST
ignore it.

The person's choices are those of the person the file is opened for. A
consumer that runs as that person reads them through `CurrentUser\`. A
consumer that runs as anyone else MUST NOT read its own `CurrentUser\`
for them, since that is its own key and not the person's; it reads the
person's `Users\<SID>\Generic\Applications\Defaults` if it may, and
otherwise uses the machine's choices alone.
[*applications.defaults.person-is-whom-the-file-is-opened-for]

## Finding the default

The default for a file whose media type is `type/subtype` is found by
trying these choices in order and taking the first that is usable:

1. the person's choice named `type/subtype`
   [*applications.defaults.order.person-exact]
2. the person's choice named `type/*`
   [*applications.defaults.order.person-pattern]
3. the machine's choice named `type/subtype`
   [*applications.defaults.order.machine-exact]
4. the machine's choice named `type/*`
   [*applications.defaults.order.machine-pattern]

A choice is **usable** for the file when the catalogue has a usable
declaration for the id it names (§5.3, §5.4), and that application is a
candidate to open the file (§5.6). A choice that is not usable is
passed over and the next is tried. It is never an error: an application
that has been removed, or that no longer says it opens the type, is
simply no longer anybody's default, and nothing need be done about the
choice that named it. A consumer MAY say on its own log that it passed
one over. [*applications.defaults.unusable-choice-is-passed-over]

When no choice is usable, the type has no default, and a consumer that
picks uses its own rule among the candidates (§5.6).

A choice selects among the candidates and never adds one. A consumer
MUST NOT open a file with an application that is not a candidate for
it, whatever a choice says.
[*applications.defaults.a-choice-adds-no-candidate]

> [!NOTE]
> The person's choices come before the machine's whichever is the more
> particular. A person who chooses one application for `image/*` means
> every image, including the types the machine has chosen something
> else for; the machine's choices are what a person has not decided,
> not what overrules them.

A consumer reads the choices when it picks, or remembers them under the
rule of §5.4 for a remembered catalogue: it MUST notice when either key
changes, or MUST say, in its own documentation, how stale a remembered
choice may be.

## Setting them

A person sets their own choices by writing values in their own key, and
clears one by deleting its value. Whoever may write the machine's key
sets the machine's in the same way. A writer creates each key of the
path that is not there yet, one level at a time: the registry creates
no key on the way to another.

Who may write each key is that key's security descriptor, and nothing
else. A system MUST let every person who can log on to a desktop read
the machine's key, and SHOULD let only administrators write it, as a
Peios system's `Machine` hive does from its root: SYSTEM and
Administrators have full control, and Authenticated Users read. A
person's own key is theirs by the descriptor of their part of the
`Users` hive.

A program that offers to set choices, such as a settings application,
MUST find out whether it may write a key by asking the registry: by
opening the key for writing values, or, where the key is not there yet,
the nearest key above it that is for creating subkeys. It MUST NOT
infer the answer from the groups the person is in, since the
descriptor, and not membership, is what the registry checks.
[*applications.defaults.a-writer-asks-the-registry]

A writer SHOULD offer, for a type, only the applications that are
candidates for it, and for a pattern `type/*`, only those that say they
open `type/*`. It is not an error to write anything else: a choice that
is not usable is passed over when it is read.

> [!NOTE]
> Any program running as a person can change that person's choices, as
> it can change anything else of theirs. This section does not try to
> prevent it, since a program running as the person could as easily do
> whatever it would have done by being the default. What it does
> prevent is a choice opening a file with something that is not a
> candidate, or with something a package did not install.
