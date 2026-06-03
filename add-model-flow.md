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

Or `serve.sh` will auto-download via `wget` on first run (can be slow).

## 3. Add to serve.sh

Add a line in the `MODELS` dict:

```bash
MODELS["<key>"]="<org>/<repo>|<filename>.gguf|<display description>"
```

Example:
```bash
MODELS["qwen3.5-2b"]="unsloth/Qwen3.5-2B-GGUF|Qwen3.5-2B-Q4_K_M.gguf|Qwen3.5 2B (Q4_K_M)"
```

## 4. Add to run_benchmarks.sh

Add the key to the `ALL_KEYS` array.

## 5. Profile

```bash
bash run_benchmarks.sh <key>             # thinking mode
bash run_benchmarks.sh --no-reasoning <key>  # no-think mode
```

Or manually per model:
```bash
./serve.sh <key>
# wait for server ready
uv run python profile_client.py --port 12345           # [out] only
uv run python profile_client.py --port 12345 --reasoning  # show [think] too
./stop.sh 12345
```

Results saved to `results/<key>_think.txt` and `results/<key>_nothink.txt`.

## 6. Update report.md

- Add row to the **Models Tested** table
- Add rows to all 4 result tables (TTFT, TPOT, Throughput, Wall Duration)
- Update the **Throughput Ranking** table
- Update **Key Findings** and **Recommendations** sections
