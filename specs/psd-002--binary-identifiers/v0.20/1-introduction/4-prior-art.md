---
title: Prior Art
---

## MS-DTYP

The GUID and LUID types defined in this specification derive from the
Microsoft Data Types specification (MS-DTYP), §2.3.4 (GUID)
and §2.3.7 (LUID).

The Peios GUID binary format is identical to the MS-DTYP GUID. The
Peios GUID string format follows the same hyphenated hex convention
but normalises to lowercase hex digits on output, where Microsoft
implementations typically produce uppercase.

The Peios LUID binary format diverges from MS-DTYP in one detail:
HighPart is an unsigned 32-bit integer (uint32) rather than the
signed 32-bit integer (LONG) used in MS-DTYP. The signed type in
MS-DTYP is a Win32 API convention with no semantic purpose -- LUID
values are never negative. Making the field unsigned simplifies
comparison and eliminates a class of sign-extension bugs.

## RFC 4122

RFC 4122 ("A Universally Unique IDentifier (UUID) URN Namespace")
defines the UUID format and generation algorithms. The GUID
binary layout used by Microsoft and adopted by Peios is the
mixed-endian variant of the RFC 4122 UUID: the first three fields
are little-endian integers and the last field is a raw byte array.
This differs from the RFC 4122 network byte order representation
where all fields are big-endian.

Peios generates version 4 (random) GUIDs as defined in RFC 4122 §4.4.

## DCE RPC

The GUID structure originates from the DCE 1.1 RPC specification,
which defined the `uuid_t` type with the same field layout. The
mixed-endian encoding reflects the DCE convention of encoding integer
fields in the sender's native byte order (little-endian on x86).
