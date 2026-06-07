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
| `benchmark.md` | Benchmarking quick reference |
| `add-model-flow.md` | Guide for adding new models |
| `serve_gpu.sh` | GPU server launcher (`--ngl N` supported) |
| `serve_cpu.sh` | CPU server launcher |
| `run_gpu_benchmarks.sh` | GPU benchmark runner (has post-run validation) |
| `run_cpu_benchmarks.sh` | CPU benchmark runner (has post-run validation) |
| `generate_examples_gpu.sh` | GPU example generator (`--ngl N` supported) |
| `generate_examples_cpu.sh` | CPU example generator |
| `scripts/profile_client.py` | Benchmark client (server timings) |
| `scripts/analyze_results.py` | Result analyzer (decode speed, not TPOT) |
| `scripts/generate_examples.py` | Example generator script |
