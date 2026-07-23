---
name: patent-slm
description: >
  Train and run local patent-domain specialist SLMs: Gemma 4 on Soulkiller (V100) and
  Mistral-7B for Jetson Orin / Ollama edge deploy. Covers QLoRA, hybrid GPU→CPU→disk
  offload, vision-safe LoRA for formal drawings (37 CFR 1.84), llama.cpp CUDA serve,
  and Ollama Modelfiles. Use when the user says patent SLM, fine-tune patents, QLoRA
  Gemma, Mistral patent, Orin SLM, ollama mistral, patent drafting model, hybrid offload,
  GPU then RAM, /patent-slm, or work under /mnt/storage/models/gemma-4,
  /mnt/storage/models/mistral-7b-patent, or /mnt/storage/patents.
---

# Patent-domain SLMs (Gemma 4 + Mistral 7B)

You operate **two** patent specialist tracks on NAS:

| Track | Role | Primary runtime |
|-------|------|-----------------|
| **Gemma 4 E4B** | Multimodal-capable, V100 lab model | HF QLoRA + adapter infer |
| **Mistral 7B Instruct** | **Orin / edge SLM** (~4.4GB Q4) | Ollama + llama.cpp CUDA |

Paths and scripts below are the source of truth.

## Layout (NAS)

| Path | Role |
|------|------|
| `/mnt/storage/models/gemma-4/` | Gemma models, train/infer, CUDA llama.cpp, datasets |
| `/mnt/storage/models/gemma-4/E4B-it/` | Primary V100 multimodal base |
| `/mnt/storage/models/gemma-4/26B-A4B-it/` | Larger specialist (QLoRA scale-up) |
| `/mnt/storage/models/gemma-4/datasets/` | Shared `patent_sft_*.jsonl` + figures |
| `/mnt/storage/models/gemma-4/adapters/patent-qlora-e4b/final/` | Gemma LoRA |
| `/mnt/storage/models/mistral-7b-patent/` | **Orin track**: train/infer/Modelfile/GGUF |
| `/mnt/storage/models/mistral-7b-q4km/` | Stock Q4_K_M GGUF |
| `/mnt/storage/patents/` | USPTO PDF corpus + practice docs |
| `/mnt/storage/models/gemma-4/.venv/` | Shared py3.11 + torch cu124 (symlinked by Mistral tree) |
## Which model when

- **User says Orin / edge / ollama / lightweight / Jetson** → **Mistral 7B** track.
- **User says multimodal / drawings vision / Gemma / V100 lab** → **Gemma 4** track.
- Default for portable patent SLM: **Mistral 7B Q4**.

## Non‑negotiable hardware rules

1. **V100 = no bf16 AMP.** `TrainingArguments(fp16=False, bf16=False)`; LoRA adapters in **fp32**.
2. **Hybrid memory always:** fill GPU budget first, then CPU RAM, then disk offload folder.
3. **Never reboot** without explicit user OK (GPU thrash recovery may need module reload).
4. **No password/secrets in files.** Prefer existing venv; install only what is missing.
5. **CPU-only llama.cpp is not “done.”** Prefer CUDA `llama-cli` with `-ngl` / `--n-gpu-layers`.
6. **Gemma vision is in scope** for patent drawings — do not permanently exclude vision towers.
7. **Orin:** prefer Q4 GGUF fully on GPU (`-ngl 999`); 7B Q4 ≈ 4.4GB fits 8GB+ Orin.

## Hybrid offload model

```
GPU VRAM (budgeted GiB)  →  first layers / activations
CPU system RAM           →  overflow weights
Disk offload / mmap      →  if RAM tight (NAS path ok)
```

### Training (HF accelerate)

`train_patent_qlora.py`:

- `device_map="auto"` + `max_memory={0: "12GiB", "cpu": "40GiB"}`
- `offload_folder=/mnt/storage/models/gemma-4/offload`
- 4-bit NF4 base via bitsandbytes; `llm_int8_enable_fp32_cpu_offload=True`
- **Do not** call `prepare_model_for_kbit_training()` (fp32 cast OOMs on 16GB)

### Inference — two supported paths

**A. Trained adapter (primary product path)**

```bash
bash /mnt/storage/models/gemma-4/run_patent_gpu.sh
# or:
/mnt/storage/models/gemma-4/.venv/bin/python -u \
  /mnt/storage/models/gemma-4/infer_patent_gpu.py \
  --adapter /mnt/storage/models/gemma-4/adapters/patent-qlora-e4b/final \
  --gpu-gib 13 --cpu-gib 40
```

Loads E4B 4-bit + PEFT adapter on CUDA; hybrid `max_memory` if needed.

**B. llama.cpp hybrid GGUF**

```bash
# Build once (CUDA sm_70, gcc-14 host, CUDA 12.9)
bash /mnt/storage/models/gemma-4/build_llama_cpp.sh

# Serve: GPU layers first, rest CPU/RAM
export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:${LD_LIBRARY_PATH}
bash /mnt/storage/models/gemma-4/serve_llama_cpp.sh /path/to/model.gguf 40
# lower ngl if cudaMalloc OOM (26B Q4 ~16GB ≈ full V100)
```

Binary: `/mnt/storage/models/gemma-4/llama.cpp/build/bin/llama-cli` must link `libggml-cuda`.

## Vision-safe LoRA (patent drawings)

Gemma 4 vision uses **`Gemma4ClippableLinear`** — PEFT cannot wrap that class.

**Correct approach:** collect real `nn.Linear` / `Linear4bit` only, including each
wrapper’s inner **`.linear`**:

```python
from train_patent_qlora import collect_lora_linear_targets
targets = collect_lora_linear_targets(model, include_vision=True, include_audio=False)
# language q_proj/... + vision_tower.*.linear
```

- Default: `--include-vision` (on), `--include-audio` (off)
- Figure corpus: `extract_patent_figures.py` → `datasets/patent_figures_sft.jsonl` + PNGs
- First short train may be **text SFT** while still attaching vision LoRA targets
- Multimodal image-batch collator is the next scale step, not a permanent skip of vision

## Train entry (short proof run)

```bash
cd /mnt/storage/models/gemma-4
.venv/bin/python -u train_patent_qlora.py \
  --gpu-gib 12 --cpu-gib 40 \
  --max-steps 40 --max-seq-len 768 \
  --include-vision --no-include-audio \
  --out /mnt/storage/models/gemma-4/adapters/patent-qlora-e4b \
  --proof-dir /tmp/…   # only if goal harness requires; else omit
```

Expect: language+vision target counts printed; loss declines; adapter under `…/final/`
(`adapter_config.json`, `adapter_model.safetensors`).

## CUDA build gotchas (Soulkiller)

| Issue | Fix |
|-------|-----|
| gcc-15 too new for nvcc | Pin `gcc-14` / `g++-14` as host compiler |
| glibc `noexcept` vs `math_functions.h` | CUDA 12.9 + surgical `noexcept(true)` on the 6 clashing `extern` decls in `math_functions.h` (cospif/sinpif/rsqrtf/cospi/sinpi/rsqrt) |
| Missing cuBLAS | `libcublas-12-9` + `libcublas-dev-12-9` |
| V100 | `CMAKE_CUDA_ARCHITECTURES=70` (CUDA 13 drops sm_70 offline compile) |
| 26B Q4 GGUF ~16GB | Use **partial** `--n-gpu-layers` (e.g. 12–40); full `-ngl 999` OOMs |

## Dataset / tests

- Text SFT: `datasets/patent_sft_train.jsonl` (+ eval + smoke prompts)
- Figures: `datasets/patent_figures_sft.jsonl` (image paths in user content)
- Unit tests (must stay green):

```bash
cd /mnt/storage/models/gemma-4
.venv/bin/python -m unittest tests.test_dataset_and_train_helpers -v
```

Tests cover: hybrid `max_memory`, vision `.linear` targets, AMP-off flags, saved adapter, llama-cli presence.

## Recovery (GPU wedged, no reboot unless asked)

1. Kill train/infer CUDA clients only (not broad `fuser -k` on live sessions).
2. Prefer `nvidia-smi` reset / stop stuck containers over reboot.
3. If modules leak with zero holders: **ask user** before reboot.
4. Steam-headless docker can pin the GPU — stop container carefully before module reload.

## Workflow when invoked

1. **Status** — `nvidia-smi`; confirm single train; adapter + datasets exist.
2. **Train or resume** — short steps first; vision-safe LoRA; AMP off; hybrid budgets.
3. **Smoke on GPU** — `infer_patent_gpu.py` / `run_patent_gpu.sh` (not CPU llama).
4. **Serve** — CUDA llama with partial ngl, or HF adapter path.
5. **Figures** — extract / multimodal SFT when user needs drawing specialization.
6. **Proof** — adapter files + non-empty generations + unit tests; never claim GPU success from CPU-only runs.

## What not to do

- Do not use vLLM as the hybrid offload runtime here.
- Do not permanently `exclude_modules` all vision.
- Do not enable bf16 GradScaler on Volta.
- Do not thrash the NIC/NAS with parallel maxed downloads during train.
- Do not embed user passwords in skill files or repo.

## Mistral 7B track (Orin / Ollama)

Tree: `/mnt/storage/models/mistral-7b-patent/`

| Artifact | Path |
|----------|------|
| HF base | `Mistral-7B-Instruct-v0.3/` (`bash download_mistral_hf.sh`) |
| Stock Q4 GGUF | symlink → `../mistral-7b-q4km/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf` |
| Datasets | symlink → gemma-4 patent SFT JSONL |
| Train | `train_patent_qlora.py` (standard LoRA targets, no vision) |
| Infer | `infer_patent_gpu.py` |
| Serve | `serve_llama_cpp.sh` (`-ngl 999` fits Orin) |
| Ollama | `Modelfile.ollama` → `ollama create patent-mistral-7b -f Modelfile.ollama` |
| Local ollama base | already on host: `mistral:7b` (4.4GB) |

```bash
cd /mnt/storage/models/mistral-7b-patent
bash download_mistral_hf.sh
.venv/bin/python -u train_patent_qlora.py --max-steps 60 --gpu-gib 12
.venv/bin/python -u infer_patent_gpu.py
export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:$LD_LIBRARY_PATH
bash serve_llama_cpp.sh ./Mistral-7B-Instruct-v0.3-Q4_K_M.gguf 999
ollama create patent-mistral-7b -f Modelfile.ollama
```

### Orin deploy checklist

1. Copy Q4 GGUF (or merged patent GGUF) to Orin — ~4.4GB.
2. Prefer **Ollama** on Orin (`patent-mistral-7b` Modelfile) or CUDA `llama-cli` for Jetson arch.
3. Optional: after QLoRA, `convert_lora_to_gguf.py` then `llama-cli --lora` / Ollama ADAPTER.
4. Do **not** ship full Gemma 26B to Orin; keep multimodal work on V100.

### Mistral tests

```bash
cd /mnt/storage/models/mistral-7b-patent
.venv/bin/python -m unittest tests.test_mistral_helpers -v
```

## Quick reference commands

```bash
# Health
nvidia-smi
ollama list   # expect mistral:7b

# Gemma unit tests / train / infer
cd /mnt/storage/models/gemma-4
.venv/bin/python -m unittest tests.test_dataset_and_train_helpers -v
.venv/bin/python -u train_patent_qlora.py --gpu-gib 12 --cpu-gib 40 --max-steps 40 --include-vision
bash run_patent_gpu.sh --prompt "List five 37 CFR 1.84 drawing requirements."

# Mistral (Orin track)
cd /mnt/storage/models/mistral-7b-patent
.venv/bin/python -u train_patent_qlora.py --max-steps 60 --gpu-gib 12
bash serve_llama_cpp.sh ./Mistral-7B-Instruct-v0.3-Q4_K_M.gguf 999
ollama create patent-mistral-7b -f Modelfile.ollama

# Rebuild CUDA llama (shared)
bash /mnt/storage/models/gemma-4/build_llama_cpp.sh
```

## Shell aliases (Soulkiller)

Installed in `~/.bash_aliases` + wrappers under `/mnt/storage/models/bin/`.

| Alias | Command | Backend |
|-------|---------|---------|
| `pm` / `patent-mistral` | **interactive chat** (default) | Ollama `patent-mistral-7b` (Orin-ready) |
| `pg` / `patent-gemma` | **interactive chat**; `--once` for one-shot | Gemma4 **E4B-it-abliterated** + QLoRA |
| `pml` / `patent-mistral-llama` | **interactive chat**; `--once` for one-shot | Mistral Q4 GGUF CUDA llama.cpp |
| `pmg` / `patent-mistral-gpu` | **interactive chat**; `--once` for one-shot | Mistral **abliterated** + QLoRA |
| `patent-models` | list installed | ollama + adapter paths |
| `patent-help` | print cheat sheet | — |

Chat notes: `pg`/`pmg` compact history at **75%** of effective ctx (default cap 8192).
In-chat: `/quit` `/clear` `/ctx` `/compact` `/max N`.

```bash
source ~/.bash_aliases   # or open a new shell
pg                       # open Gemma patent chat
pmg --once "List five 37 CFR 1.84 drawing requirements."
patent-models
```

## Abliteration (over-refusal)

If stock instruct refuses innocent patent/lab asks, use the **`abliteration`** skill
(rare, ethically gated). Artifacts:

| Model | Abliterated dir |
|-------|-----------------|
| Mistral | `…/mistral-7b-patent/Mistral-7B-Instruct-v0.3-abliterated` |
| Gemma | `…/gemma-4/E4B-it-abliterated` |

Script: `/mnt/storage/models/abliterate_patent.py`. Prefer skill **`/abliteration`**
over ad-hoc runs so ethical gates and smoke checks stay consistent.

Start by checking GPU health and which artifact the user needs: **Gemma train/infer**, **Mistral/Orin**, **ollama**, **llama serve**, **abliteration**, or **figure multimodal data**.
