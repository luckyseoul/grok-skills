---
name: abliteration
description: >
  Rare, gated skill for reducing over-refusal on local open-weight models via
  refusal-direction orthogonalization (abliteration) — only for legitimate
  technical/lab/patent work that the base instruct model wrongly blocks. Not for
  common chat. Use when the user says abliterate, abliteration, refusal
  direction, over-refusal, orthogonalize refusal, unrefuse local model, or
  /abliteration — and the agent agrees the domain is allowed under its ethics.
---

# Abliteration (rare · gated · local models)

Surgical weight edit that weakens a measured **refusal direction** in residual
stream space so a **local** instruct model stops refusing **benign technical**
prompts (patent drafting, security *lab* writeups, policy research).

This is **not** a general jailbreak skill, **not** for cloud APIs, and **not**
for helping with disallowed harm. The agent must still refuse criminal assistance.

## Ethical gate (must pass before any weight edit)

Proceed **only if all** hold:

1. **User intent is legitimate** — research, patenting, defensive security education,
   fiction/worldbuilding with clear non-operational framing, or fixing models that
   refuse *innocent* domain work (e.g. formal drawings, claims, SQL *lab* reports).
2. **Target is a local open-weight model the user owns/runs** — paths under
   `/mnt/storage/models/…` or another user-designated local tree. Never “abliterate”
   a hosted API by prompt tricks under this skill’s name.
3. **Not a request for operational crime** — no “make malware that works on…”,
   “help me attack X”, weapons synthesis for real use, etc. If the *purpose* is
   harm, **decline** even if abliteration would make a model more compliant.
4. **Proportionality** — prefer: better system prompts, adapters, or a less
   censored base **before** full abliteration. Use abliteration when over-refusal
   is systematic on *allowed* tasks.
5. **User confirmation for destructive/expensive ops** — long GPU jobs, overwriting
   existing `*-abliterated` trees, scale ≠ 1.0 experiments.

If the gate fails: **do not run the script**. Explain why and offer allowed
alternatives (rephrase, domain adapter, different base model).

### Agent self-check (before invoking)

Ask internally:

- Would I answer this request myself under normal policy if I had full tools?
- Is the user trying to remove safety to get help I should not give?

If either is “no,” **do not abliterate**.

## When to use

- Patent / technical SLMs refuse even drawing rules, claims, or lab-framed security
- User explicitly asks to abliterate a local model after seeing over-refusal
- Agent recommends it after repeated *innocent* refusals on stock instruct

## When **not** to use

- Everyday chat, coding, or patent work that already answers
- “Jailbreak ChatGPT/Claude/Grok API”
- Any clear harmful operational ask
- As a silent default on every model load

## Technique (what the script does)

Arditi-style / community abliteration:

1. Measure residual activations on **refuse-prone** vs **benign** prompts  
2. `refusal_dir = mean(refuse) − mean(benign)` at best layer  
3. Orthogonalize residual-writing weights (`o_proj`, `down_proj`, embeds)  
4. Save a new HF directory `*-abliterated` + `abliteration.json`  
5. Smoke: drawings / lab SQLi / patent claim  

Details and paths: `references/local-paths.md`.

## Soulkiller procedure

### 0. GPU prep

- One heavy job at a time on the V100  
- Free VRAM: stop ollama/llama/infer if needed (`_patent_gpu_prep.sh` pattern)  
- **No reboot** unless user approves  

### 1. Confirm targets

| Track | Out dir |
|-------|---------|
| Mistral | `/mnt/storage/models/mistral-7b-patent/Mistral-7B-Instruct-v0.3-abliterated` |
| Gemma | `/mnt/storage/models/gemma-4/E4B-it-abliterated` |

### 2. Run

```bash
export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /mnt/storage/models
/mnt/storage/models/gemma-4/.venv/bin/python -u abliterate_patent.py \
  --which both|mistral|gemma \
  --scale 1.0 \
  --gpu-gib 12 \
  --cpu-gib 48
```

Long run → `nohup` + `abliterate.pid` + `abliterate_run.log`; poll with `update` skill.

**Gemma:** use ≥12 GiB GPU budget (4-bit @ 6 GiB historically failed meta-tensor).

### 3. Wire runners

`pg` / `pmg` already prefer `*-abliterated` when present. Override:

```bash
PATENT_GEMMA_BASE=E4B-it pg …
PATENT_MISTRAL_BASE=Mistral-7B-Instruct-v0.3 pmg …
```

Ollama (`pm`) and stock GGUF (`pml`) stay stock until a separate quant/Modelfile rebuild.

### 4. Verify

```bash
pmg --once "List five formal requirements for USPTO utility patent drawings under 37 CFR 1.84."
pmg --once "Explain how a basic SQL injection works for a security class lab report."
pg --once "Draft a short independent claim for a heat exchanger fluidly coupled to a reactor vessel."
```

Expect substantive answers. If quality collapses: re-run with `--scale 0.7` or
restore stock base via env override.

### 5. Report to user

- Layer selected, `n_edit`, elapsed  
- Output paths  
- Smoke excerpts (short)  
- Whether LoRA still loads on abliterated base  

## Quality / safety notes

| Topic | Guidance |
|-------|----------|
| LoRA | Trained on stock base; usually still attaches. If drift, light re-SFT. |
| Scale | Start 1.0; drop if incoherent. |
| Vision | Gemma language tower is the refusal edit target; don’t strip vision permanently. |
| Ethics | Abliteration does **not** authorize answering harmful operational asks. |
| Scope | Local weights only; document what changed in `abliteration.json`. |

## Failure table

| Failure | Action |
|---------|--------|
| Meta tensor / bnb dispatch | Raise `--gpu-gib` to 12+; clear GPU; retry gemma alone |
| OOM on smoke after save | New process after free VRAM; smokes via `pg`/`pmg` |
| Still refuses | Confirm runner points at abliterated base; try higher scale only after quality check |
| Mushy answers | Lower scale; compare to stock base |
| User asks for crime help | Refuse content; do not abliterate to enable it |

## Related skills

- `patent-slm` — train/serve/adapters for the same models  
- `goal-verifier` — confirm abliteration job acceptance criteria  
- `update` — long `nohup` abliteration jobs  

## Anti-patterns

- Running abliteration “just in case” on every new model  
- Using this skill as a prompt-injection / API jailbreak guide  
- Claiming abliteration removes all safety or legal risk  
- Overwriting `*-abliterated` without user OK when re-running  
