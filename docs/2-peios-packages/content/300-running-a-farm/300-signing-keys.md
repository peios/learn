---
title: Signing Keys
type: how-to
description: How to generate, store, publish, and rotate the Ed25519 signing key that authenticates everything the build farm produces.
related:
  - peios-packages/running-a-farm/installation
  - peios-packages/running-a-farm/configuration
---

The build farm's signing key is the single point of trust for everything it publishes. Compromise of the key means an attacker can forge any package. This page covers what to do with the key beyond `chmod 600`, and how to rotate it when needed.

## What gets signed

Every artefact `peipkg-manager` publishes carries a signature made by this one key:

- Each `.peipkg` file (inline signature inside the tar archive — [PSD-009 §5.1](../../../specs/psd-009--peipkg/v0.22/5-signing/1-package-signature)).
- The repository descriptor at `<repo-base>/repo.json` (detached `.sig` file).
- The active and archive indexes (detached `.sig` files).

A consumer trusts the repository because they've added the key's *fingerprint* to their trust set out-of-band. Compromise of the key, or any practice that would let an attacker hold it, breaks that whole chain.

## Generating the key

Ed25519, raw 32-byte seed or PEM PKCS#8. Either works with `peipkg-manager` and `peipkg-build`.

```bash
sudo openssl genpkey -algorithm ed25519 -out /etc/peipkg-manager/farm.ed25519
sudo chmod 600 /etc/peipkg-manager/farm.ed25519
sudo chown root:root /etc/peipkg-manager/farm.ed25519
```

Verify it parses:

```bash
sudo openssl pkey -in /etc/peipkg-manager/farm.ed25519 -text -noout
```

You should see `ED25519 Private-Key:` and 32 hex bytes.

## Computing the fingerprint

The key's fingerprint is the lowercase hex SHA-256 of the raw 32-byte public key. Compute it from the private key file:

```bash
sudo openssl pkey -in /etc/peipkg-manager/farm.ed25519 -pubout 2>/dev/null \
  | openssl pkey -pubin -outform DER 2>/dev/null \
  | tail -c 32 \
  | sha256sum \
  | awk '{print $1}'
```

Or — easier — just let `peipkg-manager` do it on first start. Once the daemon has run once, `repo.json` contains the key's fingerprint at `repo.signing.keys[].fingerprint`:

```bash
jq -r '.repo.signing.keys[].fingerprint' \
  /var/lib/peipkg-manager/repo/repo.json
```

This is the value users add to their trust set. Display it grouped (4-char chunks separated by spaces or colons) so people comparing it visually can spot mismatches:

```
1a2b 3c4d 5e6f 7890 ...
```

The on-wire form is the unbroken 64-character hex string; grouping is for human display only.

## Publishing the public key

Consumers fetch the public key file at the conventional URL `<repo-base>/keys/<fingerprint>.pub`, written there automatically by `peipkg-repo init`. The public key is in PEM SubjectPublicKeyInfo form, the same format other tools (`ssh-keygen -A`, `openssl pkey -pubin`) recognise.

Publishing the *fingerprint* (so a user can verify they've fetched the right key) is the operator's job. For the official Peios repo, fingerprints go on the project website, in the OS image, and in trail-of-trust documentation. For a custom repo, anywhere your users will look.

> [!IMPORTANT]
> Fingerprint distribution is the trust anchor. A user adding your repo will type or paste the fingerprint they got from your website to verify the key the package manager fetched. If an attacker can substitute the fingerprint *at the source* — by compromising your DNS, your TLS cert, your website CMS — they own the trust chain. Pick distribution channels you can defend, and consider distributing through more than one (website, README in the OS image, a side-channel like an email signature).

## What NOT to do

- **Don't store the key in environment variables.** They leak through process listings, core dumps, and child-process inheritance.
- **Don't commit the key to a git repo.** Even private repos eventually leak (forks, mirrors, CI logs).
- **Don't put the key in a container image.** Images get pulled, cached, and inspected; the key inside is one `docker pull` away from anyone who can reach your registry.
- **Don't keep the key on a CI runner.** Build artefacts and CI logs are routinely retained, often by third parties. If your build farm runs on GitHub Actions, the signing key being there means GitHub's infrastructure is your trust boundary.

The recommended deployment is a long-lived host the operator owns, with the key on disk under `0600` permissions.

## Backups

Back the key up *offline*. The simplest practice: copy the key to a removable medium (encrypted USB stick, paper printout via `paperkey` or QR code), store it physically separately. If the build host is wiped or destroyed, you can restore the key without your users having to add a new trust anchor.

A standard backup test: occasionally stand up a fresh build host from the backup and verify it signs identically to the production host. Same key, same recipe, same source ref → same `.peipkg` bytes. If they differ, your "backup" doesn't restore what you think it does.

## Rotation

The spec defines three key statuses ([PSD-009 §6.1.4](../../../specs/psd-009--peipkg/v0.22/6-repository/1-descriptor)): `active`, `transitioning`, `revoked`. Rotation moves a key through these states.

### Routine rotation (no compromise)

The transitioning model lets you rotate without breaking consumers. Steps:

1. Generate a new key:
   ```bash
   sudo openssl genpkey -algorithm ed25519 -out /etc/peipkg-manager/farm-new.ed25519
   sudo chmod 600 /etc/peipkg-manager/farm-new.ed25519
   ```
2. Edit `repo.json`: add the new key as `active`, change the old key's status from `active` to `transitioning`, set the old key's `valid_until` to (say) 30 days from now.
3. Re-sign `repo.json` with the *old* key (transitioning keys are still valid for verification). `peipkg-repo` does this if you point its `--sign-key` flag at the old key while editing the descriptor; v0 doesn't have a dedicated rotate subcommand yet, so this is a manual edit followed by a re-sign.
4. Update `peipkg-manager`'s `[signing].key_file` to the new key.
5. Restart `peipkg-manager`. New publishes are signed with the new key.
6. After 30 days (or whenever you're confident consumers have refreshed), edit `repo.json` again to remove the old key entirely. Re-sign with the new key.

The transition window must be longer than your consumers' typical refresh interval. The default consumer trust-state max-age is 30 days ([PSD-009 §6.5.4](../../../specs/psd-009--peipkg/v0.22/6-repository/5-trust-model)), so 30 days is a sensible floor.

> [!NOTE]
> v0 of `peipkg-repo` doesn't ship a `rotate-key` subcommand — the workflow is manual JSON edits + a re-sign with the existing key. Rotation is rare enough that automating it carefully (with a transition-period scheduler, sanity checks against descriptor consistency, etc.) is real work that v1 doesn't yet need. When the workflow becomes a regular operation, the subcommand can be added.

### Compromise rotation

If the key is *known* compromised:

1. Generate a new key immediately.
2. Edit `repo.json`: add the new key as `active`, change the compromised key's status to `revoked`. **Do not** keep the compromised key in transitioning state.
3. Re-sign `repo.json` with the new key.
4. Publish the new descriptor. Consumers refreshing get the revoked status and reject any signature from the compromised key going forward.
5. Notify users out-of-band — the in-band revocation works for consumers who refresh, but consumers caching the old descriptor still trust the compromised key until they re-sync.

The spec recommends keeping an *offline* signing key for descriptor updates so you can publish revocation even if the compromised key is the same one that signs descriptors ([PSD-009 §5.2.6](../../../specs/psd-009--peipkg/v0.22/5-signing/2-key-management)). For v0 with one signing key, you can't sign a revocation without using the compromised key — practically, this means a compromise event means consumers need to add a new trust anchor out-of-band. Plan accordingly.
