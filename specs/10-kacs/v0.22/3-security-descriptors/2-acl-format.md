---
title: ACL Format
---

An Access Control List (ACL) is the binary container for ACEs. DACLs, SACLs, and CAAP policy ACL blobs all use the same standard binary ACL format.

## Binary format

An ACL begins with an 8-byte header followed by `AceCount` ACEs packed contiguously:

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | AclRevision | ACL revision number. Determines which ACE families the ACL formally permits. |
| 1 | 1 | Sbz1 | Reserved. Preserved for compatibility but not interpreted by KACS. |
| 2 | 2 | AclSize | Total size of the ACL in bytes, including the 8-byte header. Little-endian. |
| 4 | 2 | AceCount | Number of ACEs in the ACL. Little-endian. |
| 6 | 2 | Sbz2 | Reserved. Preserved for compatibility but not interpreted by KACS. |

The ACE array begins immediately at offset 8. Each ACE is self-delimiting via its `AceSize` field. The parser walks the ACL by iterating exactly `AceCount` ACEs within the `AclSize` boundary.

## Parsing rules

- `AclSize` MUST be at least 8 bytes.
- `AclSize` MUST NOT exceed the containing buffer.
- The ACL body MUST contain exactly `AceCount` ACEs within the declared `AclSize`.
- Truncated ACEs, ACE overruns, or leftover bytes within `AclSize` are malformed.
- The architectural maximum ACL size is 64 KB because `AclSize` is a 16-bit field.

ACE structure, ACE-type definitions, and revision-versus-ACE-family rules are specified in the ACE Types section.
