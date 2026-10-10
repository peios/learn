---
title: "linux.*"
description: "Every field the evman catalogue defines under linux: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `linux`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="linux.cap"></a>`linux.cap`

- **Type:** `str.enum`
- **Values:** `chown` · `dac-override` · `dac-read-search` · `fowner` · `fsetid` · `kill` · `setgid` · `setuid` · `setpcap` · `linux-immutable` · `net-bind-service` · `net-broadcast` · `net-admin` · `net-raw` · `ipc-lock` · `ipc-owner` · `sys-module` · `sys-rawio` · `sys-chroot` · `sys-ptrace` · `sys-pacct` · `sys-admin` · `sys-boot` · `sys-nice` · `sys-resource` · `sys-time` · `sys-tty-config` · `mknod` · `lease` · `audit-write` · `audit-control` · `setfcap` · `mac-override` · `mac-admin` · `syslog` · `wake-alarm` · `block-suspend` · `audit-read` · `perfmon` · `bpf` · `checkpoint-restore`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The Linux capability whose check prompted the record, named as its
`CAP_*` constant with the prefix removed, in kebab case: `CAP_NET_ADMIN`
is `net-admin`. Context, never the decision. On Peios every capability
check is answered by KACS, either by mapping the capability to a
privilege — `net-admin` to SeTcbPrivilege, for example — or with a fixed
answer, so this says which Linux gate asked and `privilege.name` and the
outcome say what was decided.

Two sets have fixed answers and never involve a privilege. Twelve are
granted to every process unconditionally, because KACS makes the real
decision elsewhere: `chown`, `dac-override`, `dac-read-search`, `fowner`,
`fsetid`, `kill`, `setgid`, `setuid`, `net-bind-service`,
`net-broadcast`, `ipc-owner` and `lease`. `setpcap`, `setfcap` and
`mac-override` are refused whatever the token holds.

The set is open because new Linux releases add capabilities.

**Carried by:**

- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
