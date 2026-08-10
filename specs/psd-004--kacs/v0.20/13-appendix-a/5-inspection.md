---
title: Inspection Interfaces
---

## procfs

**`/proc/<pid>/token`** — opens a query-only inspection handle bound to the primary token of process `<pid>`. The returned handle supports `KACS_IOC_QUERY` only and carries a fixed cached access mask of `TOKEN_QUERY`; it is not a general-purpose token handle and MUST reject non-query token ioctls. User-facing tools MAY format the queried token state as text, but that formatting is userspace policy rather than kernel ABI. Access is gated by `PROCESS_QUERY_INFORMATION` on the target process's SD, plus PIP dominance check for protected processes. Reading `/proc/self/token` is always allowed.

**`/proc/<pid>/task/<tid>/token`** — opens a query-only inspection handle bound to the effective token of thread `<tid>`. If the thread is impersonating, the handle resolves to the impersonation token; otherwise it resolves to the process's primary token. It follows the same fixed-`TOKEN_QUERY`, query-only rules as `/proc/<pid>/token`. Access requirements are the same as `/proc/<pid>/token` (`PROCESS_QUERY_INFORMATION` + PIP dominance).

## securityfs

**`/sys/kernel/security/kacs/self`** — opens a query-only inspection handle bound to the calling thread's effective token. It follows the same fixed-`TOKEN_QUERY`, query-only rules as the procfs token inspection nodes. It is exposed as a world-readable securityfs node rather than as a KACS-SD-protected object, because it can return only the caller's own effective token through a fixed query-only handle. Opening the node MUST fail closed if the caller has no effective token.

**`/sys/kernel/security/kacs/sessions`** — lists active LogonSessions with LogonSession ID, user SID, logon type, auth package, and logon time. Protected by an SD granting BUILTIN\Administrators and SYSTEM FILE_READ_DATA. Access is enforced via normal AccessCheck against this SD — no special privilege check.

The sessions listing is a UTF-8 text ABI. Each active published LogonSession is
reported as one line:

```text
session_id=<decimal-u64> user_sid=<lowercase-hex-sid> logon_type=<decimal-u32> auth_package=<lowercase-hex-utf8> created_at=<decimal-u64>\n
```

The field order shown above is fixed. Future kernel versions MAY append
additional ` key=value` fields to the end of a line; consumers MUST ignore
unknown appended fields. `user_sid` is the exact binary SID encoded as
lowercase hexadecimal. `auth_package` is the exact UTF-8 authentication package
string encoded as lowercase hexadecimal, with no escaping layer. The order of
session lines is not significant.
