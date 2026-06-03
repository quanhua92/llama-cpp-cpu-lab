# Adding a New Model — Step-by-Step Flow

## 1. Find the GGUF File

Pick a small model from HuggingFace. Look for repos with "GGUF" in the name and a `Q4_K_M.gguf` file.

Check file list at:
```
https://huggingface.co/<org>/<repo>/tree/main
```

## 2. Download

```bash
cd /home/quan/llama-cpp/models
wget -c -O <filename>.gguf "https://huggingface.co/<org>/<repo>/resolve/main/<filename>.gguf"
```

## 3. Add to serve.sh

Edit `/home/quan/llama-cpp/serve.sh` — add a line in the `MODELS` dict:

```bash
MODELS["<key>"]="<org>/<repo>|<filename>.gguf|<display description>"
```

Example:
```bash
MODELS["qwen3.5-2b"]="unsloth/Qwen3.5-2B-GGUF|Qwen3.5-2B-Q4_K_M.gguf|Qwen3.5 2B (Q4_K_M)"
```

## 4. Profile

Edit `/home/quan/llama-cpp/run_benchmarks.sh` — add key to the `MODEL_KEYS` array, then:

```bash
bash run_benchmarks.sh
```

Or manually per model:
```bash
./serve.sh <key>
# wait for "all slots are idle" in server.log
uv run python profile_client.py          # [out] only
uv run python profile_client.py --reasoning  # show [think] too
./stop.sh
```

## 5. Update report.md

Add the results to the **Summary Table** (sorted by size/TTFT ascending) and add a **Detailed Results** section with per-iteration TTFT and assessment notes.
