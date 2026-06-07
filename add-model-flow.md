# Adding a New Model — Step-by-Step Flow

## 1. Find the GGUF File

Pick a small model from HuggingFace. Look for repos with "GGUF" in the name and a `Q4_K_M.gguf` file.

Check file list at:
```
https://huggingface.co/<org>/<repo>/tree/main
```

Good GGUF sources: `bartowski/`, `unsloth/`, `hugging-quants/`

## 2. Download

Use `hf` CLI (fast, handles resume):
```bash
uv run hf download <org>/<repo> <filename>.gguf --local-dir models/
```

Or `serve_cpu.sh`/`serve_gpu.sh` will auto-download via `wget` on first run (can be slow).

## 3. Add to serve_cpu.sh and serve_gpu.sh

Add a line to the `MODELS` dict in **both** files:

```bash
MODELS["<key>"]="<org>/<repo>|<local-filename>.gguf|<display description>"
```

**Important — always rename to a clear local filename.** The remote GGUF filename on HuggingFace may be ambiguous (e.g. Google's repos sometimes omit "qat" from filenames). Always choose a local filename that clearly identifies the model variant, using the repo name as the canonical source. Example of bad vs good:

- Remote: `gemma-4-E2B_q4_0-it.gguf` from repo `google/gemma-4-E2B-it-qat-q4_0-gguf`
- Bad:  `MODELS["gemma4-qat-e2b"]="...|gemma-4-E2B_q4_0-it.gguf|..."`  (no "qat" in filename, confusing)
- Good:  `MODELS["gemma4-qat-e2b"]="...|gemma-4-E2B-it-qat-q4_0.gguf|..."` (matches repo name, clear)

`serve_cpu.sh` uses `wget -O "$MODEL_PATH" "$MODEL_URL"` — the URL points to the remote filename, but the file is saved locally with the clean name you choose.

Example:
```bash
MODELS["qwen3.5-2b"]="unsloth/Qwen3.5-2B-GGUF|Qwen3.5-2B-Q4_K_M.gguf|Qwen3.5 2B (Q4_K_M)"
MODELS["gemma4-qat-e2b"]="google/gemma-4-E2B-it-qat-q4_0-gguf|gemma-4-E2B-it-qat-q4_0.gguf|Gemma 4 E2B QAT (Q4_0) — Dense 2.3B, QAT quantized"
```

## 4. Add to run_cpu_benchmarks.sh and run_gpu_benchmarks.sh

Add the key to the `ALL_KEYS` array in **both** files.

## 5. Profile

```bash
bash run_cpu_benchmarks.sh <key>             # CPU thinking mode
bash run_cpu_benchmarks.sh --no-reasoning <key>  # CPU no-think mode
bash run_gpu_benchmarks.sh <key>             # GPU thinking mode
bash run_gpu_benchmarks.sh --no-reasoning <key>  # GPU no-think mode
```

Or manually per model:
```bash
./serve_cpu.sh <key>
# wait for server ready
uv run python scripts/profile_client.py --port 12345           # [out] only
uv run python scripts/profile_client.py --port 12345 --reasoning  # show [think] too
./stop.sh 12345
```

Results saved to `results/cpu/<key>_think.txt` / `results/cpu/<key>_nothink.txt` (CPU) and `results/gpu/` (GPU).

## 6. Update reports/cpu.md and reports/gpu.md

- Add row to the **Models Tested** table
- Add rows to all 4 result tables (TTFT, TPOT, Throughput, Wall Duration)
- Update the **Throughput Ranking** table
- Update **Key Findings** and **Recommendations** sections
