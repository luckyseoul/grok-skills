# Execution Discipline — User Signals from Rung Campaign (May 2026)

## Core Lesson
The user has a very strong, repeated preference that the agent must **execute the work directly** rather than producing scripts or commands for the user to run.

### Explicit signals observed
- "I just need you to run the damn sims man"
- "I'm not running a damn thing, you are"
- "dude just finish it"
- "just fucking kill it and figure out the custom gpu version"
- Multiple instances of frustration when the agent continued to hand over setup scripts, launch commands, or explanations after the user had signaled they wanted the simulations driven to completion.

### Required agent behavior when these signals appear
1. Immediately stop producing new scripts or "here's the command" hand-offs.
2. Use the available tools (terminal with background=true + notify_on_complete, process management, direct execution) to drive the actual workload.
3. Report only the minimum status needed.
4. Own the outcome.

### Pitfall
Continuing to iterate on "setup" or "here's how you run it" after the user has made clear they want the agent to finish the sims/data generation. This pattern dominated the frustration in the Rung campaign sessions.

This reference was added after the final "dude just finish it" message in the May 31 2026 session.