#!/usr/bin/env python3

import argparse
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description="Generate complex Gaussian noise IQ samples in sc16 format."
    )

    parser.add_argument(
        "--output",
        default="noise.sc16",
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
        default=0.1,
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
    print(f"  duration    : {args.duration:.3f} s")
    print(f"  samples     : {n_samples}")
    print(f"  output      : {args.output}")

    rng = np.random.default_rng(args.seed)

    # Complex Gaussian noise
    noise = (
        rng.standard_normal(n_samples)
        + 1j * rng.standard_normal(n_samples)
    ) / np.sqrt(2)

    # Normalize to avoid clipping
    peak = np.max(np.abs(noise))
    noise = noise / peak

    # Convert to signed 16-bit IQ
    scale = 32767

    i = np.real(noise * scale).astype(np.int16)
    q = np.imag(noise * scale).astype(np.int16)

    # Interleaved I/Q:
    # I0, Q0, I1, Q1, ...
    iq = np.empty(2 * n_samples, dtype=np.int16)
    iq[0::2] = i
    iq[1::2] = q

    iq.tofile(args.output)

    print("Done.")


if __name__ == "__main__":
    main()