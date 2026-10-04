---
title: Session locales
type: how-to
description: Select character handling and regional conventions for console, SSH and GXWI sessions.
---

Experimental includes `org.gnu.glibc-bin`: the `locale` and `localedef` tools
and compiled `C.UTF-8` data. New user sessions default to `LANG=C.UTF-8`.
This gives UTF-8 character handling with the C locale's conventions. A
locale controls character classification, sorting, and number, money and
date formatting; it does not select a console keyboard layout or font,
which [console keyboards and fonts](~peios/console-tools/keyboard-and-fonts)
cover.

Regional locales are precompiled in optional `org.gnu.glibc-langpack-*`
packages. For example, install `org.gnu.glibc-langpack-en` for British
English or `org.gnu.glibc-langpack-de` for German. Installing a pack does
not select it. `org.gnu.glibc-locale-source` contains source definitions
and is not required to use these packs; no `locale-gen` step is needed.

## Machine and principal preferences

The machine default is under `Machine\System\Locale`. An administrator
can change it after installing the corresponding pack, in System Settings
or with `reg`.

In **System Settings**, on the **Language & keyboard** tab, **Language**
lists every locale installed in full, by its language and place, and
**Formats** chooses how dates, numbers, money, measures and paper sizes are
written, if not as the language writes them. **Save** writes `LANG`, and
`LC_TIME`, `LC_NUMERIC`, `LC_MONETARY`, `LC_MEASUREMENT` and `LC_PAPER` for
the formats. Anyone may look; changing it needs write access to
`Machine\System\Locale`, which as shipped only Administrators have.

```sh
reg set -p Machine/System/Locale LANG sz:en_GB.UTF-8
```

A principal's own values, under `Users\<SID>\Locale`, override the
machine's. The principal may set them, and so may Administrators. Use
`lps show NAME` to find a local principal's SID, or `token user` within
that principal's session, then substitute the SID after the principal has
logged in at least once:

```sh
reg new Users/S-1-5-21-1-2-3-1000/Locale
reg set Users/S-1-5-21-1-2-3-1000/Locale LANG sz:en_GB.UTF-8
reg set -p Users/S-1-5-21-1-2-3-1000/Locale LC_NUMERIC sz:de_DE.UTF-8
```

Authd provisions a private `Users\<SID>` root on authenticated logon. The
principal, SYSTEM and Administrators have full access, inherited by child
keys. Creation and its descriptor are committed atomically. Existing roots
and their descriptors are left alone; failure to provision is reported but
does not deny login. A write needs access to the registry layer as well as
to the key, and the base layer lets Authenticated Users set values, so the
principal can write their own preferences there.

Values are `REG_SZ` locale names. Supported names are `LANG`, `LC_CTYPE`,
`LC_NUMERIC`, `LC_TIME`, `LC_COLLATE`, `LC_MONETARY`, `LC_MESSAGES`,
`LC_PAPER`, `LC_NAME`, `LC_ADDRESS`, `LC_TELEPHONE`, `LC_MEASUREMENT` and
`LC_IDENTIFICATION`. Each principal value overrides the same machine value.
A machine category override remains in force when a principal changes only
`LANG`; set that category explicitly to override it too. Categories without
an override use `LANG`.

`LC_ALL`, `LANGUAGE` and `LOCPATH` are not stored preferences. In particular,
persisting `LC_ALL` would hide every category choice. It remains useful for
a single command, for example `LC_ALL=C sort names`.

Malformed values, wrong types and locale data absent from the standard
system locale directory are reported and ignored, retaining the preceding
default for that value. Names cannot contain paths. Absent settings fall
back to `C.UTF-8`; `C` and `POSIX` are also valid choices. Minimal custom
images must include `glibc-bin` to make the UTF-8 fallback available.

## When a change takes effect

Console login, SSH session children and new GXWI compositor sessions read
these preferences. Programs launched from them inherit the resulting
environment. Existing sessions keep their environment, including a GXWI
session rejoined after a browser disconnect. Sign out and start a new
session to pick up a change. Applications may still choose their own locale.

Console `login -p` preserves other environment settings but refreshes locale
preferences and removes inherited `LC_ALL` and `LANGUAGE`. GXWI also clears
inherited locale overrides before applying preferences. For SSH, registry
preferences are defaults; explicitly permitted client environment entries,
user environment files or administrator `SetEnv` settings retain OpenSSH's
normal ability to override them for that session.

Service environments are not changed. These preferences are resolved by
user-session launchers, not applied as peinit global environment variables.

Inspect a new session with:

```sh
locale
locale charmap
locale -k decimal_point
```
