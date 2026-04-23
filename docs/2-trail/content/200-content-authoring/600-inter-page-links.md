---
title: Inter-Page Links
type: how-to
description: Use the ~slug shorthand to link between pages. Trail resolves these at build time to absolute URLs.
---

Trail provides a shorthand syntax for linking between pages in your documentation site. Instead of writing absolute paths that may break if the site structure changes, you reference pages by their slug.

## Syntax

Use the tilde prefix `~` in a Markdown link's URL:

```markdown
Read about [tokens](~identity/how-tokens-work) for more detail.
```

At build time, Trail replaces `~identity/how-tokens-work` with `/identity/how-tokens-work/`, producing a working absolute link in the output.

## How slugs work

A page's slug is its file path relative to the content root (or product content root in multi-product mode), with the `.md` extension removed.

| File path | Slug |
|---|---|
| `content/guides/install.md` | `guides/install` |
| `content/peios/identity/tokens.md` | `peios/identity/tokens` |

Use the full slug (including product prefix in multi-product mode) in the link:

```markdown
See [understanding identity](~peios/identity/understanding-identity).
```

## Validation

Trail validates internal links after building the site. If a `~slug` reference points to a page that does not exist, Trail does not fail the build. Instead, it:

1. Resolves the link to `/slug/` regardless of whether the page exists.
2. Prints a warning at the end of the build listing broken internal links.

This means broken links are visible in the build output but do not block deployment. Check the build output during development to catch and fix broken references.

## Examples

Link to a page in the same category:

```markdown
See [quick start](~getting-started/quick-start) to get up and running.
```

Link to a page in a different category:

```markdown
The [search feature](~features/search) is built in.
```

Link to a page in a specific product (multi-product mode):

```markdown
Read the [Trail configuration reference](~trail/configuration/trail-toml).
```

## When to use inter-page links

Use `~slug` links for all references between pages in the same Trail site. Do not use relative paths like `../other-page` or hard-coded absolute paths like `/guides/install/`, because:

- Relative paths break if a page moves to a different category.
- Hard-coded absolute paths work but provide no validation.
- `~slug` links are validated at build time and resolve correctly regardless of the linking page's location.

For external links, use standard Markdown link syntax with a full URL:

```markdown
See the [Mermaid documentation](https://mermaid.js.org/) for details.
```

## How it works

Trail's `resolvePageLinks` function runs after Markdown rendering. It uses a regular expression to find `href="~..."` attributes in the rendered HTML and replaces each one with `href="/slug/"`. The function checks the site's page map to verify the target exists, but resolves the link either way.
