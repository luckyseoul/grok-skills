# Local RFC Library + DTN/BPv7 Expert (Internal)

**Created**: 2026-05-27 during active draft-perry-dtn-cpb experimental campaign.

## Components

- `~/.grok/ietf-rfcs/` — Full local copy of key RFCs and drafts
- `~/.grok/skills/dtn-bpv7-expert/` — Expert skill that treats the local library as primary source of truth
- `~/.grok/skills/statistical-analyst/` — Complementary skill (imported + heavily tuned) for turning simulation results into rigorous claims

## Rationale

Web searches (including advanced ones) frequently:
- Cite wrong RFC versions
- Ignore errata status
- Blend draft language with final spec
- Hallucinate section numbers

For an IETF Experimental-track document on a security/reliability-sensitive topic (confidence metrics in contact plans), citation hygiene is mandatory.

## Status

Core DTN/BPv7 family (9171, 9172, 9174, 8949, 5050) fetched on creation date.

Fetch tools exist for ongoing maintenance.

The `dtn-bpv7-expert` skill is instructed to always quote the local files.

## Future

- Bulk import of remaining high-relevance RFCs (CDDL 8610/9682, more BPSec context work, CBOR updates, etc.)
- Keep all revisions of draft-perry-dtn-cpb in the drafts/ tree
- Periodic refresh of the core specs
