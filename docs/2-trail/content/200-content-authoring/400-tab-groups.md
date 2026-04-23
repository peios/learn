---
title: Tab Groups
type: how-to
description: Group related content into tabbed panels using HTML comment markers to present alternatives side by side.
---

Tab groups let you present alternative versions of content (different languages, platforms, or approaches) in a compact tabbed interface. Readers click a tab to see the relevant content without scrolling past irrelevant alternatives.

## Syntax

Tab groups use HTML comments as markers. The outer delimiters are `<!-- tabs -->` and `<!-- /tabs -->`. Each tab within the group starts with `<!-- tab:Tab Name -->`.

```markdown
<!-- tabs -->
<!-- tab:npm -->

Install with npm:

\`\`\`
npm install my-package
\`\`\`

<!-- tab:yarn -->

Install with yarn:

\`\`\`
yarn add my-package
\`\`\`

<!-- tab:pnpm -->

Install with pnpm:

\`\`\`
pnpm add my-package
\`\`\`

<!-- /tabs -->
```

## How tab groups render

The first tab is visible by default. Clicking a tab button shows its panel and hides the others. Tab state is not persisted across pages or page loads.

The rendered output:

- A row of tab buttons at the top with the name from each `<!-- tab:Name -->` marker.
- One content panel per tab. Only the active panel is visible.
- The active tab button has a blue bottom border. Inactive buttons are gray.

## Complete example

Here is a tab group showing configuration in different formats:

```markdown
<!-- tabs -->
<!-- tab:TOML -->

\`\`\`toml
title = "My Docs"
description = "Documentation for my project."
base_url = "https://docs.example.com"
\`\`\`

<!-- tab:YAML (comparison) -->

\`\`\`yaml
title: My Docs
description: Documentation for my project.
base_url: https://docs.example.com
\`\`\`

<!-- /tabs -->
```

## Code in tabs

Tab groups work well with code blocks. When a code block is the only content in a tab panel, it renders flush against the tab container with no extra padding or rounded corners, creating a clean integrated appearance.

## Rules and limitations

- Tab names come from the `<!-- tab:Name -->` marker. The name is everything after `tab:` and before `-->`, with whitespace trimmed.
- You can have any number of tabs in a group.
- Content between `<!-- tabs -->` and the first `<!-- tab:Name -->` is ignored.
- Tab groups cannot be nested.
- Each tab group on a page gets a unique ID. Multiple tab groups on the same page are independent.
- Tab selection does not sync across groups. Clicking "npm" in one tab group does not affect other tab groups on the page.

## How it works

Trail transforms tab groups during the post-processing phase. The `<!-- tabs -->` and `<!-- /tabs -->` comments survive Markdown rendering because Goldmark is configured with `html.WithUnsafe()`. Trail's `transformTabGroups` function finds these markers, extracts the tab names and content, and replaces the block with styled HTML containing tab buttons and panels. Client-side JavaScript handles tab switching.
