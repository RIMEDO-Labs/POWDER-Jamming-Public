#!/usr/bin/env python3

import argparse
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description="Generate complex Gaussian noise IQ samples."
    )

    parser.add_argument(
        "--output",
        default="noise.fc32",
        help="Output IQ file"
    )

    parser.add_argument(
        "--sample-rate",
        type=float,
        default=92.16e6,
        help="Sample rate in samples/s"
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Duration of generated signal [s]"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed"
    )

    args = parser.parse_args()

    n_samples = int(args.sample_rate * args.duration)

    print("Generating noise:")
    print(f"  sample rate : {args.sample_rate / 1e6:.2f} MS/s")
    print(f"  duration    : {args.duration:.2f} s")
    print(f"  samples     : {n_samples}")
    print(f"  output      : {args.output}")

    rng = np.random.default_rng(args.seed)

    noise = (
        rng.standard_normal(n_samples)
        + 1j * rng.standard_normal(n_samples)
    ) / np.sqrt(2)

    noise = noise.astype(np.complex64)

    noise.tofile(args.output)

    print("Done.")


if __name__ == "__main__":
    main()