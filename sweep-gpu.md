# GPU Config Sweep

Systematically test `llama-server` flag combinations to find optimal settings for your GPU. Uses a 2-phase approach with real long prompts.

## Corpus

Long prompts use a Project Gutenberg text as filler. Downloaded to `tuning/corpus.txt`:

```bash
wget -O tuning/corpus.txt https://www.gutenberg.org/files/1661/1661-0.txt
```

Default: *The Adventures of Sherlock Holmes* by Arthur Conan Doyle (607 KB, ~150K tokens). Replace with any large plain text file if preferred.

## 2 Phases

### Phase 1: Speed Tuning (threads x spec)

Find the best CPU threads and speculative decoding setting. Short prompt ("2+2"), ngl=99, ctx=8192. Only 6 combos, ~2 min.

| Dimension | Values |
|-----------|--------|
| `-t N` | 8, 16, 24 |
| `--spec-type` | none, ngram-simple |

Picks the best threads + spec for tok/s. These carry into phase 2.

### Phase 2: Context + GPU Offload + KV Quant Scaling (long prompts)

Find the highest ngl that fits for each ctx size, with and without KV cache quantization. Uses **real long prompts** filling 80% of the context window.

| Dimension | Values |
|-----------|--------|
| `-ngl N` | 99, 60, 40, 20 |
| `-c N` | 8192, 32768, 65536 |
| KV quant | q8 (`-ctk q8_0 -ctv q8_0`, default for GPU) |

12 combos, each takes minutes (long prompt). This is the main phase — measures real TTFT and tok/s under load, and finds the VRAM boundary with actual context usage. KV quant (`q8`) halves KV cache VRAM with almost zero quality loss, enabling larger contexts on GPU.

Output includes a recommendation: highest ngl per ctx that fits.

**Total: ~18 combos.** Phase 1 is fast (~2 min). Phase 2 depends on context sizes tested.

## Running

No other llama-server should be on the GPU — the script checks via `nvidia-smi` and aborts if occupied.

Stop the GPU service first, then run each command in a **separate terminal** (don't chain with `&&`):

```bash
# Step 1: Stop GPU service (if running)
systemctl --user stop llama-gpu.service
```

```bash
# Step 2: Verify GPU is free
nvidia-smi
```

You should see no llama-server under Processes.

```bash
# Step 3: Start the sweep
nohup ./sweep_gpu_config.sh > /tmp/sweep.log 2>&1 &
echo "Started: $!"
```

```bash
# Step 4: Monitor progress (separate command, run multiple times)
cat /tmp/sweep.log
```

```bash
# Or monitor the sweep.log inside the results folder
cat tuning/gpu/<model>/<timestamp>/sweep.log
```

### Stopping the sweep

Use `pkill -9` — regular `pkill` hangs because the script tries to stop the server subprocess:

```bash
pkill -9 -f "sweep_gpu_config"
```

Then clean up any leftover server:

```bash
./stop.sh 8100
```

## Results

```
tuning/gpu/<model>/<timestamp>/
  summary.md                           ← phase 1 + 2 tables + recommendation
  sweep.log                            ← timestamped log
  p1_t8_specnone.txt                   ← phase 1 raw output
  p2_ngl99_ctx8192.txt                 ← phase 2 raw output
  p2_ngl99_ctx8192_prompt.txt          ← phase 2 long prompt used
  ...
```

The `summary.md` has 2 sections:

**Phase 1:** Speed tuning table

| threads | spec | TTFT (ms) | tok/s |
|---------|------|-----------|-------|
| 8 | none | 90 | 88.4 |
| 8 | ngram-simple | 85 | 95.2 |

**Phase 2:** Context + GPU offload + KV quant scaling table

| ngl | ctx | kv | est tokens | TTFT (ms) | tok/s | status |
|-----|-----|----|------------|-----------|-------|--------|
| 99 | 8192 | none | ~1638 | 90 | 88.0 | FIT |
| 99 | 65536 | none | ~13107 | - | - | OOM |
| 99 | 65536 | q8 | ~13107 | 450 | 85.2 | FIT |

**Recommendation:** highest ngl per ctx that fits, including whether KV quant is needed. Uses the best threads/spec from phase 1.

## Editing Sweep Values

Open `sweep_gpu_config.sh` and change the arrays at the top:

```bash
NGL_VALUES=(99 80 60)          # GPU layers to test
CTX_VALUES=(4096 8192 16384 32768 65536)  # context sizes
T_VALUES=(8 24)                # CPU threads
SPEC_VALUES=("none" "ngram-simple")       # speculative decoding
KV_QUANT_VALUES=("q8")              # KV cache quantization (q8 is default for GPU)
CTX_FILL=0.80                  # how much of ctx to fill with corpus (0.5-0.9)
```
