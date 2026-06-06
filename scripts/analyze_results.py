#!/usr/bin/env python3
import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

PROMPTS = {
    "Q01": "software architecture",
    "Q02": "neural networks learn",
    "Q03": "TCP vs UDP",
    "Q04": "garbage collection Python",
    "Q05": "microservices",
    "Q06": "closure in programming",
    "Q07": "CAP theorem",
    "Q08": "DNS resolution",
    "Q09": "design patterns",
    "Q10": "database transactions",
}

METRIC_RE = re.compile(
    r"\[(Q\d{2})\]\s+TTFT=([\d.]+)ms\s+TPOT=([\d.]+)ms\s+Chunks=(\d+)\s+Total=([\d.]+)s"
)

FAILED_RE = re.compile(r"Failed\.")


def parse_result_file(filepath: Path) -> dict:
    data = {"model": None, "questions": {}, "failed": []}
    text = filepath.read_text(errors="replace")

    stem = filepath.stem
    if "_think" in stem:
        data["mode"] = "think"
    elif "_nothink" in stem:
        data["mode"] = "nothink"
    else:
        data["mode"] = "unknown"

    data["model"] = stem.replace("_think", "").replace("_nothink", "")

    for m in METRIC_RE.finditer(text):
        qid = m.group(1)
        data["questions"][qid] = {
            "ttft_ms": float(m.group(2)),
            "tpot_ms": float(m.group(3)),
            "chunks": int(m.group(4)),
            "total_s": float(m.group(5)),
        }

    return data


def load_all_results(results_dir: Path) -> list[dict]:
    results = []
    for f in sorted(results_dir.glob("*.txt")):
        if f.name == "summary.txt":
            continue
        parsed = parse_result_file(f)
        results.append(parsed)
    return results


def print_overview_table(results: list[dict], sort_by: str = "avg_tpot"):
    modes = sorted(set(r["mode"] for r in results))

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Overview: {mode} mode ===[/bold cyan]")

        table = Table(
            title=f"Model Performance ({mode})",
            show_lines=True,
            title_style="bold",
        )
        table.add_column("Model", style="bold", min_width=18)
        table.add_column("Questions", justify="right")
        table.add_column("Avg TTFT", justify="right")
        table.add_column("Avg TPOT", justify="right")
        table.add_column("Avg T/s", justify="right", style="green bold")
        table.add_column("Avg Total", justify="right")

        rows = []
        for r in mode_results:
            qs = r["questions"]
            if not qs:
                continue
            n = len(qs)
            avg_ttft = sum(v["ttft_ms"] for v in qs.values()) / n
            avg_tpot = sum(v["tpot_ms"] for v in qs.values()) / n
            avg_total = sum(v["total_s"] for v in qs.values()) / n
            avg_tps = 1000 / avg_tpot if avg_tpot > 0 else 0
            rows.append((r["model"], n, avg_ttft, avg_tpot, avg_tps, avg_total))

        sort_idx = {"avg_ttft": 2, "avg_tpot": 3, "avg_tps": 4, "avg_total": 5}[sort_by]
        reverse = sort_by in ("avg_tps",)
        rows.sort(key=lambda x: x[sort_idx], reverse=reverse)

        for model, n, avg_ttft, avg_tpot, avg_tps, avg_total in rows:
            table.add_row(
                model,
                str(n),
                f"{avg_ttft:,.1f}",
                f"{avg_tpot:,.1f}",
                f"{avg_tps:,.2f}",
                f"{avg_total:,.1f}",
            )

        console.print(table)


def print_per_question_tables(results: list[dict], sort_by: str = "tpot_ms"):
    modes = sorted(set(r["mode"] for r in results))
    all_qids = [f"Q{i:02d}" for i in range(1, 11)]

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Per-Question: {mode} mode ===[/bold cyan]")

        for qid in all_qids:
            label = PROMPTS.get(qid, qid)
            console.print(f"\n[bold]{qid}: {label}[/bold]")

            table = Table(show_lines=True)
            table.add_column("Model", style="bold", min_width=18)
            table.add_column("TTFT (ms)", justify="right")
            table.add_column("TPOT (ms)", justify="right")
            table.add_column("T/s", justify="right", style="green bold")
            table.add_column("Chunks", justify="right")
            table.add_column("Total (s)", justify="right")

            rows = []
            for r in mode_results:
                if qid in r["questions"]:
                    q = r["questions"][qid]
                    tps = 1000 / q["tpot_ms"] if q["tpot_ms"] > 0 else 0
                    rows.append((
                        r["model"],
                        q["ttft_ms"],
                        q["tpot_ms"],
                        tps,
                        q["chunks"],
                        q["total_s"],
                    ))

            per_key = {"avg_ttft": "ttft_ms", "avg_tpot": "tpot_ms", "avg_tps": "tps", "avg_total": "total_s",
                       "ttft_ms": "ttft_ms", "tpot_ms": "tpot_ms", "tps": "tps", "chunks": "chunks", "total_s": "total_s"}
            sort_key = per_key.get(sort_by, "tpot_ms")
            sort_idx = {"ttft_ms": 1, "tpot_ms": 2, "tps": 3, "chunks": 4, "total_s": 5}[sort_key]
            reverse = sort_by == 3
            rows.sort(key=lambda x: x[sort_idx], reverse=reverse)

            for model, ttft, tpot, tps, chunks, total in rows:
                table.add_row(
                    model,
                    f"{ttft:,.1f}",
                    f"{tpot:,.1f}",
                    f"{tps:,.2f}",
                    str(chunks),
                    f"{total:,.1f}",
                )

            console.print(table)


def print_comparison_table(results: list[dict]):
    think = {r["model"]: r for r in results if r["mode"] == "think"}
    nothink = {r["model"]: r for r in results if r["mode"] == "nothink"}
    common = sorted(set(think.keys()) & set(nothink.keys()))

    if not common:
        console.print("[yellow]No models have both think and nothink results.[/yellow]")
        return

    console.print(f"\n[bold cyan]=== Think vs No-Think Comparison ===[/bold cyan]")

    table = Table(show_lines=True, title="Think vs No-Think Overhead")
    table.add_column("Model", style="bold", min_width=18)
    table.add_column("Think TTFT", justify="right")
    table.add_column("NoThink TTFT", justify="right")
    table.add_column("Think TPOT", justify="right")
    table.add_column("NoThink TPOT", justify="right")
    table.add_column("Think T/s", justify="right", style="green")
    table.add_column("NoThink T/s", justify="right", style="green")
    table.add_column("TTFT Δ%", justify="right")
    table.add_column("TPOT Δ%", justify="right")

    rows = []
    for model in common:
        t_qs = think[model]["questions"]
        nt_qs = nothink[model]["questions"]
        n_t = len(t_qs)
        n_nt = len(nt_qs)
        if n_t == 0 or n_nt == 0:
            continue

        t_ttft = sum(v["ttft_ms"] for v in t_qs.values()) / n_t
        nt_ttft = sum(v["ttft_ms"] for v in nt_qs.values()) / n_nt
        t_tpot = sum(v["tpot_ms"] for v in t_qs.values()) / n_t
        nt_tpot = sum(v["tpot_ms"] for v in nt_qs.values()) / n_nt
        t_tps = 1000 / t_tpot if t_tpot > 0 else 0
        nt_tps = 1000 / nt_tpot if nt_tpot > 0 else 0
        ttft_delta = ((t_ttft - nt_ttft) / nt_ttft * 100) if nt_ttft > 0 else 0
        tpot_delta = ((t_tpot - nt_tpot) / nt_tpot * 100) if nt_tpot > 0 else 0

        rows.append((
            model, t_ttft, nt_ttft, t_tpot, nt_tpot, t_tps, nt_tps,
            ttft_delta, tpot_delta,
        ))

    rows.sort(key=lambda x: x[7])

    for model, t_ttft, nt_ttft, t_tpot, nt_tpot, t_tps, nt_tps, ttft_d, tpot_d in rows:
        table.add_row(
            model,
            f"{t_ttft:,.1f}",
            f"{nt_ttft:,.1f}",
            f"{t_tpot:,.1f}",
            f"{nt_tpot:,.1f}",
            f"{t_tps:,.2f}",
            f"{nt_tps:,.2f}",
            f"{ttft_d:+.1f}%",
            f"{tpot_d:+.1f}%",
        )

    console.print(table)


def print_question_stability(results: list[dict]):
    modes = sorted(set(r["mode"] for r in results))
    all_qids = [f"Q{i:02d}" for i in range(1, 11)]

    for mode in modes:
        mode_results = [r for r in results if r["mode"] == mode]
        console.print(f"\n[bold cyan]=== Question Variance: {mode} mode ===[/bold cyan]")
        console.print("(std dev across models — lower = more consistent across models)\n")

        table = Table(show_lines=True)
        table.add_column("Question", style="bold", min_width=10)
        table.add_column("Topic", min_width=22)
        table.add_column("Mean TTFT", justify="right")
        table.add_column("Std TTFT", justify="right")
        table.add_column("Mean TPOT", justify="right")
        table.add_column("Std TPOT", justify="right")

        for qid in all_qids:
            ttfts, tpots = [], []
            for r in mode_results:
                if qid in r["questions"]:
                    ttfts.append(r["questions"][qid]["ttft_ms"])
                    tpots.append(r["questions"][qid]["tpot_ms"])

            if not ttfts:
                continue

            import statistics
            n = len(ttfts)
            mean_ttft = sum(ttfts) / n
            mean_tpot = sum(tpots) / n
            std_ttft = statistics.stdev(ttfts) if n > 1 else 0
            std_tpot = statistics.stdev(tpots) if n > 1 else 0

            table.add_row(
                qid,
                PROMPTS.get(qid, ""),
                f"{mean_ttft:,.1f}",
                f"{std_ttft:,.1f}",
                f"{mean_tpot:,.1f}",
                f"{std_tpot:,.1f}",
            )

        console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Analyze CPU benchmark results")
    parser.add_argument(
        "--dir", type=str, default="results/cpu",
        help="Results directory (default: results/cpu)",
    )
    parser.add_argument(
        "--sort", type=str, default="avg_tpot",
        choices=["avg_ttft", "avg_tpot", "avg_tps", "avg_total", "ttft_ms", "tpot_ms", "tps"],
        help="Sort metric (default: avg_tpot)",
    )
    parser.add_argument(
        "--section", type=str, default="all",
        choices=["all", "overview", "per-question", "comparison", "stability"],
        help="Which sections to show (default: all)",
    )
    args = parser.parse_args()

    results_dir = Path(args.dir)
    if not results_dir.exists():
        console.print(f"[red]Directory not found: {results_dir}[/red]")
        sys.exit(1)

    results = load_all_results(results_dir)
    if not results:
        console.print("[red]No result files found.[/red]")
        sys.exit(1)

    console.print(f"[bold]Loaded {len(results)} result files from {results_dir}[/bold]")
    models = sorted(set(r["model"] for r in results))
    console.print(f"Models: {', '.join(models)}\n")

    section = args.section

    if section in ("all", "overview"):
        print_overview_table(results, sort_by=args.sort)

    if section in ("all", "per-question"):
        print_per_question_tables(results, sort_by=args.sort)

    if section in ("all", "comparison"):
        print_comparison_table(results)

    if section in ("all", "stability"):
        print_question_stability(results)


if __name__ == "__main__":
    main()
