---
title: Prior Art
description: The LUID derives from MS-DTYP §2.3.7, diverging in one detail — HighPart is unsigned where MS-DTYP has it signed.
---

## MS-DTYP

The LUID type defined in this document derives from the Microsoft
Data Types specification (MS-DTYP), §2.3.7.

The Peios LUID binary format diverges from MS-DTYP in one detail:
HighPart is an unsigned 32-bit integer (uint32) rather than the
signed 32-bit integer (LONG) used in MS-DTYP. The signed type in
MS-DTYP is a Win32 API convention with no semantic purpose — LUID
values are never negative. Making the field unsigned simplifies
comparison and eliminates a class of sign-extension bugs.
