# Skill evolution rubric (10 dimensions)

Score each dimension **0–2** (0 missing, 1 partial, 2 solid). Target **≥ 14/20**
before calling an evolve “done.” Below 10/20 → structural rewrite, not polish.

## Dimensions

### 1. Trigger quality (description frontmatter)
- Includes **what** + **when** + concrete trigger phrases
- Avoids colliding with unrelated skills (narrow tags)
- Slash name mentioned if there is a conventional `/name`

### 2. Scope clarity
- Clear when **not** to use
- Boundaries vs sibling skills listed

### 3. Actionable workflow
- Numbered steps an agent can execute without guessing
- Decision points and stop conditions

### 4. Environment fidelity
- Real paths, tools, and commands for **this** machine/stack
- No phantom integrations (“call skill X” that doesn’t exist)

### 5. Evidence / verification
- How to know the skill succeeded (files, tests, smokes)
- Failure modes with recovery

### 6. Safety / HITL
- Risky ops require confirmation
- Secrets never written into skill files

### 7. Brevity vs completeness
- Dense enough to run; not a novel
- Progressive disclosure: details in `references/` when long

### 8. Examples
- At least one realistic input → expected behavior
- Prefer real paths over “foo bar”

### 9. Maintainability
- Version note or changelog hint
- References instead of duplicating large specs

### 10. Style match
- Matches house style of peer skills under `~/.grok/skills/`
  (frontmatter, tables, anti-patterns section)

## Rewrite priorities

1. Fix **false triggers** and phantom dependencies first  
2. Then workflow + verification  
3. Then prose polish  

## Backup policy

Before major rewrite:

```bash
ts=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/.grok/skills/<name>/versions/$ts
cp ~/.grok/skills/<name>/SKILL.md ~/.grok/skills/<name>/versions/$ts/
# optional: copy references/
```

Rollback = restore from latest `versions/<ts>/SKILL.md`.
