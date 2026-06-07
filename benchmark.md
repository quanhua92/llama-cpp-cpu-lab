# Benchmark Guide

Quick reference for running benchmarks. Extracted from README.md and add-model-flow.md.

## Rules

1. **One model at a time.** One step at a time. Never run benchmarks in parallel.
2. **Always use `nohup`.** Thinking models can take 5-10+ min per step.
3. **Wait for completion** before starting the next step.
4. **Monitor** with `tail -f` and `ls`.

## 3-Step Per-Model Flow

Every model gets 3 steps: think benchmark, nothink benchmark, examples. Pick CPU or GPU.

### GPU

```bash
# Step 1: Think benchmark
nohup bash run_gpu_benchmarks.sh <key> > /tmp/bench_gpu_think.log 2>&1 &
echo "Started: $!"

# Step 2: Nothink benchmark (after step 1 finishes)
nohup bash run_gpu_benchmarks.sh --no-reasoning <key> > /tmp/bench_gpu_nothink.log 2>&1 &
echo "Started: $!"

# Step 3: Examples (after step 2 finishes)
nohup ./generate_examples_gpu.sh <key> > /tmp/examples_gpu.log 2>&1 &
echo "Started: $!"
```

### CPU

```bash
# Step 1: Think benchmark
nohup bash run_cpu_benchmarks.sh <key> > /tmp/bench_cpu_think.log 2>&1 &
echo "Started: $!"

# Step 2: Nothink benchmark (after step 1 finishes)
nohup bash run_cpu_benchmarks.sh --no-reasoning <key> > /tmp/bench_cpu_nothink.log 2>&1 &
echo "Started: $!"

# Step 3: Examples (after step 2 finishes)
nohup ./generate_examples_cpu.sh <key> > /tmp/examples_cpu.log 2>&1 &
echo "Started: $!"
```

### Partial GPU Offload

For large models that don't fit in VRAM (>16 GB on 16 GB card):

```bash
nohup bash run_gpu_benchmarks.sh --ngl 40 <key> > /tmp/bench_gpu_think.log 2>&1 &
echo "Started: $!"

nohup ./generate_examples_gpu.sh --ngl 40 <key> > /tmp/examples_gpu.log 2>&1 &
echo "Started: $!"
```

### Monitor Progress

```bash
# Check process is alive
ps -p <PID> -o pid,cmd

# Check log tail
tail -20 /tmp/bench_gpu_think.log

# Check for failures in results
grep -c "Failed\." results/gpu/<key>_think.txt

# Check for timing data (means questions completed)
grep -c "timings" results/gpu/<key>_think.txt
```

**Do NOT use `ls | wc -l` alone** — it shows file count but not whether the process finished. Always pair with `ps -p <PID>`.

### Monitor Loop

When asked to monitor, keep checking every 60s until done or max ~15 min:

```bash
for i in 1 2 3; do
  ps -p <PID> -o pid,cmd 2>/dev/null || { echo "Process finished"; break; }
  count=$(ls results/gpu/*_nothink.txt 2>/dev/null | wc -l)
  echo "=== $(date +%H:%M:%S) === $count/6 done"
  tail -3 /tmp/bench_gpu_think.log
  sleep 60
done
```

If still running after 3 checks, immediately run the same loop again. Repeat until done. Never ask the user to say "check again".

Stops early if process finishes. If still running after 15 min, report status and stop. Adjust the number based on expected runtime.

### What You Get

```
results/<cpu|gpu>/<key>_think.txt       # 10 questions with thinking enabled
results/<cpu|gpu>/<key>_nothink.txt     # 10 questions with thinking disabled
results/<cpu|gpu>/<key>_think.json      # raw timing data (auto-saved)
results/<cpu|gpu>/<key>_nothink.json
examples/<cpu|gpu>/<key>_ask.md         # ask example output
examples/<cpu|gpu>/<key>_reflect.md     # reflect example output
examples/<cpu|gpu>/<key>_ask.json       # raw timing data (auto-saved)
examples/<cpu|gpu>/<key>_reflect.json
```

## Full Suite (All Models)

Same 3 steps but omit the `<key>` to run every model in `ALL_KEYS`. Each step can take hours.

```bash
# GPU think
nohup bash run_gpu_benchmarks.sh > /tmp/bench_gpu_think.log 2>&1 &
echo "Started: $!"

# GPU nothink (after think finishes)
nohup bash run_gpu_benchmarks.sh --no-reasoning > /tmp/bench_gpu_nothink.log 2>&1 &
echo "Started: $!"

# GPU examples (after nothink finishes)
nohup ./generate_examples_gpu.sh > /tmp/examples_gpu.log 2>&1 &
echo "Started: $!"
```

Monitor: `ls results/gpu/*.txt | wc -l`

## Stopping

```bash
# Stop everything (run separately, don't chain)
./stop.sh
```

## Analyze Results

```bash
uv run python scripts/analyze_results.py                          # all sections
uv run python scripts/analyze_results.py --section overview       # model rankings
uv run python scripts/analyze_results.py --section per-question  # per-Q breakdown
uv run python scripts/analyze_results.py --section comparison     # think vs nothink
uv run python scripts/analyze_results.py --section stability      # question variance
uv run python scripts/analyze_results.py --sort avg_decode_speed  # sort by decode speed
uv run python scripts/analyze_results.py --dir results/gpu       # analyze GPU results
```

## Metrics

| Metric | Source | Description |
|--------|--------|-------------|
| TTFT | Client | Time to first token (ms) |
| Decode Speed | Server | `predicted_per_second` — real generation throughput (tok/s) |
| Decode Time | Server | `predicted_per_token_ms` — ms per generated token |
| Prefill Time | Server | `prompt_ms` — time to process prompt tokens |
| Prefill Speed | Server | `prompt_per_second` — prompt tokens/sec |

All decode metrics come from llama.cpp server timings (not client chunk counting).

## Adding a New Model

1. Download GGUF to `models/`
2. Add key to `MODELS` dict in `serve_cpu.sh` and `serve_gpu.sh`
3. Add key to `ALL_KEYS` array in `run_cpu_benchmarks.sh` and `run_gpu_benchmarks.sh`
4. Run 3-step benchmark flow (above)
5. Update `reports/cpu.md` and `reports/gpu.md`

See `add-model-flow.md` for full details.
