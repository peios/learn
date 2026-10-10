---
title: "mitigation.*"
description: "Every field the evman catalogue defines under mitigation: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `mitigation`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="mitigation.action"></a>`mitigation.action`

- **Type:** `str.enum`
- **Values:** `enable` · `disable` · `lock` · `unlock`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The direction of a change to a process mitigation's state. `enable` and
`lock` harden a process; `disable` and `unlock` loosen it, and are the
ones to read closely. A Peios mitigation is meant to persist once set, so
a permitted `disable` or `unlock` is unusual, and a refused one is a
process trying to weaken its own protection.

**Carried by:**

No event carries this field yet.

## <a id="mitigation.name"></a>`mitigation.name`

- **Type:** `str.enum`
- **Values:** `wxp` · `tlp` · `lsv` · `ui-access` · `no-child` · `cfif` · `cfib` · `pie` · `sml`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The single process mitigation a record is about, named for its
`KACS_MIT_*` bit: `wxp` write-XOR-execute, `tlp` trusted library paths,
`lsv` library signature verification, `no-child` the ban on creating
processes, `cfif` and `cfib` forward- and backward-edge control-flow
integrity, `pie` the refusal of non-PIE executables, `sml` the
speculation mitigation lock, and `ui-access`, which is reserved.

There is no `cfi`. The legacy `KACS_MIT_CFI` bit is an alias that sets
both `cfif` and `cfib` and is not itself kept, so a record names whichever
of the two it concerns.

**A request for `cfif` fails today on every live process**, because the
kernel offers no way to turn on IBT for a running task. A service that
asks for it is not protected by it, whatever it believes.

**Carried by:**

No event carries this field yet.

## <a id="mitigation.trusted-prefixes"></a>`mitigation.trusted-prefixes`

- **Type:** `str.path[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The path prefixes the trusted library paths mitigation (`tlp`) accepts. A
process under it may map a file executable only if the file's path begins
with one of these. Each entry begins and ends with `/` and is compared
byte for byte with the start of the path, without normalisation. At most
64, held in one table for the whole system.

These are prefixes, not files: a search for a file's path does not match
the prefix that admitted it. **An empty list trusts nothing** rather than
checking nothing, so a process under `tlp` is then refused every
file-backed executable mapping.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
