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

## 5. Profile + Examples

For each backend you want to test (CPU or GPU), run all three steps. **Prefer `nohup` to avoid shell timeout — especially for thinking models which can run for 5-10+ minutes per step.**

```bash
# GPU example: <key>
nohup bash run_gpu_benchmarks.sh <key> > /tmp/bench_gpu_think.log 2>&1 &
nohup bash run_gpu_benchmarks.sh --no-reasoning <key> > /tmp/bench_gpu_nothink.log 2>&1 &
nohup ./generate_examples_gpu.sh <key> > /tmp/examples_gpu.log 2>&1 &

# CPU example: <key>
nohup bash run_cpu_benchmarks.sh <key> > /tmp/bench_cpu_think.log 2>&1 &
nohup bash run_cpu_benchmarks.sh --no-reasoning <key> > /tmp/bench_cpu_nothink.log 2>&1 &
nohup ./generate_examples_cpu.sh <key> > /tmp/examples_cpu.log 2>&1 &
```

> **Important: Run only one step at a time.** Wait for the previous step to fully complete before starting the next. Monitor progress with:
> ```bash
> tail -f /tmp/bench_gpu_think.log
> ls results/gpu/<key>*.txt    # check which results exist
> ```

Results:
- `results/<cpu|gpu>/<key>_think.txt` / `results/<cpu|gpu>/<key>_nothink.txt`
- `examples/<cpu|gpu>/<key>_ask.md` / `examples/<cpu|gpu>/<key>_reflect.md`

## 6. Update reports/cpu.md and reports/gpu.md

- Add the model's stats (Decode speed and Prompt speed) to the **Nothink Mode** and **Think Mode** ranking tables in the appropriate positions based on its decode speed rank.
- Update the **Key Observations** and **Notes** sections with any noteworthy performance, size, or offload insights.
