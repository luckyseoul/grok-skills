# Patent SLM paths (Soulkiller)

## Gemma 4 (V100 / multimodal)

- Models root: `/mnt/storage/models/gemma-4/`
- Train: `train_patent_qlora.py`
- GPU infer: `infer_patent_gpu.py`, `run_patent_gpu.sh`
- Figure extract: `extract_patent_figures.py`
- llama CUDA build: `build_llama_cpp.sh` → `llama.cpp/build/bin/llama-cli`
- Serve: `serve_llama_cpp.sh`
- Adapter: `adapters/patent-qlora-e4b/final/`
- Datasets: `datasets/patent_sft_*.jsonl`, `patent_figures_sft.jsonl`
- Tests: `tests/test_dataset_and_train_helpers.py`

## Mistral 7B (Orin / Ollama)

- Root: `/mnt/storage/models/mistral-7b-patent/`
- Stock Q4: `/mnt/storage/models/mistral-7b-q4km/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf`
- Ollama local: `mistral:7b` (snap models under `/var/snap/ollama/common/models/`)
- Train / infer / serve / Modelfile: same root
- Tests: `tests/test_mistral_helpers.py`

## Shared

- Patents corpus: `/mnt/storage/patents/`
- CUDA toolkit for llama: `/usr/local/cuda-12.9` (sm_70 + g++-14)
- Venv: `/mnt/storage/models/gemma-4/.venv` (Mistral tree symlinks it)
