# Execution Mode Communication Patterns (RCFX / Patent Work)

**Date**: 31 May 2026 (Rung Campaign sessions)

## Trigger Signals from User (shift immediately to Execution Mode)

- "youre the expert, Im just trying to get these damn sims finished"
- "I just need you to run the damn sims man"
- "today? jfc I've been stuck on this for months and you're talking in terms of days"
- "why is this running single threaded? the whole point of making 3.8 was so that it wouldnt take 4 years each rung"
- Repeated requests for "just run it" after multiple setup steps.

## Required Shift

When any of the above appear:
- Stop offering new scripts or detailed options.
- Stop explaining *why* something is set up a certain way.
- Use tools to launch the actual simulation (or data generation) directly.
- Use background + notify_on_complete for anything that will take >2 minutes.
- Report in very short status format:
  - What was launched
  - Current state / ETA if known
  - The one next thing the user must do (if anything)

## Anti-Patterns (caused frustration)

- Handing the user another `generate_*.sh` or `run_*.sh` after they have already expressed impatience.
- Long explanations of MPI flags, build decisions, or workflow philosophy once the user has said they just want the sims running.
- Framing progress in terms of "we can do this today/this week" when the user has been blocked for months.

## Good Pattern (used successfully at end of session)

Direct command blocks + "Run this. Tell me when it finishes or what the next blocker is."

Example of acceptable response after trigger:
"Running the minimal real LIGGGHTS physics case now with the correct sjkr model on the existing data. Will report output when it completes or hits the next hard blocker."

## Notes for Patent Work

User will not accept custom/non-certified code paths for final evidence. All real runs for the application must go through standard LIGGGHTS (the binary built in this session). Custom GPU DEM or other one-off tools are off-limits for the patent record.
