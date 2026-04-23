---
title: Binary Packing
type: concept
description: Build and parse binary structs in Lua with provium.pack() and provium.unpack() — the foundation for syscall and ioctl arguments.
related:
  - provium/kernel-testing/raw-syscalls
  - provium/kernel-testing/ioctl
---

Kernel interfaces work with binary structs — fixed layouts of integers at specific byte offsets. Provium provides `pack` and `unpack` functions for building and parsing these structs directly in Lua.

## Packing

`provium.pack(fmt, ...)` converts values into a binary string according to a format specifier:

```lua
-- A struct with two u32 fields and one u64 field
local data = provium.pack("u32 u32 u64", 1, 42, 0)
-- data is a 16-byte string: [01 00 00 00] [2A 00 00 00] [00 00 00 00 00 00 00 00]
```

The format string is a space-separated list of type specifiers. Each specifier consumes one value argument.

### Format types

| Specifier | Size | Range |
|---|---|---|
| `u8` | 1 byte | 0 to 255 |
| `u16` | 2 bytes | 0 to 65535 |
| `i16` | 2 bytes | -32768 to 32767 |
| `u32` | 4 bytes | 0 to 4294967295 |
| `i32` | 4 bytes | -2147483648 to 2147483647 |
| `u64` | 8 bytes | 0 to 2^64-1 |
| `i64` | 8 bytes | -2^63 to 2^63-1 |

All values are encoded in **little-endian** byte order.

## Unpacking

`provium.unpack(fmt, data)` extracts values from a binary string:

```lua
local a, b, c = provium.unpack("u32 u32 u64", data)
```

The format string works the same as `pack`. Each specifier produces one return value. The data must be long enough to satisfy all specifiers — if it is too short, an error is raised.

## Concatenation

Packed strings are regular Lua strings. You can concatenate them to build complex structures piece by piece:

```lua
-- Build a SID: revision, sub-authority count, authority, sub-authorities
local sid = provium.pack("u8 u8 u8 u8 u8 u8 u8 u8",
    1, count, 0, 0, 0, 0, 0, authority)
for _, sa in ipairs(sub_authorities) do
    sid = sid .. provium.pack("u32", sa)
end
```

This is how the KACS test helper library builds SIDs, ACEs, ACLs, and security descriptors.

## Practical examples

### Building a SID

A Windows-compatible Security Identifier (SID):

```lua
function build_sid(authority, sub_authorities)
    local count = #sub_authorities
    local sid = provium.pack("u8 u8 u8 u8 u8 u8 u8 u8",
        1, count, 0, 0, 0, 0, 0, authority)
    for _, sa in ipairs(sub_authorities) do
        sid = sid .. provium.pack("u32", sa)
    end
    return sid
end

local SID_SYSTEM = build_sid(5, {18})          -- S-1-5-18
local SID_EVERYONE = build_sid(1, {0})         -- S-1-1-0
local SID_ADMINS = build_sid(5, {32, 544})     -- S-1-5-32-544
```

### Building an ACE

An Access Control Entry with a header and a SID:

```lua
function build_allow_ace(mask, sid)
    local ace_size = 4 + 4 + #sid
    -- Pad to 4-byte alignment
    while ace_size % 4 ~= 0 do ace_size = ace_size + 1 end
    local ace = provium.pack("u8 u8 u16 u32",
        0x00,       -- type: ACCESS_ALLOWED
        0x00,       -- flags
        ace_size,   -- size
        mask)       -- access mask
        .. sid
    while #ace < ace_size do ace = ace .. "\0" end
    return ace
end
```

### Building an ACL

An Access Control List containing ACEs:

```lua
function build_acl(aces)
    local ace_data = ""
    for _, ace in ipairs(aces) do
        ace_data = ace_data .. ace
    end
    local acl_size = 8 + #ace_data
    return provium.pack("u8 u8 u16 u16 u16",
        2,           -- revision
        0,           -- pad
        acl_size,    -- size
        #aces,       -- ace count
        0)           -- pad
        .. ace_data
end
```

### Parsing a kernel response

After a syscall or ioctl returns output data:

```lua
local ret, out = vm:ioctl(fd, KACS_IOC_QUERY, args)
assert(ret == 0)

local class, buf_len = provium.unpack("u32 u32", out)
```

## Precision note

Lua uses double-precision floating point for all numbers. This gives exact integer representation up to 2^53. Values above this — such as `u64` privilege bitmasks with high bits set — may lose precision. The KACS test helpers work around this by combining privileges using addition rather than bitwise OR, and by avoiding the highest bits in privilege constants where possible.
