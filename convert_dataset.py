#!/usr/bin/env python3
"""
Convert OpenAI-500K dataset from internal bin format to cuvs fbin/ibin format.

Internal format: [dim:int32, count:int32, data...]
CUVS format:     [count:uint32, dim:uint32, data...]
"""

import struct
import sys
from pathlib import Path


def convert_bin_to_fbin(input_file: Path, output_file: Path, data_type='f'):
    """
    Convert internal bin format to cuvs fbin/ibin format.

    Args:
        input_file: Input bin file path
        output_file: Output fbin/ibin file path
        data_type: 'f' for float32, 'q' for int64
    """
    print(f"Converting {input_file} -> {output_file}")

    with open(input_file, 'rb') as f:
        # Read internal format: [dim, count]
        first_meta = struct.unpack('i', f.read(4))[0]
        second_meta = struct.unpack('i', f.read(4))[0]

        print(f"  Input format: dim={first_meta}, count={second_meta}")

        # For vectors: first_meta=dim, second_meta=num_vectors
        # For ground truth: first_meta=k, second_meta=num_queries
        dim = first_meta
        count = second_meta

        # Read data
        element_size = 4 if data_type == 'f' else 8
        data_size = dim * count * element_size
        data = f.read(data_size)

        if len(data) != data_size:
            raise ValueError(f"Data size mismatch: expected {data_size}, got {len(data)}")

    # Write cuvs format: [count, dim]
    with open(output_file, 'wb') as f:
        f.write(struct.pack('I', count))  # uint32
        f.write(struct.pack('I', dim))    # uint32
        f.write(data)

    print(f"  Output format: nrows={count}, dim={dim}")
    print(f"  ✓ Conversion successful")


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_dataset.py <input_dir> <output_dir>")
        print()
        print("Example:")
        print("  python convert_dataset.py /datasets/openai_500k ./data")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("OpenAI-500K Dataset Conversion")
    print("=" * 80)
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # File mappings
    conversions = [
        ("openai_500k_train_vectors.bin", "openai500k_base.fbin", 'f'),
        ("openai_500k_test_queries.bin", "openai500k_query.fbin", 'f'),
        ("openai_500k_ground_truth.bin", "openai500k_groundtruth.ibin", 'q'),
    ]

    for input_name, output_name, dtype in conversions:
        input_file = input_dir / input_name
        output_file = output_dir / output_name

        if not input_file.exists():
            print(f"Warning: {input_name} not found, skipping...")
            continue

        try:
            convert_bin_to_fbin(input_file, output_file, dtype)
            print()
        except Exception as e:
            print(f"Error converting {input_name}: {e}")
            sys.exit(1)

    print("=" * 80)
    print("Conversion completed successfully!")
    print("=" * 80)
    print()
    print("Generated files:")
    for _, output_name, _ in conversions:
        output_file = output_dir / output_name
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"  {output_name:40s} {size_mb:10.2f} MB")
    print()


if __name__ == "__main__":
    main()
