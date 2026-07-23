# BBP Video PoC Skill

**Name:** bbp-video-poc  
**Purpose:** Specialized skill for preparing professional, submission-ready video proof-of-concepts (PoCs) for bug bounty and OSS security contribution reports. Focuses on safe, local-only reproductions that clearly demonstrate the vulnerability without affecting production systems.

## Core Capabilities
- Generate detailed, timed video recording scripts tailored to specific bug bounty programs' recommended local testing environments (e.g., GitLab GDK, Mattermost Docker self-hosted, Kubernetes kind/minikube, Nuclei `nuclei -t`, Elastic Agent/Beats local, MongoDB driver Go tests).
- Produce exact terminal commands, environment setup steps, and reproduction sequences for each finding.
- Create asciinema / terminal recording commands, OBS Studio scene layouts and recording tips, voice-over narration scripts, on-screen text annotations, and timing breakdowns (e.g., "0:00-0:15: Setup", "0:15-1:30: Trigger vuln", "1:30-2:00: Show impact").
- Ensure videos highlight:
  - Root cause (show the vulnerable code path at HEAD if possible via editor or comments).
  - Attack flow / preconditions.
  - Impact (e.g., RCE, authz bypass, file write).
  - Safe reproduction only (never prod).
- Integrate with existing hunt artifacts: parse findings from `/home/nick/active-bbp-hunt-report.md` or per-program full reports.
- Suggest or generate supporting visuals (thumbnails, diagrams) using available image/video generation tools.
- Output structured deliverables: per-finding `video-poc-*.md` scripts, ready-to-run shell snippets, and a master "Video PoC Playlist" index.
- Best practices: Keep videos 2-6 minutes, professional, clear audio, high contrast terminal, demonstrate fix direction briefly if relevant.

## When to Use This Skill
- After documenting a finding with Root/Impact/Fix and local repro notes.
- Before finalizing a full report or short summary PDF.
- When user requests "video portions", "PoC video scripts", "prepare submission videos", or similar.
- For top findings or "all we've found" when prioritizing quality submissions.
- To batch-generate for a program (e.g., "do video portions for all K8s findings").

## Inputs Typically Provided
- Finding ID / title / program (e.g., "Kubernetes #2 Webhook authorizer fail-open").
- Key code snippets or file:line references at exact HEAD.
- Local repro steps already documented.
- Target environment (GDK / kind / Docker / `go run` etc.).
- Desired video length and style notes.

## Outputs
- `video-poc-<program>-<finding#>.md` with:
  - Prerequisites & one-time setup commands.
  - Step-by-step recording script (with timestamps).
  - Exact commands to paste/run.
  - Narration script.
  - Visual cues / what to show on screen.
  - Post-recording: editing notes, title/description for upload (YouTube unlisted or direct attach to report).
  - asciinema command (if terminal-heavy).
- Master index file listing all videos with links to scripts.
- Optional: Shell script to automate env setup for the PoC.
- Guidance on using `image_to_video` or similar for any animated diagram portions.

## Usage Examples / Invocation
- "Use bbp-video-poc skill to generate video script for PD #1 Nuclei code RCE."
- "Create video portions for the top 2 findings across all BBPs."
- "Batch video PoCs for all 3 Kubernetes findings using kind."
- The skill can read from the active report or be fed finding details directly.

## Implementation Notes for This Skill
- Always emphasize **local-only**, **no production impact**, and compliance with program rules (many explicitly encourage local GDK/kind/Docker for research).
- Tailor per program based on their policy language (e.g., GitLab strongly recommends GDK; K8s kind/minikube).
- For OSS bounties like ProjectDiscovery, focus on easy `nuclei -t malicious.yaml` repros that anyone can run after cloning.
- Leverage other tools/skills when needed (e.g., read the hunt report with read_file, generate images with imagine skill, run setup commands).
- Output files should be placed in `/home/nick/bbp-reports/video-pocs/` or alongside the corresponding full report.
- Maintain a clean, copy-paste friendly format so the user (or submitter) can follow along easily while recording.

## Related Artifacts
- Reads: `/home/nick/active-bbp-hunt-report.md`, individual full reports in `/home/nick/bbp-reports/`.
- Writes: Video scripts and supporting files under `/home/nick/bbp-reports/video-pocs/`.
- Can coordinate with other skills (docx, pptx, imagine) for supplementary materials.

This skill makes video PoC preparation fast, consistent, and high-quality — a key differentiator for strong bounty submissions.