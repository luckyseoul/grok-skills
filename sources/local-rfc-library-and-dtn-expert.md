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

## Status (as of 2026-05-27)

**Core DTN/BPv7 family present:**
- RFC 9171, 9172, 9174, 8949 (CBOR), 5050

**Style, Process & Submission Guides present:**
- RFC 7322 (Style Guide)
- RFC 8874 & 8875 (GitHub usage + admin for IETF)
- Living guides: authors.ietf.org + RFC Editor styleguide (HTML snapshots in guides/)

**XML Coding Guide (the important one for writing the draft):**
- RFC 7991 (xml2rfc v3 Vocabulary — the primary spec)
- RFC 7992–7996 (HTML, PDF, Text, SVG formats)
- Full `external/xml2rfc/` clone (best current practical examples and docs from the IETF Tools team)

**cbor2:**
- Full clone of https://github.com/agronholm/cbor2 in external/cbor2/ (README + excellent docs/ on deterministic encoding, canonical_encoder, etc. — directly relevant to BPSec and our simulator).

**Expert layer:**
- `dtn-bpv7-expert` skill knows to route XML authoring questions to RFC 7991 + the xml2rfc clone, CBOR determinism questions to cbor2 docs + RFC 8949, and GitHub process questions to 8874/8875.

Fetch tools (`tools/fetch-rfc`, `tools/fetch-draft`) exist for ongoing maintenance.

The `dtn-bpv7-expert` skill is instructed to always quote the local files for citations.

## Future

- Bulk import of remaining high-relevance RFCs (especially CDDL 8610/9682 and any others referenced in the draft's security considerations or references section)
- Keep all revisions of draft-perry-dtn-cpb in the drafts/ tree
- Add more curated cross-reference notes in the `dtn/` directory
- Periodic refresh of the core specs + the two external tool repos (cbor2 and xml2rfc)
