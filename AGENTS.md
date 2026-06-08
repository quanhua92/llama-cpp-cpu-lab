# Project Rules

Mandatory rules for all agents working in this repository. These are non-negotiable.

## NEVER

1. **NEVER delete `results/` or `examples/` files without explicit user permission.** These are benchmark artifacts that take minutes to hours to generate. Deleting them wastes real time and GPU cycles. If you need to clean up, ASK FIRST.

2. **NEVER commit without being asked.** Only commit when the user explicitly says "commit".

3. **NEVER run benchmarks in parallel.** One model, one step at a time. The machine has limited CPU/GPU. Parallel runs distort results and risk OOM.

4. **NEVER chain `pkill`/`kill` with other commands in one shell invocation.** `pkill` can hang or match the wrong process. Run `pkill` as a separate command, verify it completed, then run the next command.

5. **NEVER use `tail -f` or long-running `while sleep` loops in bash.** These block the shell tool and cannot be interrupted cleanly.

6. **NEVER run a benchmark step without first confirming the previous step finished.** Check `ps -p <PID>` and the log before starting the next step.

7. **NEVER assume SCP transfers are complete.** Always check with `ls -la` before and after a delay, or `ps aux | grep scp`.

8. **NEVER use `rm -f` or `rm -rf` on result/example files.** If cleanup is needed, list what would be deleted and ask for confirmation.

9. **NEVER assume a benchmark step is done just because the file count hasn't changed.** A model may be mid-run. Check the process and log.

10. **NEVER use `ls *.txt | wc -l` as the only completion check.** It tells you file count but not whether the process finished. Always pair with `ps -p <PID>`.

## ALWAYS

1. **Always use `nohup` + `echo "Started: $!"` for benchmarks.** Thinking models take 5-10+ minutes per step. Shell sessions time out.

2. **Always pass `--output` flag to `profile_client.py`.** The benchmark runner scripts handle this — but if running manually, don't forget.

3. **Always save JSON alongside TXT/MD.** The scripts do this automatically. Don't disable it.

4. **Always verify syntax after editing shell scripts.** Run `bash -n <file>` before committing.

5. **Always verify syntax after editing Python scripts.** Run `python3 -c "import ast; ast.parse(open('<file>').read())"` or the project's linter.

6. **Always check for failed questions after benchmarks.** The benchmark scripts have post-run validation. Check the output for `FAIL:` lines.

7. **Always use server-side metrics (`predicted_per_second`).** Client-side TPOT is deprecated and removed from all scripts.

8. **Always match existing code style.** No comments unless asked. Mimic surrounding patterns.

9. **Always monitor benchmarks by checking BOTH the process AND the log, not just file count.**
   - Check process: `ps -p <PID> -o pid,cmd`
   - Check log tail: `tail -20 /tmp/bench_gpu_think.log`
   - Check for failures: `grep -c "Failed\." results/gpu/<key>_think.txt`
   - Check for timing data: `grep -c "timings" results/gpu/<key>_think.txt`
   - File count alone (`ls | wc -l`) is NOT sufficient to confirm completion.

10. **When user asks to monitor, check 3 times with 60s sleep. If still running, immediately start another round of 3 checks. Keep going until done. Never ask the user to say "check again".**
    ```bash
    for i in 1 2 3; do
      ps -p <PID> -o pid,cmd 2>/dev/null || { echo "Process finished"; break; }
      count=$(ls results/gpu/*_nothink.txt 2>/dev/null | wc -l)
      echo "=== $(date +%H:%M:%S) === $count/6 done"
      tail -3 /tmp/bench_gpu_think.log
      sleep 60
    done
    ```
    After the loop, if the process is still running, run the same loop again in a new tool call. Repeat until process finishes. Never stop and wait for the user to ask.
    This monitors for up to 15 minutes. Stops early if process finishes. If still running after 15 min, report status and stop. Adjust the number based on expected runtime.

## Project Context

- **Machine (GPU):** Intel i9-13900K, 64GB RAM, NVIDIA RTX 4060 Ti 16GB (Ada, SM 8.9)
- **Machine (CPU):** Intel i7-10700, 64GB RAM
- **llama.cpp:** `repo/build/bin/llama-server`
- **Models dir:** `models/` (or `LOCAL_LLM_MODELS` env var override)
- **Results dir:** `results/cpu/`, `results/gpu/`
- **Examples dir:** `examples/cpu/`, `examples/gpu/`

## Benchmark Flow (3 Steps Per Model)

```
Step 1: think benchmark    → results/<backend>/<key>_think.txt
Step 2: nothink benchmark → results/<backend>/<key>_nothink.txt
Step 3: examples          → examples/<backend>/<key>_ask.md + _reflect.md
```

Run one step at a time. Wait for completion. Each step uses `nohup`.

## Large Models (>16GB VRAM)

Use `--ngl N` for partial GPU offload:
```bash
./serve_gpu.sh qwen3.6-27b --ngl 40
bash run_gpu_benchmarks.sh --ngl 40 qwen3.6-27b
./generate_examples_gpu.sh --ngl 40 qwen3.6-27b
```

## Key Files

| File | Purpose |
|------|---------|
| `BENCHMARK.md` | Benchmarking quick reference |
| `ADD-MODEL-FLOW.md` | Guide for adding new models |
| `serve_gpu.sh` | GPU server launcher (`--ngl N` supported) |
| `serve_cpu.sh` | CPU server launcher |
| `run_gpu_benchmarks.sh` | GPU benchmark runner (has post-run validation) |
| `run_cpu_benchmarks.sh` | CPU benchmark runner (has post-run validation) |
| `generate_examples_gpu.sh` | GPU example generator (`--ngl N` supported) |
| `generate_examples_cpu.sh` | CPU example generator |
| `scripts/profile_client.py` | Benchmark client (server timings) |
| `scripts/analyze_results.py` | Result analyzer (decode speed, not TPOT) |
| `scripts/generate_examples.py` | Example generator script |

## Fact-Checking Guide

### Verifying Computed Results (Internal Data)

Whenever benchmarks are run (via `run_cpu_benchmarks.sh` or `run_gpu_benchmarks.sh`), raw json/txt logs are written to the `results/` directory. When creating or updating markdown tables (in `reports/cpu.md`, `reports/gpu.md`, `reports/gemma4-qat-comparison.md`, etc.), verify the metrics using these rules.

#### Automated Table Verification

To prevent human error and typos, always run the automated validator script:

```bash
python3 scripts/verify_reports.py
```

This script parses the markdown tables in all report files and compares every cell's values against the raw JSON outputs in `results/cpu` and `results/gpu` using the exact mathematical definitions below. It outputs `[PASS]` or `[FAIL]` indicators.

#### Mathematical Formulas for Metrics

If you must manually verify or calculate stats, use the exact calculations below:

- **Average TTFT (ms):** Arithmetic mean of `ttft_ms` across the 10 questions.
  $$\text{Avg TTFT} = \frac{1}{10} \sum_{i=1}^{10} \text{ttft\_ms}_i$$
- **Average Wall Duration (s):** Arithmetic mean of `total_time_s` across the 10 questions.
  $$\text{Avg Wall} = \frac{1}{10} \sum_{i=1}^{10} \text{total\_time\_s}_i$$
- **Average Decode Speed (tok/s):** Total predicted tokens divided by total predicted time. Do **NOT** average the per-question decode speeds.
  $$\text{Avg Decode} = \frac{\sum_{i=1}^{10} \text{predicted\_n}_i}{\sum_{i=1}^{10} \left( \frac{\text{predicted\_ms}_i}{1000} \right)}$$
- **Average Prompt Speed (tok/s):** Total prompt tokens divided by total prompt time. Do **NOT** average the per-question prompt speeds.
  $$\text{Avg Prompt} = \frac{\sum_{i=1}^{10} \text{prompt\_n}_i}{\sum_{i=1}^{10} \left( \frac{\text{prompt\_ms}_i}{1000} \right)}$$

#### Delta Percentages ($\Delta\%$)

When comparing two models or modes, compute the percentage difference using raw, unrounded numbers first, and then round the final percentage to the nearest integer:

$$\Delta\% = \text{round}\left( \frac{\text{New} - \text{Baseline}}{\text{Baseline}} \times 100 \right)$$

*Example:* If No-Think Wall is `8.183s` and Think Wall is `33.128s`:

$$\Delta\% = \text{round}\left( \frac{33.128 - 8.183}{8.183} \times 100 \right) = \text{round}(304.839\%) \rightarrow +305\%$$

#### Table Formatting Rules

- **Bolding:** Always bold the better performing model in each comparison row/cell.
  - *TTFT, TPOT, and Wall Duration:* Lower values are better. Bold the **lowest** value.
  - *Throughput / Speeds (tok/s):* Higher values are better. Bold the **highest** value.
- **Rankings:** Order rankings strictly by average Decode Speed in descending order. Ensure no adjacent entries are inverted.
- **Rounding Precision:**
  - Sizes on disk: Standardize to `GB` or `MB` with 1 decimal place (e.g., `14.4 GB` instead of `14 GB`).
  - Speeds: Standardize to 1 decimal place in lists/rankings (e.g., `11.9 tok/s`) and 2 decimal places in side-by-side comparison tables (e.g., `11.90 tok/s`).
  - TTFT: Standardize to nearest integer in milliseconds (e.g., `616 ms`).

### Fact-Checking External Model Information

When adding a new model to `serve_cpu.sh` and `serve_gpu.sh` under the `MODELS` associative array, you must fact-check and verify its specifications.

#### Key Metadata Attributes to Verify

1. **Architecture Type:**
   - *Dense:* All model parameters are computed for every token.
   - *MoE (Mixture of Experts):* Sparse computation where only a subset of parameters is active per token. Verify the expert routing mechanism (e.g., how many experts are routed vs shared).
2. **Parameter Counts:**
   - Verify **Total Parameters** (all weights) and **Active Parameters** per token for MoE models (e.g., Gemma 4 26B-A4B has 25.2B total / ~3.8B active; Qwen 3.6 35B-A3B has 35B total / ~3B active).
3. **Context Length:**
   - Verify the native context window supported by the model base (e.g., 256K for Gemma 4 26B-A4B, 262K for Qwen 3.6).
4. **Multimodality:**
   - Verify what modalities the model officially supports natively (e.g., text-only, vision-language, audio input), even if our deployed GGUF is currently run text-only in `llama.cpp`. Note unified/encoder-free designs (e.g., Gemma 4 12B).
5. **Quantization Method:**
   - **PTQ (Post-Training Quantization):** Standard quants like `Q4_K_M`, `Q8_0`.
   - **QAT (Quantization-Aware Training):** Models trained with quantization target active (usually Google's `Q4_0` QAT files). QAT models offer higher quality at comparable file sizes.

#### Standard Web Search Templates

Use these queries on Hugging Face or search engines to pull official model details:

- **For parameter counts & MoE routing:**
  `"<Model Name>" "total parameters" OR "active parameters" OR "experts"`
- **For context lengths:**
  `"<Model Name>" "context window" OR "context length" OR "RoPE"`
- **For architectural details:**
  `"<Model Name>" "architecture" OR "encoder-free" OR "multimodal"`
- **For quantization details:**
  `"<Model Name>" GGUF "<Quantization>" OR "QAT"`

### Example Output Verification

Example captures are stored in `examples/cpu/` and `examples/gpu/`.

1. Verify that the metadata block at the bottom of the example markdown file (e.g., `TTFT: 928ms | 10.6 tok/s | 169.0s total (1775 tokens)`) matches the details cited in the comparison reports exactly.
2. Ensure that the persona claims (e.g., "professional chef persona", "literary tone") and fluency evaluations match the actual text generated in the example files.

### Verifying Qualitative & Comparative Claims ("Best", "Top", "Similar")

When writing or reviewing summaries that make qualitative claims or compare model characteristics, use the following rules to verify that they are factual.

#### "Best" or "Top" Claims

- **Performance Bests:** Statements declaring a model as "top" or "best" in speed must correspond directly to its rank in our benchmark reports.
- **Capabilities Bests:** Statements declaring a model "best" for a specific category must be sourced from widely accepted public benchmarks (such as Hugging Face Open LLM Leaderboard v2) or detailed evaluation publications.
- **Tone:** Avoid marketing hype or absolute phrases. Use objective, qualified phrasing (e.g., "consistently ranks top in its parameter class").

#### "Similar" Claims

- **Similar Active Parameters / Size:** Claims that two models are "similar in size" or have "similar active parameters" must be supported by the parameter counts. A difference of less than 20% in active parameters qualifies as "similar active parameters".
- **Similar Speed / Throughput:** Claims that two models have "similar speed" must be verified against our benchmark tables. The average decode speeds must be within a 15% margin to be described as similar.
- **Similar Architecture:** Claims that two models have "similar architecture" must be checked for key structural patterns (e.g., both are MoE models using standard top-8 expert routing, or both are dense models using GQA).

### Checklists for Files to Update

When modifying benchmarks, the following files must remain consistent:

- [ ] **Model Lists:** Check that the model exists in the `MODELS` lists in both `serve_cpu.sh` and `serve_gpu.sh`.
- [ ] **Model Key / Names:** Ensure the names match the directories and GGUF files perfectly.
- [ ] **CPU Rankings:** Update `reports/cpu.md` using the output of `analyze_results.py`.
- [ ] **GPU Rankings:** Update `reports/gpu.md` using the output of `analyze_results.py`.
- [ ] **Model Description in README:** Update `README.md`'s "Curated Models" table with accurate parameter counts, architectural summaries, and file sizes.
- [ ] **Run Verification:** Run `python3 scripts/verify_reports.py` and verify all tests pass.
