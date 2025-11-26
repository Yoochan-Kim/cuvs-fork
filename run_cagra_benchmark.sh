#!/bin/bash

# CAGRA Benchmark Runner for OpenAI-500K dataset
# Usage: ./run_cagra_benchmark.sh [data_dir] [output_dir]

set -e

# Configuration
DATA_DIR="${1:-./data}"
OUTPUT_DIR="${2:-./benchmark_results}"
CONFIG_FILE="cagra_openai500k_bench.json"
BENCHMARK_BIN="./cpp/build/bench/ann/CUVS_BENCH"

# Benchmark parameters
BENCHMARK_TIME=30  # 30 seconds per benchmark
CONCURRENCY_LEVELS=(1 5 10 20 30 40 60 80 100)

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo "=========================================="
echo "CAGRA Benchmark for OpenAI-500K"
echo "=========================================="
echo "Data directory: ${DATA_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo "Config file: ${CONFIG_FILE}"
echo "Benchmark binary: ${BENCHMARK_BIN}"
echo ""

# Check if benchmark binary exists
if [ ! -f "${BENCHMARK_BIN}" ]; then
    echo "Error: Benchmark binary not found at ${BENCHMARK_BIN}"
    echo "Please build the benchmark first:"
    echo "  cd cpp/build"
    echo "  cmake .. -DCMAKE_BUILD_TYPE=Release"
    echo "  make -j"
    exit 1
fi

# Check if config file exists
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "Error: Config file not found: ${CONFIG_FILE}"
    exit 1
fi

# Step 1: Build index
echo "=========================================="
echo "Step 1: Building CAGRA index"
echo "=========================================="
INDEX_BUILD_LOG="${OUTPUT_DIR}/index_build.log"
${BENCHMARK_BIN} \
    --build \
    --force \
    --data_prefix="${DATA_DIR}/" \
    --index_prefix="${OUTPUT_DIR}/" \
    --benchmark_counters_tabular=true \
    "${CONFIG_FILE}" 2>&1 | tee "${INDEX_BUILD_LOG}"

echo ""
echo "Index build completed. Log saved to: ${INDEX_BUILD_LOG}"
echo ""

# Step 2: Run search benchmarks for each concurrency level
echo "=========================================="
echo "Step 2: Running search benchmarks"
echo "=========================================="

for CONCURRENCY in "${CONCURRENCY_LEVELS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Running benchmark with concurrency=${CONCURRENCY}"
    echo "=========================================="

    OUTPUT_FILE="${OUTPUT_DIR}/search_concurrency_${CONCURRENCY}.json"
    LOG_FILE="${OUTPUT_DIR}/search_concurrency_${CONCURRENCY}.log"

    ${BENCHMARK_BIN} \
        --search \
        --mode=throughput \
        --threads=${CONCURRENCY} \
        --data_prefix="${DATA_DIR}/" \
        --index_prefix="${OUTPUT_DIR}/" \
        --benchmark_min_time=${BENCHMARK_TIME} \
        --benchmark_counters_tabular=true \
        --benchmark_out="${OUTPUT_FILE}" \
        --benchmark_out_format=json \
        "${CONFIG_FILE}" 2>&1 | tee "${LOG_FILE}"

    echo "Concurrency ${CONCURRENCY} completed."
    echo "  Results: ${OUTPUT_FILE}"
    echo "  Log: ${LOG_FILE}"
done

echo ""
echo "=========================================="
echo "All benchmarks completed!"
echo "=========================================="
echo "Results saved to: ${OUTPUT_DIR}"
echo ""
echo "Summary files:"
ls -lh "${OUTPUT_DIR}"/search_concurrency_*.json
echo ""
echo "To analyze results, run:"
echo "  python analyze_cagra_results.py ${OUTPUT_DIR}"
