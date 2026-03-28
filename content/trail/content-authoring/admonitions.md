---
title: Admonitions
type: how-to
order: 30
description: Use GitHub-style blockquote syntax to create NOTE, WARNING, IMPORTANT, TIP, and CAUTION callouts in your documentation.
---

Admonitions are highlighted callout blocks that draw attention to important information. Trail supports five types using GitHub's blockquote alert syntax.

## Syntax

An admonition is a standard Markdown blockquote with a type marker on the first line:

```markdown
> [!NOTE]
> This is additional context the reader might find useful.
```

The type marker must be on the first line of the blockquote, in the format `[!TYPE]`. The rest of the blockquote becomes the admonition body.

## Available types

Trail supports five admonition types. Each has a distinct color and icon.

### NOTE

Use for supplementary information that adds context.

```markdown
> [!NOTE]
> Trail generates heading IDs automatically from the heading text.
> You do not need to add them manually.
```

Renders with a blue left border and an information icon.

### TIP

Use for helpful suggestions or best practices.

```markdown
> [!TIP]
> Run `trail serve` during development. It watches for changes
> and reloads the browser automatically.
```

Renders with a green left border and a lightbulb icon.

### IMPORTANT

Use for information the reader must know to proceed correctly.

```markdown
> [!IMPORTANT]
> Page slugs in pathway files must match the file paths exactly.
> A typo will not cause a build error but will break navigation.
```

Renders with a purple left border and an exclamation mark icon.

### WARNING

Use for potential pitfalls or situations that could cause problems.

```markdown
> [!WARNING]
> Trail deletes the output directory on every build. Do not store
> hand-written files in `_site/`.
```

Renders with a yellow left border and a warning icon.

### CAUTION

Use for actions that could cause data loss or are difficult to reverse.

```markdown
> [!CAUTION]
> Changing the `base_url` after deployment will break all existing
> external links and search engine references to your site.
```

Renders with a red left border and a warning icon.

## Styling details

Each admonition type has a specific color scheme for both light and dark modes:

| Type | Border color | Background color | Title |
|---|---|---|---|
| NOTE | Blue | Light blue / dark blue | "Note" |
| TIP | Green | Light green / dark green | "Tip" |
| IMPORTANT | Purple | Light purple / dark purple | "Important" |
| WARNING | Yellow | Light yellow / dark yellow | "Warning" |
| CAUTION | Red | Light red / dark red | "Caution" |

## How it works

Trail transforms admonitions during the post-processing phase after Markdown rendering. Goldmark renders the blockquote syntax into standard HTML `<blockquote>` elements. Trail's `transformAdmonitions` function then pattern-matches the `[!TYPE]` marker and replaces the blockquote with styled `<div>` elements.

This means admonitions work without any special Markdown extensions. Any Markdown editor or GitHub preview will render them as blockquotes with visible type markers, which is a reasonable fallback.
