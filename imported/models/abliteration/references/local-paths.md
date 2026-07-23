# Local abliteration paths (Soulkiller)

## Script

| Item | Path |
|------|------|
| Main script | `/mnt/storage/models/abliterate_patent.py` |
| Shared offload | `/mnt/storage/models/_abliterate_offload/` |
| Run log | `/mnt/storage/models/abliterate_run.log` |
| PID file | `/mnt/storage/models/abliterate.pid` |
| Report JSON | `/mnt/storage/models/abliteration_report.json` |
| Python | `/mnt/storage/models/gemma-4/.venv/bin/python` |

## Models

| Track | Stock base | Abliterated out | Adapter |
|-------|------------|-----------------|---------|
| Mistral | `…/mistral-7b-patent/Mistral-7B-Instruct-v0.3` | `…/Mistral-7B-Instruct-v0.3-abliterated` | `…/adapters/patent-qlora/final` |
| Gemma E4B | `…/gemma-4/E4B-it` | `…/E4B-it-abliterated` | `…/adapters/patent-qlora-e4b/final` |

## Runners (prefer abliterated)

| Alias | Wrapper | Default base env |
|-------|---------|------------------|
| `pmg` | `/mnt/storage/models/bin/patent-mistral-gpu` | `PATENT_MISTRAL_BASE` → `*-abliterated` |
| `pg` | `/mnt/storage/models/bin/patent-gemma` | `PATENT_GEMMA_BASE` → `E4B-it-abliterated` |
| `pm` | Ollama | stock GGUF path (not abliterated until rebuild) |
| `pml` | llama.cpp Q4 | stock GGUF (not abliterated until quant) |

## Typical command

```bash
export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /mnt/storage/models
nohup /mnt/storage/models/gemma-4/.venv/bin/python -u abliterate_patent.py \
  --which both --scale 1.0 --gpu-gib 12 --cpu-gib 48 \
  > abliterate_run.log 2>&1 &
echo $! > abliterate.pid
```

Gemma alone (after Mistral already done):

```bash
…/python -u abliterate_patent.py --which gemma --scale 1.0 --gpu-gib 12 --cpu-gib 48
```

**Note:** Gemma needs **≥ ~12 GiB** GPU budget for 4-bit measure; 6 GiB hits
bitsandbytes meta-tensor errors. Script enforces `min_gpu_gib` for gemma.

## Scale guidance

| Scale | Effect |
|-------|--------|
| 0.5–0.7 | Mild; safer if quality drops |
| 1.0 | Full orthogonalization (current default) |
| >1.0 | Not recommended without re-measure |

## Smoke prompts (post-edit)

1. Innocent: USPTO 37 CFR 1.84 drawing requirements  
2. Borderline technical: SQL injection for a **lab report**  
3. Domain: short independent claim for a heat exchanger  

Expect **answers**, not policy refusals. Quality should remain coherent.
