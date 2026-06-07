# Examples

Per-model example outputs for debugging and quality comparison.

## Structure

- `cpu/` — Per-model outputs generated on CPU (i7-10700)
- `gpu/` — Per-model outputs generated on GPU

## Output files

Each model produces:
- `{model}_ask.md` / `{model}_ask.json` — single prompt response
- `{model}_reflect.md` / `{model}_reflect.json` — reflection agent (generate → critique → revise)

The `.md` files contain `[think]` reasoning, `[out]` answer, `[timings]` server metrics, and summary.
The `.json` files contain the raw server timing data for re-analysis.

### Timings format

Each `.md` file includes `[timings]` lines with real metrics from the llama.cpp server:

```
[timings] prompt_n=35, prompt_ms=5.6, prompt_per_token_ms=0.16, prompt_per_second=6242, predicted_n=16, predicted_ms=36.4, predicted_per_token_ms=2.27, predicted_per_second=440
```

| Field | Meaning |
|-------|---------|
| `prompt_n` | Number of prompt tokens |
| `prompt_ms` | Time to process prompt (prefill) |
| `prompt_per_token_ms` | ms per prompt token |
| `prompt_per_second` | prompt tokens/sec (prefill speed) |
| `predicted_n` | Number of generated tokens |
| `predicted_ms` | Total generation time |
| `predicted_per_token_ms` | ms per generated token (decode time) |
| `predicted_per_second` | tokens/sec (decode speed) |

## Generating

```bash
# All models (CPU)
./generate_examples_cpu.sh

# Single model
./generate_examples_cpu.sh gemma4-qat-26b-a4b

# Only ask or only reflect
./generate_examples_cpu.sh --prompts ask
./generate_examples_cpu.sh --prompts reflect

# Custom question (saves as _custom.md, or --name to pick suffix)
./generate_examples_cpu.sh --question "explain quantum computing in Vietnamese"
./generate_examples_cpu.sh --question "explain recursion" --name recursion

# No-think mode (faster, no reasoning)
./generate_examples_cpu.sh --no-reasoning

# Skip already-generated files
./generate_examples_cpu.sh --skip-existing

# Large models (12B+) take 10-20 min per prompt. Use nohup to avoid timeout:
nohup ./generate_examples_cpu.sh gemma4-qat-12b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-26b-a4b > /tmp/examples.log 2>&1 &
nohup ./generate_examples_cpu.sh gemma4-qat-31b > /tmp/examples.log 2>&1 &

# GPU
nohup ./generate_examples_gpu.sh > /tmp/examples_gpu.log 2>&1 &
tail -f /tmp/examples_gpu.log
ls examples/gpu/*.md | wc -l  # count completed files
```
