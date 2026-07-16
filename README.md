# VK Chat Moderator Bot

A moderation bot for VKontakte chats.

## Features

- **Anti-spam** — detects links, spam patterns
- **Profanity filter** — auto-deletes offensive messages + warnings
- **Captcha** — welcome gate for new members
- **Warning system** — 3 warnings = ban
- **Statistics** — member count, bans, warnings

## Required VK Bot Permissions

When creating a community bot token, enable the following permissions:

- **Messages** — send and receive messages in conversations
- **Manage messages** — delete messages from chats
- **Groups** — access group information for admin checks

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in VK_TOKEN and ADMIN_IDS
python -m bot.main
```

## Admin Commands

- `/mod help` — list commands
- `/mod stats` — chat statistics
- `/mod ban <id>` — ban a user
- `/mod unban <id>` — unban a user
- `/mod warn <id>` — add a warning
- `/mod reset <id>` — reset warnings
- `/mod check <id>` — check user status

## Moderation Logic

1. New member → captcha verification
2. Profanity → delete + warning
3. Spam (links, repeated characters) → delete + warning
4. 3 warnings → ban

## License

MIT
