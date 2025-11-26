#!/usr/bin/env python3
"""
Analyze CAGRA benchmark results and generate summary report.
Usage: python analyze_cagra_results.py <results_dir>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def parse_benchmark_result(json_file: Path) -> Dict:
    """Parse a single benchmark JSON result file."""
    with open(json_file, 'r') as f:
        data = json.load(f)

    if 'benchmarks' not in data or len(data['benchmarks']) == 0:
        return None

    # Get the first benchmark result
    bench = data['benchmarks'][0]

    # Extract metrics
    result = {
        'name': bench.get('name', ''),
        'threads': bench.get('threads', 1),
        'iterations': bench.get('iterations', 0),
        'real_time': bench.get('real_time', 0),
        'cpu_time': bench.get('cpu_time', 0),
        'time_unit': bench.get('time_unit', 'ms'),
    }

    # Extract custom counters
    if 'counters' in bench:
        counters = bench['counters']
        result['recall'] = counters.get('Recall', 0.0)
        result['qps'] = counters.get('items_per_second', 0.0)
        result['total_queries'] = counters.get('total_queries', 0)
        result['latency'] = counters.get('Latency', 0.0)
        result['end_to_end'] = counters.get('end_to_end', 0.0)

        # Search parameters
        result['itopk'] = counters.get('itopk', 0)
        result['search_width'] = counters.get('search_width', 0)
        result['refine_ratio'] = counters.get('refine_ratio', 0.0)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_cagra_results.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)

    # Find all result JSON files
    result_files = sorted(results_dir.glob("search_concurrency_*.json"))

    if not result_files:
        print(f"Error: No result files found in {results_dir}")
        sys.exit(1)

    print("=" * 80)
    print("CAGRA Benchmark Results Summary")
    print("=" * 80)
    print()

    # Parse all results
    results = []
    for json_file in result_files:
        result = parse_benchmark_result(json_file)
        if result:
            results.append(result)

    if not results:
        print("Error: No valid results found")
        sys.exit(1)

    # Sort by concurrency (threads)
    results.sort(key=lambda x: x['threads'])

    # Print table header
    print(f"{'Concurrency':>12} {'QPS':>12} {'Recall':>10} {'Latency(ms)':>15} {'Total Queries':>15}")
    print("-" * 80)

    # Print results
    for r in results:
        concurrency = r['threads']
        qps = r.get('qps', 0.0)
        recall = r.get('recall', 0.0)
        latency = r.get('latency', 0.0)
        total_queries = r.get('total_queries', 0)

        print(f"{concurrency:>12} {qps:>12.2f} {recall:>10.4f} {latency:>15.3f} {total_queries:>15}")

    print()
    print("=" * 80)
    print("Search Parameters:")
    if results:
        r = results[0]
        print(f"  k: 10")
        print(f"  itopk_size: {r.get('itopk', 'N/A')}")
        print(f"  search_width: {r.get('search_width', 'N/A')}")
        print(f"  refine_ratio: {r.get('refine_ratio', 'N/A')}")
    print()

    # Save summary to CSV
    csv_file = results_dir / "summary.csv"
    with open(csv_file, 'w') as f:
        f.write("Concurrency,QPS,Recall,Latency_ms,Total_Queries\n")
        for r in results:
            f.write(f"{r['threads']},{r.get('qps', 0.0):.2f},{r.get('recall', 0.0):.4f},"
                   f"{r.get('latency', 0.0):.3f},{r.get('total_queries', 0)}\n")

    print(f"Summary saved to: {csv_file}")
    print()


if __name__ == "__main__":
    main()
