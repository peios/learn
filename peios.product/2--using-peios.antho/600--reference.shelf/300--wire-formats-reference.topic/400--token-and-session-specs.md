---
title: Token and session specs
type: reference
description: Where the binary token and session specifications are laid out — the Peios Kernel TRM's KACS ABI appendix.
related:
  - peios/wire-formats-reference/overview
  - peios/tokens/token-types
  - peios/logon-sessions/logon-types
---

The binary specs that `kacs_create_token` and `kacs_create_session` accept, and the payload format of every token query class, are laid out in the **Peios Kernel TRM §3.A**, the KACS ABI reference. All 46 header offsets and all 24 query classes are there.

The conceptual field list — what a token holds and what each field does — is [Token types](~peios/tokens/token-types).

## Shape, in summary

Both specs are length-prefixed throughout: a field is a 32-bit byte count followed by that many bytes, and an absent field has a count of zero. Arrays are a 32-bit element count followed by that many records.

Size limits are 64 KB for a token spec and 4096 bytes for a session spec; both are in [Other constants](~peios/constants-and-catalogs/other-constants).

The enumerated values a spec carries — impersonation level, elevation type, logon type, mandatory policy, audit policy — are catalogued in [Other constants](~peios/constants-and-catalogs/other-constants) too, under the names the headers declare.

For building a session spec from the command line rather than by hand, `logonse` types the surface for you; the underlying format is unchanged.
