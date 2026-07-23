---
name: sudo
description: Secure sudo skill. Uses the pwnow password prompt skill to run commands with sudo privileges without exposing the password in history or on screen. Ideal for installing packages, system configuration, etc.
---

# sudo - Secure Sudo Execution Skill

## Purpose
Provides a convenient and secure way to execute commands with sudo. It automatically uses the pwnow skill to prompt for your password (hidden input) and runs the command via `sudo -S` (reading password from stdin).

This prevents password leakage in command history, logs, or terminal output.

## Usage
```
/sudo <full command>
```

Examples:
- `/sudo apt update && sudo apt upgrade`
- `/sudo systemctl restart nginx`
- `/sudo tailscale up`

The skill will:
1. Use pwnow to securely prompt you for your password.
2. Execute the command with sudo, piping the password.
3. Clean up (password never stored or echoed).

## How it works (for skill authors)
- Internally calls the pwnow skill for the password.
- Constructs `echo <password> | sudo -S <your command>`
- Password is handled only in memory for the duration of the execution.
- Never logs or displays the password.

## Security notes
- Relies on pwnow for the actual prompt (see pwnow/SKILL.md for details).
- Best used in interactive TUI sessions.
- For non-interactive or automated scenarios, consider passwordless sudo for specific commands via `/etc/sudoers` (with extreme caution) or other secrets management.

## Example in another skill
If a skill needs to install something or perform admin tasks:

```
Use the sudo skill:
 /sudo apt-get install -y some-package
```

This skill was added because direct sudo calls were failing in restricted environments, and secure prompting (like Hermes) makes privileged operations smooth and safe.

## Related skills
- pwnow: The underlying secure password prompt skill this depends on.
