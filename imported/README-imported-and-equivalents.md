# Imported skills & user-owned equivalents

## Policy
| Source | Allowed? | Action |
|--------|----------|--------|
| Hermes Agent skills | MIT | Copy with provenance stamp |
| Stijnman/grok-custom-skills | MIT | Copy with provenance stamp |
| Grok **bundled** product skills | Product-shipped; not re-licensed here | **Do not** copy into GitHub catalog; use **equivalents** below or call product skill in-session |
| User original skills | MIT (luckyseoul) | Canonical |

## MIT imports (this machine)
Hermes: github-pr-workflow, github-code-review, github-issues, github-repo-management, codebase-inspection, arxiv, architecture-diagram, ocr-and-documents, research-paper-writing, linux-app-build-install  
Stijnman: session-handoff-packager, natural-language-to-skill, privacy-redactor, oss-repo-maintainer, skill-rubric-reviewer, web-scraper, tool-discovery-engine, skill-researcher

## User-owned equivalents (for bundled capabilities)
| Equivalent | Bundled cousin | Difference |
|------------|----------------|------------|
| `ietf-design` | design | I-D / protocol design, not app PR DAG |
| `draft-cold-review` | review | Internet-Draft honesty cold-read |
| `gh-pr-watch` | pr-babysit | gh-native PR watch; original text |
| `office-pandoc` | docx / pptx | pandoc path, not product Office scripts |
| `plan-execute-lite` | execute-plan | Small sequential plans only |
| `spacexai-app` | build-with-ai | Short xAI provider default |
| `workflow-rhai` | create-workflow | Short Rhai authoring checklist |

Re-run `~/Projects/grok/grok-skills/tools/mirror-skills.sh` after changes.
