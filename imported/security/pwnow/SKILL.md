---
name: pwnow
description: Secure password prompt skill. Prompts the user for a password using a secure (non-echoing) input method and makes it available for privileged operations (e.g. sudo) without leaving it in command history or visible on screen. Similar to how Hermes handles password prompts.
---

# pwnow - Password Prompt Skill

## Purpose
Provides a secure way to prompt for passwords in the Grok TUI/CLI environment. Use this whenever another skill or command needs elevated privileges or authentication (e.g. `sudo`, database connections, API keys, git operations, etc.).

## Usage
Call the skill directly:

```
/pwnow <command>
```

Example:
```
/pwnow sudo apt update
```

The skill will:
1. Prompt you securely for the password (input is hidden).
2. Execute the provided command, injecting the password where needed (e.g. via `sudo -S` for sudo commands).
3. Clean up after itself (password is never stored in plain text or history).

## How it works (for skill authors)
- Uses a secure input method (Python `getpass` or `read -s` equivalent).
- For `sudo` commands, it automatically uses `sudo -S` and pipes the password.
- The password is held only in memory for the duration of the command.
- Never echoes the password to the screen or logs.

## Example in another skill
If another skill needs to run a privileged command, it should call this skill instead of using raw `sudo`.

## Security notes
- Password is never persisted.
- Works best in interactive TUI sessions.
- For non-interactive use, consider environment variables or secure vaults instead.

This skill was created because Hermes uses similar secure prompting frequently for smooth operation.