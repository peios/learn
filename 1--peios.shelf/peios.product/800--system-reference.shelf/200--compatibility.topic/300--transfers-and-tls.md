---
title: Copying Contents and Checking TLS
type: how-to
description: Use Peios rsync and OpenSSL without mistaking content transfer for security backup or SNI for peer verification.
---

Choose the intended identity and destination policy before running a transfer
or generating secret output. These instructions apply to the Peios ports;
ordinary upstream builds do not establish the native-file guarantees below.

## Synchronize contents

1. Identify the source and destination. Use a destination directory you
   control and preserve any contents that replacement could discard.
2. For recursive contents, symbolic links, and modification times, adapt:

   ```sh
   rsync -rlt source/ destination/
   rsync -rlt source/ alice@server:destination/
   ```

3. Verify the resulting contents and native descriptor. `-X` additionally
   copies ordinary `user.*` attributes, not descriptors, signatures, or
   other security attributes, even with explicit attribute filters.

New files use destination inheritance; updates retain the destination's
complete descriptor. Unix owner, group, and mode are not native authority.
Archive/security-preservation requests such as `-a`, `-p`, `-o`, `-g`,
`--chmod`, ACL preservation, and `--fake-super` are refused. This is not a
native security backup or restore mechanism.

Ordinary replacement uses an unnamed temporary inode in the destination
filesystem. Publishing requires permission to read and restore the entire
destination descriptor, including audit metadata. Unsupported staging or
insufficient rights fail without silently falling back to in-place writes.
The destination inode/descriptor check and final rename are not one atomic
security transaction; coordinate concurrent permission changes separately.

If the interruption and hardlink tradeoff is appropriate, explicitly choose
`rsync -rlt --inplace source/ destination/`. This retains the inode and its
descriptor but changes its other hardlinks too. Interruption can leave partial
contents. It is not an equivalent retry after a staged update was refused.

Alternate staging, partial/backup modes, delayed updates, hardlink
preservation, basis-directory optimization, special-file preservation,
batch mode, and unsafe symlink traversal are excluded. Replacement that
would delete an object to change its type or link target is refused; deletion
is a separate decision. Daemon serving is disabled, including over a remote
shell, while normal SSH server-side transfers remain available. SSH supplies
the recipient identity. Client password files need protected owner-only
native policy.

## Create private cryptographic output

OpenSSL uses trustd's generated trust paths by default. Per-command CA files,
directories, or environment overrides select different trust without
modifying the machine store. Use `trust` for machine trust; do not rehash its
generated directory independently.

1. Choose a directory you control and the intended effective principal.
2. Use the command's named output option for secret material: for example,
   the applicable `-out`, `-keyout`, `-secret`, `-sess_out`, or `-keylogfile`.
3. Confirm success and inspect the resulting native policy before arranging
   any intentional service sharing.

Private keys, secret-bearing PKCS12 exports, session/key-log files, derived
or random key material, RNG state, and decrypted plaintext use protected
owner-only creation. Mixed exports are treated as potentially secret; public
certificate/key output uses ordinary destination policy. Existing secret
outputs must be regular, singly linked, owned by the effective principal,
and provably protected for that owner. Refusal does not fall back to `0600`.

Shell redirection creates its own destination. `openssl ... > key.pem` does
not obtain the tool's named-output guarantee. Administrative privileges and
mandatory controls still apply to native private files.

## Verify a TLS peer

`openssl s_client` reports certificate errors without necessarily stopping.
For a strict check, require verification success and the intended identity:

```sh
openssl s_client -connect example.org:443 -servername example.org \
  -verify_return_error -verify_hostname example.org
```

Replace the host with the service being tested. For an IP identity, use
`-verify_ip`. SNI alone is not hostname verification. Inspect a failed chain,
name, or trust check rather than disabling verification to obtain success.
A successful certificate check does not grant network access or change
machine trust; listeners and connections remain subject to native policy.
