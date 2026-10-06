---
title: "reject.*"
description: "Every field the evman catalogue defines under reject: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `reject`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="reject.delivered-to"></a>`reject.delivered-to`

- **Type:** `str.enum`
- **Values:** `wire` · `self`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Where NTFE sent a refusal. `wire` answers the remote peer on the link, from
the ingress seat. `self` routes the answer back into this machine, from
every other seat, so the stack fails the local socket at once rather than
leaving it to time out.

**Carried by:**

No event carries this field yet.

## <a id="reject.packet"></a>`reject.packet`

- **Type:** `str.enum`
- **Values:** `tcp-reset` · `icmp-port-unreachable` · `icmp-admin-prohibited`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The packet NTFE built to deliver a refusal: a TCP reset for refused TCP,
an ICMP or ICMPv6 port-unreachable for refused anything else, or an ICMP or
ICMPv6 administratively-prohibited for every prohibited refusal. It decides
what the refused program sees: `ECONNREFUSED` for a reset or a
port-unreachable, `EHOSTUNREACH` for an IPv4 prohibition, and `EACCES` for
an IPv6 one. Absent when the REJECT degraded to a DROP.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
