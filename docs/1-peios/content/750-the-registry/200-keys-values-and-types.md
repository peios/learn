---
title: Keys, values, and types
type: concept
description: "The registry's data model is deliberately small — a tree of keys, each holding named typed values, and nothing else. This page covers that two-level structure, the value type set, the rules for names and case, and the one property everything later depends on: the registry stores a value's type but never interprets its data."
related:
  - peios/the-registry/overview
  - peios/the-registry/configuration-and-meaning
  - peios/the-registry/layers
  - peios/the-registry/access-control
  - peios/file-access/overview
---

The registry's data model has exactly two kinds of thing in it: **keys** and **values**. A key is a node in the tree — a container that holds child keys and values. A value is a leaf — a named, typed piece of data living inside a key. There is no third kind of thing, and the nesting only ever happens through keys. That smallness is deliberate, and it is worth getting precise about before anything else, because every later idea is built on this shape.

## Two levels, and only two

Keys nest; values do not. A key can contain other keys (its subkeys) and it can contain values, but a value cannot contain anything — it is always a leaf. You cannot put a value "inside" another value, and there is no record type between a key and a value.

| | Holds | Held by | Role |
|---|---|---|---|
| **Key** | Subkeys and values | Its parent key | The container — the registry's directories |
| **Value** | Nothing (a leaf) | Exactly one key | The data — the registry's files |

This two-level rule is a hard constraint, not a convention. When you want structure, you make subkeys; when you want data, you make values. There is no other axis.

## Keys

A **key** is identified by its path — `Machine\System\KMES` names a key three levels down from the `Machine\` hive root. Each key holds its children and its values, and each key is a first-class secured object with its own [security descriptor](~peios/the-registry/access-control); that is what makes "who can read or change this configuration" a per-key decision.

A few naming rules apply to each component of a path (each segment between separators):

- Any UTF-8 is allowed in a key name **except** backslash, forward slash, and the null byte. Backslash is the separator; forward slash is accepted on input and normalised to a backslash; null is never allowed.
- Components cannot be empty. `Machine\\System` (a doubled separator) and a trailing separator are both invalid.

Every key also has one **default value** — the single value whose name is the empty string. It is the key's "main" value, the one you get when you read the key without naming a value. Most keys also carry additional named values alongside it.

## Values

A **value** is a `(name, type, data)` triple stored in a key. A key can hold many values, each with a distinct name, plus the one unnamed default value.

Value names follow almost the same rules as key names, with one difference: **backslash and forward slash are allowed** in a value name. Value names are not paths — they are not hierarchical — so a separator inside one has no special meaning. Only the null byte is forbidden, and the empty string is reserved for the default value.

## The value types

A value's **type** is a small tag stored alongside its data. The full set:

| Type | Holds |
|---|---|
| `REG_DWORD` / `REG_QWORD` | A 32-bit / 64-bit integer. |
| `REG_DWORD_BIG_ENDIAN` | A 32-bit integer in big-endian byte order. |
| `REG_SZ` | A string. |
| `REG_EXPAND_SZ` | A string containing references to be expanded (e.g. environment variables) by whatever reads it. |
| `REG_MULTI_SZ` | An array of strings. |
| `REG_BINARY` | Raw bytes with no further structure. |
| `REG_LINK` | A symbolic-link target. The one type the registry acts on itself — see [Advanced: registry links](~peios/the-registry/registry-links). |
| `REG_NONE` | No type / no meaningful data. |

There are also three hardware-resource types carried over for format fidelity. Peios assigns them no meaning — they behave exactly like `REG_BINARY` and the registry never produces them itself. You will essentially never author one.

## Typed, but opaque

Here is the property the rest of the topic leans on. The registry stores a value's type tag and its raw bytes, and that is **all** it does with them. It does not check that the bytes match the type. It does not parse a `REG_DWORD` into a number. It does not know that `Machine\System\KMES\BufferCapacity` is supposed to be a power of two, what its default is, or which subsystem reads it. The single exception is `REG_LINK` on a link key, which the kernel follows during path resolution.

So "typed" here means **tagged**, not **validated**. The type travels with the value so that a reader knows how to interpret the bytes — but the interpreting, the validating, and the deciding-what-to-do are all somebody else's job.

Two consequences follow immediately, and both get their own treatment:

- The registry can hold a value for a subsystem that is not even running, or a setting nobody has read yet. Storage does not require a reader.
- Whether a value is *valid* is never the registry's verdict. That belongs to whatever reads it — which is the whole subject of [Configuration, not storage](~peios/the-registry/configuration-and-meaning).

## Names, case, and paths

Paths use the backslash as their canonical separator. A forward slash is accepted on input and normalised to a backslash, so `Machine/System/KMES` and `Machine\System\KMES` name the same key; the stored, canonical form always uses backslashes.

Comparison is **case-insensitive but case-preserving**. `KMES` and `kmes` resolve to the same key, but the registry keeps whatever case you wrote for display. The matching uses a fixed Unicode case-folding rule, so it does not depend on locale.

One sharp edge: there is **no Unicode normalisation**. Two different byte sequences that render as the same character (a precomposed `é` versus `e` plus a combining accent) are two *different* keys. Case is folded; representation is not.

## Volatile keys

A key can be created **volatile**, meaning it is stored only in memory and disappears on reboot or when its store unloads. It is the registry's home for runtime-only state that should never survive a restart. Volatility is fixed at creation, and there is one structural rule: the children of a volatile key must themselves be volatile (you cannot place a persistent key under a non-persistent one).

Watch the word, because it collides with a different idea. "Volatile" describes **storage persistence** — does this key survive a reboot. It says nothing about **how quickly a configuration change takes effect** — whether editing a setting applies live, on service restart, or only on reboot. That second property belongs to each individual setting and is recorded in `regman` as its `applies` field. A value can live in a perfectly persistent (non-volatile) key and still only take effect on reboot. Keep the two apart.

## Where to start

If you want the idea that the registry stores values it does not understand — what `regman` documents, what "reject-or-keep" means, and why the value the registry shows can differ from the value a subsystem is using — read [Configuration, not storage](~peios/the-registry/configuration-and-meaning).

If you want the layered truth beneath the single value you read — precedence, the base layer, and automatic revert — read [Layers](~peios/the-registry/layers).

If you want the security model — why every key carries a security descriptor and what the registry-specific access rights are — read [Access control on keys](~peios/the-registry/access-control).
