---
title: Mount Options
description: The single filesystem-specific mount parameter stratafs registers, its escaping and parse failures, generic flags, and remount.
---

stratafs registers exactly one filesystem-specific mount parameter,
`strata`, and rejects every other name. [*mount.only-strata-option] There is no option to select a
security descriptor, an access-check behaviour, an inode-numbering
scheme, or a caching mode.

```
strata=<stratum>[:<stratum>]...
<stratum> := <path>[+<flag>]...
<flag>    := create | ro | am
```

Strata are separated by `:` and given highest-precedence first. Each
stratum is an absolute path, optionally followed by flags, each
introduced by `+`. [*mount.strata-option-syntax]

```
strata=/system/retc:/lcl/etc+create:/usr/etc+ro
```

`:` separates strata rather than `,` because a mount options string is
itself comma-separated when passed through the legacy mount interface,
which would otherwise split the value.

## Escaping [*mount.escape-set]

Within a path, a literal `:`, `+`, `,` or `\` is escaped by a preceding
`\`. Those four characters are the entire escapable set; the escaped
byte is stored literally, and the backslash is consumed.

Because the legacy `mount(2)` data is one comma-separated string,
stratafs replaces the VFS's monolithic option splitter with one that
honours backslash escapes, so that an escaped comma inside a stratum
path survives the split rather than being read as an option boundary.

## Parse failures

Every malformed value is refused with `EINVAL`. The parser consumes the
whole string and errors on any byte it cannot classify; there is no
skip-and-continue path, so nothing it does not understand is silently
ignored. [*mount.parse-failure-einval]

| Condition | |
|---|---|
| The `strata=` option is absent | There is no default stack [*mount.parse.strata-absent] |
| Its value is empty | [*mount.parse.empty-value] |
| An element between two separators is empty, or the value begins or ends with a separator | [*mount.parse.empty-element] |
| A path is not absolute | Tested on the raw first byte, which is exact since `/` is not escapable [*mount.parse.path-must-be-absolute] |
| A path is empty after unescaping | Defensive; the absolute-path test already guarantees one byte [*mount.parse.empty-after-unescape] |
| An unescaped `,` appears in a path, or inside a flag token | The option string is comma-separated at the outer level [*mount.parse.unescaped-comma] |
| A `\` appears at the end of the value, or before a character that is not `:`, `+`, `,` or `\` | A dangling or meaningless escape [*mount.parse.invalid-escape] |
| A `+` is followed by no flag, or by an unrecognised one | Flag names are matched by exact length and content [*mount.parse.unknown-flag] |
| The same flag appears more than once on one stratum | [*mount.parse.duplicate-flag] |
| More than 16 strata | The array bound is reached mid-parse [*mount.parse.too-many-strata] |
| `strata=` appears twice in one option string | [*mount.parse.duplicate-strata-option] |

Two paths return `ENOMEM` rather than `EINVAL`, both allocation
failures during parsing. Nothing bounds a stratum path at parse time:
an over-long one is accepted here and fails later with `ENAMETOOLONG`
when the joined path exceeds `PATH_MAX` during a resolution. [*mount.overlong-path-enametoolong]

The stack-wide conditions — an empty stack, two `create` strata, a
stratum carrying both `create` and `ro` — are checked separately, after
parsing and before any path is resolved. They depend on nothing but the
option string, so they are reported whatever the caller's access
(§4.2.3).

## Generic mount flags [*mount.read-only-refuses-all-mutation]

Generic flags apply as they do to any filesystem, with one addition. A
stratafs mount may be mounted read-only, and the superblock's read-only
state is the **first** term of the routing decision, short-circuiting
before the provider or the create stratum is considered at all. It
therefore refuses every mutation with `EROFS` regardless of the stratum
stack, and is both independent of and stricter than a stack with no
create stratum.

Locking and synchronising are unaffected. Neither modifies an object,
neither consults the superblock's read-only state, and a reader of a
merged tree may need both. [*mount.locking-unaffected-by-read-only]

## Remount [*mount.remount-rejects-a-changed-stack]

A remount may alter generic mount flags. It may not alter the stack: a
remount supplying a `strata=` whose value differs from the mounted
one's is refused with `EINVAL`.

The test is on the value, not on the presence of the parameter, so a
remount that replays the current stack byte-for-byte is accepted — it
adds, removes, reorders and re-flags nothing. [*mount.remount-accepts-an-identical-stack] That is what makes
option-string replay work: a tool reconstructing the whole option
string from the mount table and handing it back is doing exactly this,
and flipping a stratafs mount read-only would otherwise fail on a
`strata=` that changed nothing.

The comparison is of the stored option string (§4.2.2, below), which is
why that string being reported without a second escaping layer is what
lets a replayed stack compare equal at all.

## The mount table [*mount.options-reported-verbatim]

The stack is reported in the filesystem options the kernel exposes for
mounts, so it is discoverable by anything that can read the mount
table, which on Linux is unprivileged. What is stored for this purpose
is the caller's own option string, kept verbatim at parse time: nothing
is abbreviated, no stratum is omitted, no path is canonicalised, and an
absent stratum is reported like any other, because the string is fixed
at mount and never filtered by what currently exists.

The filesystem type is reported as `stratafs`.

The value is emitted through the kernel's `seq_show_option`, which
applies its own escaping — octal for `,`, `\`, and whitespace — on top
of the escaping the value already carries. For a path containing none
of `: + , \` or whitespace, which is the ordinary case, the reported
value is byte-identical to what was supplied. For a path containing any
of them it is not reconstructable: a stored `\:` is re-escaped to
`\134:`, which reads back as a dangling escape. This is tracked as a
defect.
