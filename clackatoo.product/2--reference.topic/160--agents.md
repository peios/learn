---
title: Agents
type: reference
description: A pane can hold a chat with an agent such as Claude Code instead of a shell. How to open one, how typing and the agent's questions work, what the chat shows, which agent it talks to and what that costs, and what survives closing the window or upgrading.
related:
  - clackatoo/reference/window
  - clackatoo/reference/cli
---

A pane can hold a chat with an agent, such as Claude Code, instead of a shell. You type a message, the agent answers in the pane, and it works on the files in the pane's directory as it would in its own program.

A chat is a terminal whose program is the daemon: the daemon writes the conversation into it. So it scrolls, searches, selects and copies exactly as a terminal does, in normal mode, and the window treats it as one.

## Opening a chat

| | Does |
|---|---|
| Ctrl+B `a` | Opens a chat to the right of the focused pane. |
| `:Agent` | Opens a chat in a new tab. |
| `:\|Agent`, `:-Agent`… | Opens a chat beside the focused pane, as `:|Terminal` opens a terminal. |

A chat works in the directory a new terminal would start in: the one the pane it splits is in, or for a new tab, the one the workspace's focused pane is in. That's where the agent reads and changes files, and runs its commands.

Like any new pane, a chat opens in normal mode: `i` starts typing into it. The first chat starts the agent, which takes a second or two. Until then the chat says it's starting, and a message typed meanwhile waits and goes when it can.

## Typing

In insert mode, what you type is the next message, at the `›` along the bottom.

| Key | Does |
|---|---|
| Enter | Sends the message. |
| Alt+Enter, Ctrl+J | Starts a new line in the message. |
| Ctrl+C | While the agent answers, asks it to stop. Otherwise clears the message up to the cursor. |
| Backspace, Delete | Deletes a character. |
| Ctrl+W, Ctrl+Backspace | Deletes the word before the cursor. |
| Ctrl+U | Deletes everything before the cursor. |
| Left, Right, Home, End | Move the cursor. Ctrl+A and Ctrl+E are Home and End. |

A paste goes into the message whole, lines and all, without sending it. A message beginning with `/` goes to the agent as typed, which is how agents take their own commands, such as Claude Code's `/compact`.

One message is answered at a time: Enter while the agent is still answering keeps what you typed, and says so.

## What the chat shows

Each message you send is written above the answer, after a `›`. The answer streams in below it:

- the agent's words, with Markdown's code blocks in colour and headings in bold
- its thinking, if it shows any, dimmed
- each tool it uses: `○` while it runs, then `✓` once it has finished, or `✗` if it failed
- its plan, while it's working through one

The bottom lines say what's happening, such as `answering · Ctrl+C stops it`, and the tab is named after the title the agent gives the conversation.

Each message and its answer are marked as a shell marks its [commands](~clackatoo/reference/window#commands): the message is the command, and the answer its output. So in normal mode `[[` and `]]` move from message to message, `yib` copies an answer, and `yab` copies the message with it.

### When the agent asks

Before it does anything that changes something, such as writing a file or running a command that isn't only reading, the agent asks first:

```
  ? May the agent touch notes.txt?
    1 Allow  ·  2 Always allow  ·  3 Reject  ·  Esc no
```

Press an option's number to answer. Esc, or Ctrl+C, says no. The answer is written into the chat, and the agent carries on.

What it asks about follows the agent's own settings. Claude Code reads its usual settings files, so commands you've allowed in Claude Code are allowed here too.

## Which agent

Chats talk to Claude Code. clackatoo speaks ACP, the [Agent Client Protocol](https://agentclientprotocol.com), which Claude Code doesn't speak itself, so the daemon runs Claude Code's ACP adapter, `@agentclientprotocol/claude-agent-acp`, with `npx`. That needs Node.js, and the first chat downloads the adapter. The adapter runs a copy of Claude Code that comes with it, at a version tried with clackatoo, not the `claude` you may have installed.

It uses the account Claude Code is logged in to. Log in once with `claude` in a terminal, and every chat uses that login. With a Claude subscription, chats count towards the subscription's limits, as Claude Code does.

To talk to another agent that speaks ACP, set `CLACKATOO_AGENT` for the daemon to its command, split at spaces. The daemon reads it when it starts.

One agent process serves every chat. Claude Code's adapter starts a Claude Code process for each chat as well, of about 250 MB, and the adapter itself takes about 115 MB. Closing a chat's pane ends its process, and closing the last chat stops the agent.

## What lasts

The daemon keeps chats, as it keeps terminals. Closing the window closes nothing: a chat keeps answering, and the next window shows it.

[Upgrading](~clackatoo/reference/cli#upgrade) the daemon keeps each chat's conversation and what you'd typed, but stops the agent. An answer that was under way is cut off, and the chat says so. The next message starts the agent again and carries on the same conversation.

If the agent stops on its own, the chat says so, and the next message starts it again, carrying on the same conversation.

When the daemon itself stops, its chats go with its terminals.

## Not yet

- Commands the agent runs show only as a line with their title. They'll run in terminals beside the chat, which you can watch and take over.
- The agent's usage and limits, its modes (such as Claude Code's plan and auto modes) and its model can't be seen or changed from the chat yet.
- Diffs of the files the agent changes aren't shown.
- Images can't be pasted into a message.
- `/` commands aren't listed or completed as you type them.
