---
title: Extension
description: How the Trust Store Interface grows, through new ioctls and
  new notification types, and why its structures and the store image do
  not change in place.
---

## Additive changes

A new operation is a new ioctl. A store keeper that does not issue it
is unaffected, and a kernel that does not implement it fails `ENOTTY`,
which a store keeper MUST treat as "not supported" and not as a
failure of the connection.

## Changes requiring a version

The structures of §6.5 and §6.6 do not grow. A change to one is a new
ioctl with a new structure.

The notification `type` enumeration is closed. A store keeper MUST
ignore a record whose `type` it does not recognize, and a kernel adds a
type only together with an ioctl by which a store keeper asks for it.

The store image carries the format version of PGSS §7.4 in its header.
A kernel MUST treat an image whose version it does not implement as
malformed as a whole (§6.3).

## Reserved space

Every `_pad` field is reserved. A store keeper MUST write zero, and the
kernel fails `EINVAL` otherwise. The kernel writes zero in every `_pad`
field it returns.
