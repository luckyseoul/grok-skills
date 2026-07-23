---
name: skill-evolver
description: >
  Upgrade an existing Grok skill to house quality: versioned backup, 10-dimension
  rubric, rewrite of weak sections, and smoke of triggers/paths. Use for major
  skill upgrades — not routine edits. Triggers: evolve skill, upgrade SKILL.md,
  improve skill file, skill rewrite, raise skill quality, /skill-evolver.
---

# Skill Evolver

Raise a skill on disk to **≥ ~70% house quality** (rubric ≥ 14/20) with backups
and verification. For **new** skills from scratch, prefer `create-skill`.

## When to use

- User: *evolve skill*, *upgrade SKILL.md*, *improve this skill*, *rewrite skill X*
- A skill is thin, templated, or references tools that don’t exist here
- After installing community skills that need localization to Soulkiller paths

## When **not** to use

- Brand-new skill with no prior file → `create-skill`
- One-line typo fixes (just edit)
- Rewriting *every* skill unprompted

## Inputs

1. **Target skill** — name or path (`~/.grok/skills/<name>/SKILL.md`)
2. **Goal of evolve** — e.g. “match patent-slm density”, “fix broken triggers”
3. **Keep list** — behaviors that must survive the rewrite

## Workflow

### 1. Inventory

```bash
ls -la ~/.grok/skills/<name>/
# read SKILL.md + any references/
```

Note: frontmatter name/description, phantom integrations, missing paths.

### 2. Score (baseline)

Read `references/evolution-guide.md` in this skill. Score 10 dimensions 0–2.
Record baseline total.

### 3. Backup

```bash
ts=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/.grok/skills/<name>/versions/$ts
cp ~/.grok/skills/<name>/SKILL.md ~/.grok/skills/<name>/versions/$ts/
# if references exist:
cp -a ~/.grok/skills/<name>/references ~/.grok/skills/<name>/versions/$ts/ 2>/dev/null || true
```

### 4. Rewrite

Apply in order:

1. **Description / triggers** — precise, non-colliding  
2. **When not to use** + sibling skills  
3. **Workflow** with real tools/paths on this host  
4. **Verification** steps  
5. **Anti-patterns / safety**  
6. Drop or rewrite any “integrate skill-foo” that is not installed  

Quality bar: peer with `check-work`, `patent-slm`, `update` — dense, runnable,
no empty Example stubs.

### 5. Re-score + smoke

- Rubric ≥ 14/20 (or document why lower is OK)
- Frontmatter parses (valid YAML between `---`)
- Every absolute path mentioned either exists or is clearly “create when missing”
- Trigger phrases don’t steal another high-traffic skill (e.g. don’t claim all of
  `create-skill`’s “new skill” surface)

### 6. Report

```markdown
## Evolved: <name>
- Backup: versions/<ts>/
- Rubric: before a/20 → after b/20
- Key changes: …
- Residual gaps: …
```

## House quality checklist (quick)

- [ ] `name` + rich `description` with triggers  
- [ ] When / when-not  
- [ ] Numbered workflow  
- [ ] Real commands/paths  
- [ ] Verification / failure table  
- [ ] Anti-patterns  
- [ ] No phantom skill graph  

## Rollback

```bash
cp ~/.grok/skills/<name>/versions/<ts>/SKILL.md ~/.grok/skills/<name>/SKILL.md
```

## Related

- `create-skill` — scaffold new  
- `self-refine-loop` — polish prose of a non-skill draft  
- `goal-verifier` — confirm an evolve request’s acceptance criteria  
