# reflect.py
import argparse
import asyncio
import json
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8888, help="Server port (default: 8888)")
parser.add_argument("--max-tokens", type=int, default=8192, help="Max tokens per step (default: 8192)")
parser.add_argument("task", nargs="?", default="Write a Python function that calculates fibonacci numbers efficiently",
                    help="Task for the reflection agent (default: fibonacci)")
args = parser.parse_args()

API_BASE = f"http://localhost:{args.port}/v1"
API_URL = f"{API_BASE}/chat/completions"
MODELS_URL = f"{API_BASE}/models"


async def call_llm_streaming(client: httpx.AsyncClient, prompt: str, max_tokens: int = 8192):
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }

    start_time = time.perf_counter()
    ttft = None
    completion_tokens = 0
    thinking = ""
    response = ""
    printed_thinking_header = False
    printed_response_header = False

    try:
        async with client.stream(
            "POST", API_URL, json=payload, timeout=120.0
        ) as response_stream:
            if response_stream.status_code != 200:
                print(f"Server Error: {response_stream.status_code}")
                return None, None, None

            async for chunk in response_stream.aiter_lines():
                if not chunk.strip():
                    continue
                if ttft is None:
                    ttft = time.perf_counter() - start_time
                if chunk.startswith("data: ") and chunk != "data: [DONE]":
                    try:
                        data = json.loads(chunk[6:])
                        timings = data.get("timings", {})
                        if timings:
                            completion_tokens = timings.get("predicted_n", completion_tokens)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning_content", "")
                        if reasoning:
                            if not printed_thinking_header:
                                print(f"\n     {'[think]':>8} ", end="", flush=True)
                                printed_thinking_header = True
                            print(reasoning, end="", flush=True)
                            thinking += reasoning
                        if content:
                            if not printed_response_header:
                                print(f"\n     {'[out]':>8} ", end="", flush=True)
                                printed_response_header = True
                            print(content, end="", flush=True)
                            response += content
                    except Exception:
                        pass

        total_duration = time.perf_counter() - start_time
        gen_time = total_duration - ttft if ttft else total_duration
        tok_per_sec = completion_tokens / gen_time if gen_time > 0 else 0

        return {
            "ttft_ms": ttft * 1000 if ttft else 0,
            "total_time_s": total_duration,
            "tok_per_sec": tok_per_sec,
            "completion_tokens": completion_tokens,
            "thinking": thinking,
            "response": response,
        }, thinking, response
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None, None


async def fetch_model_name(client: httpx.AsyncClient) -> str:
    try:
        resp = await client.get(MODELS_URL, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            if models:
                return models[0].get("id", "unknown")
    except Exception:
        pass
    return "unknown"


async def reflection_workflow(client: httpx.AsyncClient, task: str):
    print(f"\n{'='*60}")
    print(f"Reflection Task: {task}")
    print(f"{'='*60}")
    
    print("\n\n[STEP 1] Initial Generation")
    print("-" * 40)
    result1, _, draft = await call_llm_streaming(client, task, max_tokens=args.max_tokens)
    if not result1:
        print("Failed to generate initial response")
        return
    
    print(f"\n\n[STEP 2] Self-Critique")
    print("-" * 40)
    critique_prompt = f"""Critique this response to the task: "{task}"

Response:
{draft}

Provide specific, actionable feedback on:
1. Clarity and coherence
2. Completeness 
3. Accuracy
4. Structure
5. Areas for improvement

Be concise but thorough."""
    
    result2, _, critique = await call_llm_streaming(client, critique_prompt, max_tokens=args.max_tokens)
    if not result2:
        print("Failed to generate critique")
        return
    
    print(f"\n\n[STEP 3] Revision")
    print("-" * 40)
    revision_prompt = f"""Original Task: {task}

Original Response:
{draft}

Critique:
{critique}

Revise the original response incorporating the critique feedback. Improve clarity, completeness, and accuracy while maintaining the core message."""
    
    result3, _, final = await call_llm_streaming(client, revision_prompt, max_tokens=args.max_tokens)
    if not result3:
        print("Failed to generate revision")
        return
    
    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    print(final)
    
    total_time = result1['total_time_s'] + result2['total_time_s'] + result3['total_time_s']
    total_tokens = result1['completion_tokens'] + result2['completion_tokens'] + result3['completion_tokens']
    avg_tps = (result1['tok_per_sec'] + result2['tok_per_sec'] + result3['tok_per_sec']) / 3
    
    print(f"\nPerformance Summary:")
    print(f"Total time: {total_time:.1f}s")
    print(f"Total tokens: {total_tokens}")
    print(f"Avg throughput: {avg_tps:.1f} tok/s")


async def main():
    async with httpx.AsyncClient() as client:
        model_name = await fetch_model_name(client)
        print(f"Model: {model_name}")
        
        await reflection_workflow(client, args.task)


if __name__ == "__main__":
    asyncio.run(main())
