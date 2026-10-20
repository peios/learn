---
title: String Format
description: The S-R-I-S string form of a SID — how each component is rendered, and the rules for parsing one back.
---

SIDs are represented in string form as:

```
S-1-{authority}-{sub1}-{sub2}-...-{subN}
```

Where:

- `S` is a literal prefix.
- `1` is the revision number.
- `{authority}` is the IdentifierAuthority. If the upper 2 bytes are
  zero, this is the decimal representation of the lower 4 bytes.
  Otherwise, it is the lowercase hexadecimal representation of all
  6 bytes, zero-padded to 12 hex digits and prefixed with `0x`.
- Each `{subN}` is the decimal representation of the corresponding
  32-bit sub-authority.

> [!NOTE]
> Example SIDs: `S-1-5-18` (Local System), `S-1-5-32-544`
> (BUILTIN\Administrators),
> `S-1-5-21-3623811015-3361044348-30300820-1013` (a domain user).
> The meanings of well-known SID values are catalogued in §4.4.
