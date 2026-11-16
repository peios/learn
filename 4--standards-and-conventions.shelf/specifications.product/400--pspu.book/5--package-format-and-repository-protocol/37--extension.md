---
title: Extension
description: What this version leaves room for, and why every format in it refuses what it doesn't understand.
---

Every format of this chapter has one form (§5.9), and a consumer refuses a
file that isn't in it. A later version that adds a field, a line kind or an
entry kind is therefore a new format: a consumer of this version refuses
what it adds rather than ignoring it, since ignoring part of a hashed file
would let two consumers take one identity for different things.

This version reserves:

- **Network transports other than HTTP** (§5.34).
- **Certificate chains** for signing a pointer file (§5.33).
- **`noarch` in other architectures' resolutions** (§5.8).
- **Index requests by a package:** only a request of the closure itself
  names an index in this version (§5.25).
