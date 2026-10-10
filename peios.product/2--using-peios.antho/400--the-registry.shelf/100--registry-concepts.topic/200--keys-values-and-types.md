---
title: Keys, values, and types
type: reference
description: Address a key and value correctly, choose explicit value types, and distinguish stored data, defaults and volatile keys.
related:
  - peios/registry-concepts/overview
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/file-access/overview
---

A registry command usually takes a **key path** and a separate **value
name**. Keeping them separate avoids changing the wrong setting:

```sh
reg get Machine/System/KMES BufferCapacity
reg ls Machine/System/KMES -l
```

<a id="two-levels-and-only-two"></a>
<span id="keys-values-and-types--two-levels-and-only-two"></span>
<span id="registry-concepts-keys-values-and-types--two-levels-and-only-two"></span>
<span id="using-peios-registry-concepts-keys-values-and-types--two-levels-and-only-two"></span>
## Keys and values in a command

Keys contain subkeys and values; values do not contain other values.
`reg get KEY` lists the key's effective values. `reg get KEY NAME` reads
one value. The literal `@` in the value-name position addresses the
unnamed **default value**, if the key has one.

A key need not have a default value. A default value is also different
from a setting's *documented default*: a consumer may use a compiled-in
default when no registry value is present.

## Keys

`Machine\System\KMES` names a key. Its permissions cover the values it
contains. To give two values different permissions, put them in different
keys; there are no per-value permission lists.

Key-name components cannot contain `\`, `/` or a null byte. Empty
components, doubled separators and trailing separators are invalid.

## Values

A value has a name, a type tag and data. Unlike a key-name component, a
value name may contain `/` or `\`: it is not a path. The null byte is
forbidden; the empty name is reserved for the default value.

## The value types

Use the type the owning component documents in `regman`. For a command-line
write, an explicit prefix avoids unintended type inference:

| Type | Meaning to a reader | `reg set` prefix |
|---|---|---|
| `REG_DWORD` | 32-bit integer | `dword:` |
| `REG_QWORD` | 64-bit integer | `qword:` |
| `REG_DWORD_BIG_ENDIAN` | Big-endian 32-bit integer | `dword-be:` |
| `REG_SZ` | Text | `sz:` |
| `REG_EXPAND_SZ` | Text whose references the consumer expands | `expand:` |
| `REG_MULTI_SZ` | List of strings | `multi:` |
| `REG_BINARY` | Bytes | `hex:` or `bin:` |
| `REG_LINK` | A link target on a link key | `link:` |
| `REG_NONE` | No type | `none:` |

For example, `sz:007` preserves the text `007`. Without the prefix,
`reg` infers an integer and loses the leading zeros. See
[`reg` value literals](~peios/registry-tools/reg#value-literals-and-types)
for encoding lists, bytes and numbers.

The hardware-resource types are retained for format fidelity and have no
Peios-specific meaning. Byte encodings, including Peios UTF-8 strings and
link targets, are documented in the
[LCS value representation](~peios/lcs/the-data-model/values#tool-value-encodings).

## Typed, but opaque

The registry does not check whether ordinary value data is sensible for
its consumer. A known type tag can accompany malformed data, such as a
number with the wrong length. Registry Editor shows such data in red as
bytes. Unknown type codes and invalid requests can still be rejected;
"opaque" does not mean every write succeeds.

`REG_LINK` on a link key is the exception: the kernel interprets it to
resolve the target. For other settings, follow
[Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning).

## Names, case, and paths

`reg` accepts forward slashes and backslashes as path separators. In a
shell, use forward slashes or quote a backslash path:

```sh
reg get 'Machine\System\KMES' BufferCapacity
```

Names are case-insensitive and retain their display case. Case matching
is locale-independent, but there is no Unicode normalization: visually
identical names with different Unicode representations can be distinct.

## Volatile keys

A volatile key is held in memory and disappears on reboot or when its
store unloads. Its children must also be volatile. `reg info KEY` shows
whether a key is volatile; Registry Editor also shows this in the key pane.

Volatility is about persistence. It does not tell you when a setting
applies. A persistent setting may still require a reboot; check the
`regman` **Applies** field.

## Where to go next

- [Make and verify a change](~peios/registry-concepts/configuration-and-meaning)
- [Understand which layer wins](~peios/registry-layers/layers)
- [Check key permissions](~peios/registry-security/access-control)
