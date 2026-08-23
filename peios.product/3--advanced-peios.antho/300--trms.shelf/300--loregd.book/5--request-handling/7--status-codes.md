---
title: Status Codes
description: The seven RSI status codes loregd returns, and the three the interface defines that it never produces.
---

loregd returns seven of the RSI status codes:

| Status | Value | Returned when |
|---|---|---|
| `RSI_OK` | 0 | The operation succeeded. Also returned by the idempotent deletions when their target was already absent. |
| `RSI_NOT_FOUND` | 1 | A named key GUID exists in neither store, or resolves to no registered hive. Also an update matching no row. |
| `RSI_ALREADY_EXISTS` | 2 | A primary-key collision in the target table — a duplicate key GUID, path entry, or value entry within one schema. |
| `RSI_STORAGE_ERROR` | 3 | A SQLite failure while serving the request. Also an operation whose GUID belongs to a hive other than the one its transaction is bound to, a mutating operation carrying an unknown transaction id, a failed commit that was not busy, and any `RSI_DELETE_LAYER` failure. |
| `RSI_TXN_BUSY` | 6 | `BEGIN IMMEDIATE` found the database busy, a conditional write could not begin its transaction, or `RSI_FLUSH` found a transaction bound to the hive. |
| `RSI_INVALID` | 7 | An unknown opcode, a request whose payload cannot be decoded, an out-of-range `RSI_WRITE_KEY` field mask, a mutating operation carrying a read-only transaction id, an `RSI_FLUSH` naming an unregistered hive, or an `RSI_BEGIN_TRANSACTION` re-using an active id. |
| `RSI_CAS_FAILED` | 8 | A conditional `RSI_SET_VALUE` whose target was absent or whose sequence did not match. |

Three codes are defined by the interface and never produced by loregd:
`RSI_NOT_EMPTY` (4), `RSI_TOO_LARGE` (5), and `RSI_TXN_NOT_SUPPORTED` (9).

`RSI_TXN_NOT_SUPPORTED` is never needed because loregd supports both
transaction modes (§4.3).

`RSI_TOO_LARGE` is never returned because an oversized or malformed frame
is not answered at all. Framing is validated before an opcode is known, and
a frame that fails validation ends the connection instead of producing a
response (§2.3).
