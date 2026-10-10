---
title: rsync and OpenSSL
type: guide
description: Choose a content-copy or TLS diagnostic command, understand destination security and interruption risks, and verify the result without relying on Unix permissions.
related:
  - peios/networking/diagnostic-tools
  - peios/networking/network-policy
  - peios/trust/the-compat-files
---

Use `rsync -rlt` for content synchronization and an explicit verification
mode for TLS diagnostics. Before either, choose a destination you control
and confirm the identity and access the command will use.

| Task | Start here | Check afterwards |
|---|---|---|
| Copy directory contents locally or over SSH | [Synchronizing contents](#synchronizing-contents-with-rsync) | Check the destination contents and native access policy. rsync is not a security-descriptor backup. |
| Create private key or other secret output | [Private outputs](#openssl-and-private-outputs) | Use the tool's named-output option and a private directory; shell redirection has different protection. |
| Diagnose a TLS server | [TLS diagnostics](#tls-diagnostics-and-network-policy) | Require successful certificate verification for the intended DNS name or IP identity. |

## Synchronizing contents with rsync

The Peios rsync port synchronizes contents between local directories or over SSH. Replace the example paths, account and server; an existing destination file may be replaced:

```sh
rsync -rlt source/ destination/
rsync -rlt source/ alice@server:destination/
```

`-rlt` copies directories recursively, carries symbolic links and preserves modification times. Add `-X` to copy ordinary `user.*` extended attributes. Security descriptors, signatures, capabilities and other security attributes are excluded from ordinary xattr synchronization, including when explicit xattr filters are supplied.

A new regular file receives the destination directory's native inheritance. An updated regular file retains the destination's complete security descriptor. Source Unix modes, UID and GID do not define the destination's Peios access policy. Archive/security-preservation requests such as `-a`, `-p`, `-o`, `-g`, ACL preservation, `--chmod` and `--fake-super` are rejected. This differs from native `cp -a`, which explicitly requests a security-preserving copy. rsync is not yet a native security backup/restore tool.

Ordinary replacement stages a private inode in the destination filesystem. Publishing a replacement requires permission to read and restore the destination's full security, including audit metadata. If those rights are unavailable, the transfer fails without publishing a replacement. rsync does not silently drop inaccessible descriptor components or change to in-place writing. It checks for destination inode and descriptor changes before publication, but that check and the final rename are not a single security transaction. Coordinate concurrent permission changes separately.

For an existing file you are authorized to write, you can explicitly choose:

```sh
rsync -rlt --inplace source/ destination/
```

An in-place update retains the original inode and its security descriptor, and also affects its other hardlinks. It is not atomic: interruption can leave partially updated contents. Use it only when that tradeoff is appropriate.

This initial port rejects alternate staging/partial/backup modes, delayed updates, hardlink preservation, basis-directory optimization, special-file preservation, batch mode and insecure symlink traversal. It also refuses replacements that would delete an existing object to change its type or symbolic-link target, since that would discard its destination security. Explicit deletion remains a separate operation. Filesystems must support unnamed temporary files for ordinary staged transfers; there is no insecure staging fallback.

Rsync daemon serving is disabled, including daemon mode invoked over a remote shell. Ordinary SSH `--server` transfers remain supported. The receiving process uses the identity supplied by SSH; installing rsync creates no service and grants no extra authority. Security-sensitive symlink ownership checks use native SIDs rather than cosmetic Unix UID zero. A client password file must have a protected owner-only native DACL.

After a transfer, check that the intended contents arrived and that the
destination's native security is still the policy you intended. If staged
replacement is refused for insufficient security rights, read that failure
before considering `--inplace`; it is a different interruption and hardlink
tradeoff, not an equivalent retry.

## OpenSSL and private outputs

OpenSSL uses trustd's generated `/etc/ssl/cert.pem` and hashed `/etc/ssl/certs` by default. Use `trust` to manage machine trust. Explicit CA-file, CA-directory and environment overrides select trust for that invocation; they do not modify the machine's trust store. `openssl rehash` is for directories you manage yourself, not trustd's generated directory.

Named secret outputs are private to the effective Peios principal from creation. This includes private keys, secret-bearing PKCS12 exports, session files, TLS key logs, derived/random key material, RNG seed files and decrypted plaintext. Public certificate and public-key outputs use ordinary destination policy, except mixed exports, which are treated as potentially secret.

An existing secret destination must be a regular file owned by the effective principal, with a protected owner-only DACL. Shared files, symbolic links, multiply linked files and policies the tool cannot prove private are refused before data is overwritten. This intentionally does not reinterpret Unix `0600` as a native access policy. Configure intentional service-key sharing separately through Peios security tools after generation. Ordinary administrative privileges and mandatory controls still apply.

Output to stdout or a pipe remains supported. Shell redirection creates its own file: `openssl ... > key.pem` does not receive the tool's named-output protection. For private named files use the command's `-out`, `-keyout`, `-secret`, `-sess_out`, `-keylogfile` or other named-output option as appropriate. A shared directory may still permit someone to remove or replace directory entries; use a directory you control for durable keys.

## TLS diagnostics and network policy

`openssl s_client` retains its diagnostic behavior: certificate errors are reported but do not necessarily abort the connection. For a strict server check, request both fatal verification errors and the expected identity:

```sh
openssl s_client -connect example.org:443 -servername example.org \
  -verify_return_error -verify_hostname example.org
```

Use `-verify_ip` for an IP identity. SNI (`-servername`) alone is not hostname verification. Explicitly selected TLS diagnostic behavior never bypasses PNP: connections and listeners remain subject to native network policy and port reservations.

A successful TLS check establishes the requested certificate checks for
that peer. It does not change system trust or grant access through PNP.
If verification fails, inspect the reported certificate, peer name and
trust anchors rather than disabling the check to declare success.
