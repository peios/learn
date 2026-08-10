---
title: Storage and Protection
---

## Engine

lpsd MUST store its data in a transactional, crash-safe, single-file
database. lpsd is specified against **SQLite in WAL mode**: WAL provides
the atomic, durable writes the logon path needs (lockout counters and
last-logon are written during authentication — §5.1), and SQLite's
online backup, `PRAGMA integrity_check`, and dump facilities back the
recovery tooling of §7.3.

The engine is private to lpsd and does not cross the seam (§2.2); the
choice does not affect interoperability with other sources.

> [!INFORMATIVE]
> Illustrative schema (normative content, illustrative DDL):
>
> ```sql
> CREATE TABLE domain (
>     id              INTEGER PRIMARY KEY CHECK (id = 0),
>     machine_sid     BLOB NOT NULL,
>     rid_counter     INTEGER NOT NULL,
>     policy          BLOB NOT NULL,        -- password/lockout policy
>     sd              BLOB NOT NULL,        -- container SD: create/enumerate + inheritable ACEs (§7.2)
>     created_at      INTEGER NOT NULL
> );
> CREATE TABLE users (
>     rid             INTEGER PRIMARY KEY,
>     object_guid     BLOB NOT NULL UNIQUE,
>     name            TEXT NOT NULL,
>     name_folded     TEXT NOT NULL UNIQUE,
>     display_name    TEXT,
>     upn             TEXT,
>     account_flags   INTEGER NOT NULL,
>     primary_group_sid BLOB NOT NULL,
>     pw_last_set     INTEGER,
>     last_logon      INTEGER,
>     account_expires INTEGER,              -- NULL = never
>     bad_pw_count    INTEGER NOT NULL DEFAULT 0,
>     last_bad_pw_time INTEGER,
>     lockout_until   INTEGER,              -- NULL = not locked
>     posix_uid       INTEGER NOT NULL,
>     posix_gid       INTEGER NOT NULL,
>     sd              BLOB NOT NULL,        -- per-principal SD (§7.2)
>     created_at      INTEGER NOT NULL,
>     modified_at     INTEGER NOT NULL,
>     version         INTEGER NOT NULL
> );
> CREATE TABLE credentials (
>     rid             INTEGER NOT NULL REFERENCES users(rid),
>     type            INTEGER NOT NULL,
>     version         INTEGER NOT NULL,
>     params          BLOB,
>     public_part     BLOB,
>     secret_part     BLOB,                 -- wrappable (see below)
>     PRIMARY KEY (rid, type)
> );
> CREATE TABLE pw_history ( rid INTEGER, seq INTEGER, verifier BLOB, PRIMARY KEY (rid, seq) );
> CREATE TABLE groups (
>     rid             INTEGER PRIMARY KEY,  -- or well-known SID for BUILTIN
>     sid             BLOB NOT NULL UNIQUE,
>     object_guid     BLOB NOT NULL UNIQUE,
>     name            TEXT NOT NULL,
>     name_folded     TEXT NOT NULL UNIQUE,
>     group_type      INTEGER NOT NULL,
>     posix_gid       INTEGER NOT NULL,
>     sd              BLOB NOT NULL,        -- per-principal SD (§7.2)
>     created_at INTEGER, modified_at INTEGER, version INTEGER
> );
> CREATE TABLE members ( group_sid BLOB NOT NULL, member_sid BLOB NOT NULL, PRIMARY KEY (group_sid, member_sid) );
> CREATE TABLE claims ( rid INTEGER, name TEXT, value BLOB, PRIMARY KEY (rid, name) );
> CREATE TABLE schema_version ( version INTEGER NOT NULL );
> ```
>
> Name folding follows the same approach as PSD-006: a folded column is
> stored and compared, avoiding a custom collation.

## At-rest protection

A `secret_part` MUST be stored as a **wrappable blob** carrying a
protection descriptor:

```
{ scheme, key_id, ciphertext_or_plaintext }
```

This version defines two schemes and a staged adoption:

- **`scheme = none` (this version).** The verifier is stored in the
  clear. At-rest protection is provided by **full-disk encryption** of
  the volume holding the database. lpsd MUST NOT implement a
  SYSKEY-style local-key obfuscation: a key stored beside its
  ciphertext adds no real protection and is forbidden as security
  theatre.
- **`scheme = tpm-sealed` (deferred — §8).** The verifier is encrypted
  under a key sealed to the platform's measured boot, optionally with a
  server-side pepper mixed into argon2id. Adopting it is a re-wrap pass
  over existing rows, requiring no schema change.

The wrappable-blob shape is mandated now so the later transition is a
data migration, not a format change.

> [!INFORMATIVE]
> **Residual risk of the `none` baseline.** Until `tpm-sealed` is adopted
> (§8), verifiers sit in cleartext behind FDE alone. An attacker with the
> powered-off disk, an unencrypted backup, or `SeBackup`/`SeDebug`-class
> access (which reads past the file SD, or reads lpsd's memory) obtains
> every verifier for offline cracking — so disk/backup/admin compromise is
> equivalent to full credential loss. Deployments that must resist this
> MUST enable FDE, MUST protect backups to the same standard as the live
> database, and SHOULD prioritise bringing `tpm-sealed` forward (§8).

## The database file and volume

The database MUST reside on a writable, security-descriptor-bearing
volume — not on a read-only or SD-less root filesystem (per the KACS
mount-policy requirements of PSD-004). lpsd MUST create the database
file with a tight SD granting full access to SYSTEM, the
`Administrators` group, and lpsd's own identity, and denying all
others, since the file holds the system's verifiers.

## Secret memory hygiene

lpsd MUST `mlock` buffers holding transient credentials and stored
verifiers, MUST zeroize them after use via a pinned/zeroizing buffer (not
a plain heap allocation that may be reallocated or moved), and MUST
disable core dumps (`PR_SET_DUMPABLE = 0`) and restrict ptrace-attach to
the TCB. authd MUST do the same for its transient-credential buffers
(§6.2.5). This complements, and does not replace, the at-rest protection
above.
