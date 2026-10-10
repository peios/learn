# Optional Cloudflare Pages previews

The live documentation remains on GitHub Pages at https://learn.peios.org.
This script does not configure or deploy a Cloudflare project. Account setup,
GitHub installation permissions, and publishing previews need maintainer approval.
Previews are public by default, including their generated Markdown and source
excerpts. Do not add private content, credentials, or runtime data to preview builds.

## One-time setup after approval

1. Create a **Pages** project with Git integration for `peios/learn`. Scope the
   GitHub installation to this repository. Do not create a Workers application.
2. Set the production branch to `main`, framework preset to **None**, root directory
   to the repository root, build command to
   `bash .github/scripts/build_cloudflare_preview.sh`, and output directory to `dist`.
   The script deliberately rejects `CF_PAGES_BRANCH=main`; an initial main build
   may fail because main does not yet contain the script (or because of that guard).
   This is expected for a preview-only project and does not require merging the PR.
   Continue to the project settings after that failure. Do not switch the
   production branch to the PR branch to get around this guard.
3. Under **Settings > Builds > Branch control**, disable **Enable automatic
   production branch deployments**. Initially use custom preview branches with
   `docs/operator-documentation-overhaul` included. Broaden to other same-repository
   review branches only when desired. This recipe does not configure fork previews.
4. Leave custom domains, DNS, the repository `CNAME`, and the GitHub Pages deployment
   workflow unchanged. Add no Functions, bindings, API tokens, or build secrets.
   Cloudflare supplies `CF_PAGES_URL` and `CF_PAGES_BRANCH`; do not override them.
5. Build the selected branch after it contains the script. Verify the deployment
   commit matches the PR head, open its preview URL, and check the home page, a deep
   article link, search, and a print page. Confirm main auto-deploy is off and no
   production domain is attached. A successful local build is not hosted verification.

The script downloads and checks its pinned Trail artifact (or checks a supplied
`TRAIL_BIN`). A changed upstream artifact fails closed; review any pin update.
Linux x86-64, Bash, Python 3, `curl`, and `sha256sum` are required.

Trail's root `url` controls canonical metadata, sitemaps, and outward print links;
it has no base-URL environment override. The build substitutes the validated
`CF_PAGES_URL` in a temporary config, retaining root-relative navigation, search,
and asset paths. It removes `CNAME` only from generated output. Tracked site files
are unchanged. No commit-path duplicate is needed because Pages gives each preview
its own deployment URL. Existing authored absolute links are not rewritten.

Local static check with the already-verified binary and output outside the checkout
(Trail replaces the output directory; use a disposable destination):

```sh
CF_PAGES_URL=https://local-check.example.pages.dev \
TRAIL_BIN=/path/to/verified/trail \
bash .github/scripts/build_cloudflare_preview.sh /tmp/peios-preview-site
```

The optional rendered-link checker and its unit tests can be run separately as
described in `.github/README.md`; there is no automatic pull-request validation
workflow. A Cloudflare branch build does not compare links against a base build.
Preview URLs are not access controls; Cloudflare's preview `noindex` behavior
does not make a public deployment private.

References: [Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/),
[branch controls](https://developers.cloudflare.com/pages/configuration/branch-build-controls/),
[build environment](https://developers.cloudflare.com/pages/configuration/build-configuration/),
[preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/).
